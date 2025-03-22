# src/visualization/charts.py
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import List, Dict, Optional
import os

from src.data.models import Team
from src.data.processors import TeamDataProcessor

class TeamVisualizer:
    """Visualize team data."""
    
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
        
    def visualize_standings(self, teams: List[Team], filename: str = 'standings.png') -> str:
        """
        Create a visualization of team standings.
        
        Args:
            teams: List of Team objects
            filename: Output filename
            
        Returns:
            str: Path to generated image
        """
        df = TeamDataProcessor.teams_to_dataframe(teams)
        df = df.sort_values('standing')
        
        plt.figure(figsize=(12, 8))
        # Update to follow the new seaborn API
        ax = sns.barplot(x='name', y='wins', hue='name', data=df, palette='viridis', legend=False)
        ax.set_title('Team Standings by Wins', fontsize=16)
        ax.set_xlabel('Team', fontsize=12)
        ax.set_ylabel('Wins', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Save the figure
        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path)
        plt.close()
        
        return output_path
    
    # Update the visualize_win_percentage method
    def visualize_win_percentage(self, teams: List[Team], filename: str = 'win_percentage.png') -> str:
        """
        Create a visualization of team win percentages.
        
        Args:
            teams: List of Team objects
            filename: Output filename
            
        Returns:
            str: Path to generated image
        """
        df = TeamDataProcessor.teams_to_dataframe(teams)
        df['win_percentage'] = df['wins'] / (df['wins'] + df['losses']) * 100
        df = df.sort_values('win_percentage', ascending=False)
        
        plt.figure(figsize=(12, 8))
        # Update to follow the new seaborn API
        ax = sns.barplot(x='name', y='win_percentage', hue='name', data=df, palette='coolwarm', legend=False)
        ax.set_title('Team Win Percentages', fontsize=16)
        ax.set_xlabel('Team', fontsize=12)
        ax.set_ylabel('Win Percentage (%)', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Save the figure
        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path)
        plt.close()
        
        return output_path
    
    # Update the visualize_division_comparison method
    def visualize_division_comparison(
        self, teams: List[Team], filename: str = 'division_comparison.png'
    ) -> Optional[str]:
        """
        Create a visualization comparing divisions.
        
        Args:
            teams: List of Team objects
            filename: Output filename
            
        Returns:
            str: Path to generated image or None if no division data
        """
        df = TeamDataProcessor.teams_to_dataframe(teams)
        
        if 'division_name' not in df.columns or df['division_name'].isna().all():
            return None
        
        # Group by division
        division_stats = df.groupby('division_name').agg({
            'wins': 'mean',
            'losses': 'mean',
            'win_percentage': 'mean'
        }).reset_index()
        
        plt.figure(figsize=(10, 6))
        # Update to follow the new seaborn API
        ax = sns.barplot(x='division_name', y='win_percentage', hue='division_name', 
                        data=division_stats, palette='deep', legend=False)
        ax.set_title('Average Win Percentage by Division', fontsize=16)
        ax.set_xlabel('Division', fontsize=12)
        ax.set_ylabel('Average Win Percentage (%)', fontsize=12)
        plt.tight_layout()
        
        # Save the figure
        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path)
        plt.close()
        
        return output_path