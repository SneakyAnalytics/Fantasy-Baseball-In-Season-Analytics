# src/visualization/player_charts.py
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import os

from src.data.models import Player
from src.data.processors import PlayerDataProcessor

class PlayerVisualizer:
    """Visualize player data."""
    
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
    
    def visualize_top_players(
        self, players: List[Player], stat: str, limit: int = 10, 
        filename: Optional[str] = None, ascending: bool = False
    ) -> str:
        """
        Create a visualization of top players by a specific statistic.
        
        Args:
            players: List of Player objects
            stat: Statistic to visualize
            limit: Number of players to include
            filename: Output filename
            ascending: Sort in ascending order if True
            
        Returns:
            str: Path to generated image
        """
        df = PlayerDataProcessor.players_to_dataframe(players)
        
        # Check if stat exists
        if stat not in df.columns:
            available_stats = [col for col in df.columns 
                              if col not in ['player_id', 'name', 'team', 'positions']]
            raise ValueError(f"Stat '{stat}' not found. Available stats: {available_stats}")
        
        # Filter out rows with NaN values for this stat
        df = df[df[stat].notna()]
        
        # Sort and limit
        df = df.sort_values(stat, ascending=ascending).head(limit)
        
        # Create visualization
        plt.figure(figsize=(12, 8))
        ax = sns.barplot(x='name', y=stat, hue='name', data=df, palette='viridis', legend=False)
        ax.set_title(f"Top {limit} Players by {stat}", fontsize=16)
        ax.set_xlabel('Player', fontsize=12)
        ax.set_ylabel(stat, fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Generate filename if not provided
        if filename is None:
            order = "bottom" if ascending else "top"
            filename = f"{order}_{limit}_players_by_{stat}.png"
        
        # Save the figure
        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path)
        plt.close()
        
        return output_path
    
    def visualize_position_comparison(
        self, players: List[Player], stat: str, filename: Optional[str] = None
    ) -> str:
        """
        Create a visualization comparing positions by a specific statistic.
        
        Args:
            players: List of Player objects
            stat: Statistic to visualize
            filename: Output filename
            
        Returns:
            str: Path to generated image
        """
        df = PlayerDataProcessor.players_to_dataframe(players)
        
        # Check if stat exists
        if stat not in df.columns:
            available_stats = [col for col in df.columns 
                              if col not in ['player_id', 'name', 'team', 'positions']]
            raise ValueError(f"Stat '{stat}' not found. Available stats: {available_stats}")
        
        # Extract primary position (first position listed)
        df['primary_position'] = df['positions'].str.split(',').str[0].str.strip()
        
        # Group by position and calculate mean
        position_stats = df.groupby('primary_position')[stat].mean().reset_index()
        position_stats = position_stats.sort_values(stat, ascending=False)
        
        # Create visualization
        plt.figure(figsize=(12, 8))
        ax = sns.barplot(x='primary_position', y=stat, hue='primary_position', 
                         data=position_stats, palette='deep', legend=False)
        ax.set_title(f"Average {stat} by Position", fontsize=16)
        ax.set_xlabel('Position', fontsize=12)
        ax.set_ylabel(f"Average {stat}", fontsize=12)
        plt.tight_layout()
        
        # Generate filename if not provided
        if filename is None:
            filename = f"position_comparison_{stat}.png"
        
        # Save the figure
        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path)
        plt.close()
        
        return output_path
    
    def visualize_player_comparison(
        self, player1: Player, player2: Player, stats: List[str], 
        filename: Optional[str] = None
    ) -> str:
        """
        Create a visualization comparing two players across multiple statistics.
        
        Args:
            player1: First Player object
            player2: Second Player object
            stats: List of statistics to compare
            filename: Output filename
            
        Returns:
            str: Path to generated image
        """
        # Convert players to DataFrames
        df1 = PlayerDataProcessor.players_to_dataframe([player1])
        df2 = PlayerDataProcessor.players_to_dataframe([player2])
        
        # Check which stats are available for both players
        available_stats = []
        for stat in stats:
            if stat in df1.columns and stat in df2.columns:
                available_stats.append(stat)
        
        if not available_stats:
            raise ValueError("No common statistics found for comparison")
        
        # Create data for visualization
        comparison_data = []
        for stat in available_stats:
            comparison_data.append({
                'stat': stat,
                'value': df1[stat].iloc[0],
                'player': df1['name'].iloc[0]
            })
            comparison_data.append({
                'stat': stat,
                'value': df2[stat].iloc[0],
                'player': df2['name'].iloc[0]
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        
        # Create visualization
        plt.figure(figsize=(14, 10))
        ax = sns.barplot(x='stat', y='value', hue='player', data=comparison_df, palette='Set1')
        ax.set_title(f"Player Comparison: {df1['name'].iloc[0]} vs {df2['name'].iloc[0]}", fontsize=16)
        ax.set_xlabel('Statistic', fontsize=12)
        ax.set_ylabel('Value', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.legend(title='Player')
        plt.tight_layout()
        
        # Generate filename if not provided
        if filename is None:
            player1_name = df1['name'].iloc[0].replace(' ', '_')
            player2_name = df2['name'].iloc[0].replace(' ', '_')
            filename = f"comparison_{player1_name}_vs_{player2_name}.png"
        
        # Save the figure
        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path)
        plt.close()
        
        return output_path