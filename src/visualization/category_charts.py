# src/visualization/category_charts.py
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import os

from src.data.models import Team, Player
from src.analysis.category_analysis import CategoryAnalyzer

class CategoryVisualizer:
    """Visualize category analysis data."""
    
    def __init__(self, output_dir: str = 'output'):
        """
        Initialize the visualizer.
        
        Args:
            output_dir: Directory to save visualizations
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Set up styling
        sns.set_style('whitegrid')
        plt.rcParams['figure.figsize'] = (12, 8)
        
    def visualize_category_strengths(
        self, analysis: Dict[str, Any], category_type: str = "both", 
        filename: Optional[str] = None
    ) -> str:
        """
        Visualize team's strengths and weaknesses across categories.
        
        Args:
            analysis: Result from CategoryAnalyzer.analyze_team_categories()
            category_type: Type of categories to visualize ("batting", "pitching", or "both")
            filename: Output filename
            
        Returns:
            str: Path to generated image
        """
        if "error" in analysis:
            raise ValueError(f"Invalid analysis data: {analysis['error']}")
        
        # Generate radar charts for categorical analysis
        if category_type == "both":
            # Create a figure with two subplots
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8), subplot_kw=dict(polar=True))
            self._create_radar_chart(analysis, "batting", ax1)
            self._create_radar_chart(analysis, "pitching", ax2)
            
            fig.suptitle(f"Category Analysis for {analysis['team_name']}", fontsize=18)
        else:
            # Create a single radar chart
            fig, ax = plt.subplots(figsize=(12, 10), subplot_kw=dict(polar=True))
            self._create_radar_chart(analysis, category_type, ax)
            
            fig.suptitle(f"{category_type.capitalize()} Category Analysis for {analysis['team_name']}", fontsize=18)
        
        plt.tight_layout()
        
        # Generate filename if not provided
        if filename is None:
            filename = f"category_analysis_{analysis['team_id']}.png"
        
        # Save the figure
        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path)
        plt.close()
        
        return output_path
    
    def _create_radar_chart(self, analysis: Dict[str, Any], category_type: str, ax: plt.Axes) -> None:
        """
        Create a radar chart on the given axes.
        
        Args:
            analysis: Result from CategoryAnalyzer.analyze_team_categories()
            category_type: Type of categories to visualize ("batting" or "pitching")
            ax: Matplotlib axes to draw on
        """
        categories = analysis["categories"][category_type]
        if not categories:
            ax.text(0.5, 0.5, f"No {category_type} categories available", 
                    ha='center', va='center', transform=ax.transAxes)
            return
        
        # Get category names and percentiles
        cat_names = list(categories.keys())
        percentiles = [categories[cat]["percentile"] for cat in cat_names]
        
        # Calculate number of variables and angles
        N = len(cat_names)
        angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
        
        # Close the polygon
        percentiles += [percentiles[0]]
        angles += [angles[0]]
        cat_names += [cat_names[0]]
        
        # Plot data
        ax.fill(angles, percentiles, 'skyblue', alpha=0.25)
        ax.plot(angles, percentiles, 'blue', linewidth=2)
        
        # Add category labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(cat_names[:-1], size=12)
        
        # Configure radar chart appearance
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80])
        ax.set_yticklabels(['20%', '40%', '60%', '80%'])
        ax.set_title(f"{category_type.capitalize()} Categories", fontsize=16)
        
        # Add strength reference circles
        circle_colors = [(0.9, 0.2, 0.2, 0.1), (0.9, 0.6, 0.2, 0.1), 
                        (0.8, 0.8, 0.2, 0.1), (0.2, 0.7, 0.2, 0.1)]
        circles = [20, 40, 60, 80]
        for r, color in zip(circles, circle_colors):
            ax.fill(np.linspace(0, 2*np.pi, 100), [r]*100, color=color)
        
        # Add legend for strength levels
        strength_levels = ['Very Weak', 'Weak', 'Average', 'Strong', 'Very Strong']
        percentile_ranges = ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%']
        legend_elements = []
        
        for i, (level, perc) in enumerate(zip(strength_levels, percentile_ranges)):
            color = (0.9 - i*0.2, 0.2 + i*0.15, 0.2, 0.5)
            legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                   label=f'{level} ({perc})', 
                                   markerfacecolor=color, markersize=10))
        
        ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.1, 0.1))
    
    def visualize_category_rankings(
        self, analyzer: CategoryAnalyzer, stat_category: str, category_type: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Visualize league rankings for a specific category.
        
        Args:
            analyzer: CategoryAnalyzer with teams data
            stat_category: Specific category to visualize (e.g., "HR", "ERA")
            category_type: "batting" or "pitching"
            filename: Output filename
            
        Returns:
            str: Path to generated image
        """
        if not analyzer.teams:
            raise ValueError("CategoryAnalyzer has no teams")
        
        # Get category data for all teams
        teams_data = []
        for team in analyzer.teams:
            analysis = analyzer.analyze_team_categories(team.team_id)
            if "error" not in analysis and stat_category in analysis["categories"][category_type]:
                teams_data.append({
                    "team_name": team.name,
                    "value": analysis["categories"][category_type][stat_category]["value"],
                    "percentile": analysis["categories"][category_type][stat_category]["percentile"]
                })
        
        if not teams_data:
            raise ValueError(f"No data available for {stat_category} in {category_type}")
        
        # Create DataFrame and sort by value
        df = pd.DataFrame(teams_data)
        
        # For ERA, WHIP and other "lower is better" stats, we need to sort differently
        ascending = stat_category in ['ERA', 'WHIP', 'BB/9']
        df = df.sort_values("value", ascending=ascending)
        
        # Create visualization
        plt.figure(figsize=(12, 8))
        bars = sns.barplot(x="team_name", y="value", data=df, palette="viridis")
        
        # Add percentiles as text on bars
        for i, p in enumerate(bars.patches):
            percentile = df.iloc[i]["percentile"]
            bars.text(p.get_x() + p.get_width()/2., p.get_height() + 0.1,
                     f'{percentile:.1f}%', ha="center", fontsize=10)
        
        plt.title(f"Team Rankings by {stat_category}", fontsize=16)
        plt.xlabel("Team", fontsize=12)
        plt.ylabel(stat_category, fontsize=12)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        
        # Generate filename if not provided
        if filename is None:
            filename = f"category_ranking_{stat_category}.png"
        
        # Save the figure
        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path)
        plt.close()
        
        return output_path
    
    def visualize_improvement_recommendations(
        self, recommendations: Dict[str, Any], category_type: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Visualize improvement recommendations for weak categories.
        
        Args:
            recommendations: Result from CategoryAnalyzer.recommend_category_improvements()
            category_type: "batting" or "pitching" 
            filename: Output filename
            
        Returns:
            str: Path to generated image
        """
        if "error" in recommendations:
            raise ValueError(f"Invalid recommendations data: {recommendations['error']}")
        
        weaknesses = recommendations["weaknesses"][category_type]
        if not weaknesses:
            raise ValueError(f"No {category_type} weaknesses found")
        
        # Get player recommendations for each weak category
        player_recs = recommendations["free_agent_recommendations"].get(category_type, {})
        
        # Create visualization
        fig, axs = plt.subplots(len(weaknesses), 1, figsize=(12, 5*len(weaknesses)))
        if len(weaknesses) == 1:
            axs = [axs]  # Make axs a list even if there's only one category
        
        for i, category in enumerate(weaknesses):
            if category in player_recs and player_recs[category]:
                # Create a DataFrame for this category's recommendations
                players = player_recs[category]
                df = pd.DataFrame(players)
                
                # Plot the recommendations
                sns.barplot(x="name", y="value", data=df, ax=axs[i], palette="viridis")
                axs[i].set_title(f"Recommended Players for {category}", fontsize=14)
                axs[i].set_xlabel("Player", fontsize=12)
                axs[i].set_ylabel(category, fontsize=12)
                axs[i].tick_params(axis='x', rotation=45)
                
                # Add position labels
                for j, player in enumerate(players):
                    axs[i].text(j, 0.1, player["positions"], rotation=90, 
                               ha='center', va='bottom', fontsize=9)
            else:
                axs[i].text(0.5, 0.5, f"No recommendations available for {category}", 
                           ha='center', va='center', transform=axs[i].transAxes)
                axs[i].set_title(f"Category: {category}", fontsize=14)
        
        plt.suptitle(f"{category_type.capitalize()} Improvement Recommendations for {recommendations['team_name']}", 
                     fontsize=16)
        plt.tight_layout()
        
        # Generate filename if not provided
        if filename is None:
            filename = f"improvement_recommendations_{category_type}_{recommendations['team_id']}.png"
        
        # Save the figure
        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path)
        plt.close()
        
        return output_path