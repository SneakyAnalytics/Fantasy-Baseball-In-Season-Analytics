# src/visualization/trend_charts.py
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import os
import matplotlib.dates as mdates
from datetime import datetime, timedelta

class TrendVisualizer:
    """Visualize player and team performance trends over time."""
    
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
    
    def visualize_player_trend(
        self, player_name: str, stat: str, stat_values: List[float], 
        dates: List[str], rolling_window: int = 7,
        filename: Optional[str] = None, include_expected: bool = False,
        expected_values: Optional[List[float]] = None
    ) -> str:
        """
        Visualize a player's performance trend over time.
        
        Args:
            player_name: Name of the player
            stat: Name of the statistic being visualized
            stat_values: List of stat values in chronological order
            dates: List of date strings corresponding to stat values
            rolling_window: Window size for rolling average
            filename: Output filename
            include_expected: Whether to include expected stats (xStats)
            expected_values: List of expected stat values (required if include_expected is True)
            
        Returns:
            str: Path to generated image
        """
        if include_expected and not expected_values:
            raise ValueError("expected_values must be provided if include_expected is True")
        
        if len(stat_values) != len(dates):
            raise ValueError("stat_values and dates must have same length")
            
        # Convert dates to datetime objects
        date_objects = [datetime.strptime(date, "%Y-%m-%d") for date in dates]
        
        # Create DataFrame
        df = pd.DataFrame({
            'date': date_objects,
            'value': stat_values
        })
        
        # Add expected values if requested
        if include_expected:
            if len(expected_values) != len(dates):
                raise ValueError("expected_values and dates must have same length")
            df['expected'] = expected_values
        
        # Calculate rolling average if enough data points
        if len(stat_values) >= rolling_window:
            df['rolling_avg'] = df['value'].rolling(window=rolling_window).mean()
            if include_expected:
                df['expected_rolling_avg'] = df['expected'].rolling(window=rolling_window).mean()
        
        # Create visualization
        plt.figure(figsize=(14, 8))
        
        # Plot actual values
        plt.plot(df['date'], df['value'], 'o-', color='blue', alpha=0.6, label=f'Actual {stat}')
        
        # Plot rolling average if available
        if 'rolling_avg' in df.columns:
            plt.plot(df['date'], df['rolling_avg'], '-', color='darkblue', linewidth=2, 
                   label=f'{rolling_window}-Day Rolling Avg')
        
        # Plot expected values if requested
        if include_expected:
            plt.plot(df['date'], df['expected'], 'o--', color='red', alpha=0.6, label=f'Expected {stat} (x{stat})')
            if 'expected_rolling_avg' in df.columns:
                plt.plot(df['date'], df['expected_rolling_avg'], '--', color='darkred', linewidth=2,
                       label=f'Expected {rolling_window}-Day Rolling Avg')
        
        # Set chart properties
        plt.title(f"{player_name}: {stat} Trend", fontsize=16)
        plt.xlabel("Date", fontsize=12)
        plt.ylabel(stat, fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        
        # Format date axis
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.gcf().autofmt_xdate()
        
        # Add trendline for overall direction
        z = np.polyfit(range(len(df['value'])), df['value'], 1)
        p = np.poly1d(z)
        plt.plot(df['date'], p(range(len(df['value']))), "r--", alpha=0.3, linewidth=1)
        
        # Highlight significant changes
        if len(stat_values) >= 3:
            last_value = stat_values[-1]
            avg_value = np.mean(stat_values[:-1])
            
            # Calculate percent change
            if avg_value != 0:
                percent_change = (last_value - avg_value) / avg_value * 100
                direction = "up" if percent_change > 0 else "down"
                
                # Add annotation if change is significant (>10%)
                if abs(percent_change) > 10:
                    plt.annotate(f"{direction.upper()} {abs(percent_change):.1f}%", 
                                xy=(df['date'].iloc[-1], last_value),
                                xytext=(10, 10 if direction == "up" else -10),
                                textcoords="offset points",
                                arrowprops=dict(arrowstyle="->", color="green" if direction == "up" else "red"))
        
        plt.tight_layout()
        
        # Generate filename if not provided
        if filename is None:
            player_name_slug = player_name.replace(' ', '_').lower()
            expected_suffix = "_with_expected" if include_expected else ""
            filename = f"trend_{player_name_slug}_{stat.lower()}{expected_suffix}.png"
        
        # Save the figure
        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path)
        plt.close()
        
        return output_path
    
    def visualize_player_rolling_stats(
        self, player_name: str, stats: Dict[str, List[float]], 
        dates: List[str], windows: List[int] = [7, 15, 30],
        filename: Optional[str] = None
    ) -> str:
        """
        Visualize a player's rolling statistics over multiple time windows.
        
        Args:
            player_name: Name of the player
            stats: Dictionary of stat names to lists of values
            dates: List of date strings corresponding to stat values
            windows: Rolling windows to calculate (in days)
            filename: Output filename
            
        Returns:
            str: Path to generated image
        """
        # Verify all stat series are the same length as dates
        for stat_name, values in stats.items():
            if len(values) != len(dates):
                raise ValueError(f"values for {stat_name} and dates must have same length")
        
        # Convert dates to datetime objects
        date_objects = [datetime.strptime(date, "%Y-%m-%d") for date in dates]
        
        # Create DataFrame
        df = pd.DataFrame({'date': date_objects})
        for stat_name, values in stats.items():
            df[stat_name] = values
        
        # Calculate rolling averages for each window and stat
        rolling_data = {}
        for window in windows:
            if len(dates) >= window:
                for stat_name in stats.keys():
                    df[f'{stat_name}_{window}d'] = df[stat_name].rolling(window=window).mean()
                    if f'{stat_name}' not in rolling_data:
                        rolling_data[f'{stat_name}'] = []
                    rolling_data[f'{stat_name}'].append((window, f'{stat_name}_{window}d'))
        
        # Create subplots for each stat
        num_stats = len(stats)
        fig, axs = plt.subplots(num_stats, 1, figsize=(14, 5*num_stats), sharex=True)
        if num_stats == 1:
            axs = [axs]  # Make axs a list even if there's only one stat
        
        # Plot each stat
        for i, (stat_name, values) in enumerate(stats.items()):
            # Plot raw values with low opacity
            axs[i].plot(df['date'], df[stat_name], 'o-', color='gray', alpha=0.3, label=f'Daily {stat_name}')
            
            # Plot rolling averages if available
            if stat_name in rolling_data:
                for window, col_name in rolling_data[stat_name]:
                    axs[i].plot(df['date'], df[col_name], '-', linewidth=2, label=f'{window}-Day Avg')
            
            # Set subplot properties
            axs[i].set_title(f"{stat_name}", fontsize=14)
            axs[i].set_ylabel(stat_name, fontsize=12)
            axs[i].grid(True, linestyle='--', alpha=0.7)
            axs[i].legend(loc='upper left')
            
            # Format date axis
            axs[i].xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            axs[i].xaxis.set_major_locator(mdates.AutoDateLocator())
        
        plt.suptitle(f"{player_name}: Rolling Performance", fontsize=16)
        plt.xlabel("Date", fontsize=12)
        fig.autofmt_xdate()
        plt.tight_layout()
        
        # Generate filename if not provided
        if filename is None:
            player_name_slug = player_name.replace(' ', '_').lower()
            stats_slug = '_'.join(list(stats.keys())[:2]).lower()  # Use first two stats in filename
            filename = f"rolling_stats_{player_name_slug}_{stats_slug}.png"
        
        # Save the figure
        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path)
        plt.close()
        
        return output_path
    
    def visualize_stat_distribution(
        self, player_name: str, stat: str, player_value: float,
        comparison_values: List[float], timeframe: str = "Season",
        filename: Optional[str] = None
    ) -> str:
        """
        Visualize how a player's stat compares to the league distribution.
        
        Args:
            player_name: Name of the player
            stat: Name of the statistic being visualized
            player_value: Player's value for the stat
            comparison_values: List of values from other players/league for comparison
            timeframe: Timeframe of the data (e.g., "Season", "Last 30 Days")
            filename: Output filename
            
        Returns:
            str: Path to generated image
        """
        plt.figure(figsize=(12, 6))
        
        # Create histogram/KDE of league distribution
        sns.histplot(comparison_values, kde=True, color='skyblue', alpha=0.5)
        
        # Add vertical line for player's value
        plt.axvline(x=player_value, color='red', linestyle='--', linewidth=2, 
                   label=f'{player_name}: {player_value}')
        
        # Calculate percentile
        percentile = sum(v < player_value for v in comparison_values) / len(comparison_values) * 100
        
        # Set chart properties
        plt.title(f"{player_name}: {stat} vs. League ({timeframe})", fontsize=16)
        plt.xlabel(stat, fontsize=12)
        plt.ylabel("Frequency", fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # Add percentile annotation
        plt.annotate(f"{percentile:.1f}th Percentile", 
                    xy=(player_value, 0),
                    xytext=(0, 20),
                    textcoords="offset points",
                    ha='center',
                    arrowprops=dict(arrowstyle="->", color="red"))
        
        plt.legend()
        plt.tight_layout()
        
        # Generate filename if not provided
        if filename is None:
            player_name_slug = player_name.replace(' ', '_').lower()
            timeframe_slug = timeframe.replace(' ', '_').lower()
            filename = f"distribution_{player_name_slug}_{stat.lower()}_{timeframe_slug}.png"
        
        # Save the figure
        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path)
        plt.close()
        
        return output_path
    
    def visualize_multistat_comparison(
        self, player_name: str, stats: Dict[str, Tuple[float, List[float]]],
        timeframe: str = "Season", filename: Optional[str] = None
    ) -> str:
        """
        Visualize how a player compares to the league across multiple statistics.
        
        Args:
            player_name: Name of the player
            stats: Dictionary mapping stat names to tuples of (player_value, comparison_values)
            timeframe: Timeframe of the data (e.g., "Season", "Last 30 Days")
            filename: Output filename
            
        Returns:
            str: Path to generated image
        """
        # Calculate percentiles for each stat
        percentiles = {}
        for stat_name, (player_value, comparison_values) in stats.items():
            percentile = sum(v < player_value for v in comparison_values) / len(comparison_values) * 100
            percentiles[stat_name] = percentile
        
        # Create DataFrame for visualization
        df = pd.DataFrame({
            'Stat': list(percentiles.keys()),
            'Percentile': list(percentiles.values())
        })
        
        # Create visualization
        plt.figure(figsize=(12, 8))
        bars = sns.barplot(x='Stat', y='Percentile', data=df, palette='viridis')
        
        # Add percentile values on top of bars
        for i, p in enumerate(bars.patches):
            bars.text(p.get_x() + p.get_width()/2., p.get_height() + 1,
                     f'{df["Percentile"].iloc[i]:.1f}%', ha="center")
        
        # Add a horizontal line at 50th percentile
        plt.axhline(y=50, color='r', linestyle='--', alpha=0.7, label='League Average (50th Percentile)')
        
        # Set chart properties
        plt.title(f"{player_name}: Percentile Rankings ({timeframe})", fontsize=16)
        plt.xlabel("Statistic", fontsize=12)
        plt.ylabel("Percentile Rank", fontsize=12)
        plt.ylim(0, 100)
        plt.grid(True, axis='y', linestyle='--', alpha=0.7)
        plt.legend()
        plt.tight_layout()
        
        # Generate filename if not provided
        if filename is None:
            player_name_slug = player_name.replace(' ', '_').lower()
            timeframe_slug = timeframe.replace(' ', '_').lower()
            filename = f"percentile_rankings_{player_name_slug}_{timeframe_slug}.png"
        
        # Save the figure
        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path)
        plt.close()
        
        return output_path