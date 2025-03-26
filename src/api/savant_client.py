"""
Baseball Savant data client for retrieving advanced Statcast metrics.

This module provides a client for accessing Baseball Savant data (MLB's Statcast platform)
to retrieve advanced metrics like exit velocity, barrel percentage, expected statistics,
and more that are critical for identifying player trends and breakout candidates.
"""

import requests
import pandas as pd
import numpy as np
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import io
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class BaseballSavantClient:
    """Client for retrieving data from Baseball Savant (Statcast)."""
    
    SAVANT_BASE_URL = "https://baseballsavant.mlb.com"
    
    def __init__(self, cache_duration: int = 3600):
        """
        Initialize the Baseball Savant client.
        
        Args:
            cache_duration: Cache duration in seconds (default: 1 hour)
        """
        self.cache = {}
        self.cache_duration = cache_duration
        
    def _get_cached_or_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Get data from cache or make a new request if needed.
        
        Args:
            url: URL to request
            params: Request parameters
            
        Returns:
            Response content
        """
        # Check cache first
        cache_key = f"{url}:{str(params)}"
        if cache_key in self.cache:
            cache_time, cache_data = self.cache[cache_key]
            if time.time() - cache_time < self.cache_duration:
                logger.debug(f"Using cached data for {url}")
                return cache_data
        
        # Make the request
        try:
            headers = {
                "User-Agent": "Fantasy Baseball Analyzer/1.0",
                "Accept": "text/html,application/xhtml+xml,application/xml",
                "Accept-Language": "en-US,en;q=0.9",
            }
            
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            # Cache the response
            self.cache[cache_key] = (time.time(), response.content)
            
            return response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to Baseball Savant: {e}")
            return None
    
    def get_statcast_leaderboard(self, 
                               player_type: str = "batter", 
                               year: Optional[int] = None,
                               min_pa: int = 25,
                               min_pitches: int = 100,
                               stats_type: str = "expected") -> pd.DataFrame:
        """
        Get Statcast leaderboard data.
        
        Args:
            player_type: 'batter' or 'pitcher'
            year: Season year (default: current year)
            min_pa: Minimum plate appearances (for batters)
            min_pitches: Minimum pitches thrown (for pitchers)
            stats_type: Type of stats ('expected', 'barrels', 'speed', etc.)
            
        Returns:
            DataFrame: Statcast leaderboard data
        """
        if year is None:
            year = datetime.now().year
            
        # Construct URL based on stats type
        if stats_type == "expected":
            url = f"{self.SAVANT_BASE_URL}/leaderboard/expected_statistics"
            params = {
                "type": player_type,
                "year": year,
                "position": "all",
                "stats": "batting" if player_type == "batter" else "pitching",
                "min_pa": min_pa if player_type == "batter" else None,
                "min_pitches": min_pitches if player_type == "pitcher" else None,
                "sort": "xwoba" if player_type == "batter" else "xera"
            }
        elif stats_type == "barrels":
            url = f"{self.SAVANT_BASE_URL}/leaderboard/barrel"
            params = {
                "type": player_type,
                "year": year,
                "min_pa": min_pa if player_type == "batter" else None,
                "min_pitches": min_pitches if player_type == "pitcher" else None,
            }
        else:
            # Default to expected stats if type is unrecognized
            url = f"{self.SAVANT_BASE_URL}/leaderboard/expected_statistics"
            params = {
                "type": player_type,
                "year": year,
                "position": "all",
                "stats": "batting" if player_type == "batter" else "pitching"
            }
            
        # Clean up params - remove None values
        params = {k: v for k, v in params.items() if v is not None}
            
        # Request the CSV data
        params["csv"] = "true"
        content = self._get_cached_or_request(url, params)
        
        if content is None:
            logger.error(f"Failed to retrieve data from {url}")
            return pd.DataFrame()
        
        # Parse the CSV data
        try:
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
            return df
        except Exception as e:
            logger.error(f"Error parsing CSV data: {e}")
            return pd.DataFrame()
    
    def get_statcast_player_trends(self, 
                                 player_id: int, 
                                 player_type: str = "batter",
                                 days_back: int = 30) -> Dict[str, Any]:
        """
        Get Statcast metrics for a player over recent time periods to analyze trends.
        
        Args:
            player_id: MLB player ID
            player_type: 'batter' or 'pitcher'
            days_back: How many days back to analyze
            
        Returns:
            Dict: Player trend data with metrics for different time periods
        """
        # Get data for different time periods for trending analysis
        end_date = datetime.now()
        
        # Define time periods for trend analysis
        periods = {
            "last7": (end_date - timedelta(days=7), end_date),
            "last15": (end_date - timedelta(days=15), end_date),
            "last30": (end_date - timedelta(days=30), end_date),
            "season": (datetime(end_date.year, 3, 1), end_date)  # Approximate season start
        }
        
        trends = {}
        
        for period_name, (start_date, period_end_date) in periods.items():
            # Format dates for the API
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = period_end_date.strftime('%Y-%m-%d')
            
            # Build URL for the specific player and time period
            if player_type == "batter":
                url = f"{self.SAVANT_BASE_URL}/statcast_search"
                params = {
                    "hfPT": "",
                    "hfAB": "",
                    "hfGT": "",
                    "hfPR": "",
                    "hfZ": "",
                    "hfStadium": "",
                    "hfBBL": "",
                    "hfNewZones": "",
                    "hfPull": "",
                    "hfC": "",
                    "hfSea": f"{end_date.year}|",
                    "hfSit": "",
                    "player_type": "batter",
                    "hfOuts": "",
                    "hfOpponent": "",
                    "pitcher_throws": "",
                    "batter_stands": "",
                    "hfSA": "",
                    "player_id": player_id,
                    "min_pitches": "0",
                    "min_results": "0",
                    "group_by": "name",
                    "sort_col": "pitches",
                    "player_event_sort": "h_launch_speed",
                    "sort_order": "desc",
                    "min_abs": "0",
                    "type": "details",
                    "game_date_gt": start_str,
                    "game_date_lt": end_str
                }
            else:  # pitcher
                url = f"{self.SAVANT_BASE_URL}/statcast_search"
                params = {
                    "hfPT": "",
                    "hfAB": "",
                    "hfGT": "",
                    "hfPR": "",
                    "hfZ": "",
                    "hfStadium": "",
                    "hfBBL": "",
                    "hfNewZones": "",
                    "hfPull": "",
                    "hfC": "",
                    "hfSea": f"{end_date.year}|",
                    "hfSit": "",
                    "player_type": "pitcher",
                    "hfOuts": "",
                    "hfOpponent": "",
                    "pitcher_throws": "",
                    "batter_stands": "",
                    "hfSA": "",
                    "player_id": player_id,
                    "min_pitches": "0",
                    "min_results": "0",
                    "group_by": "name",
                    "sort_col": "pitches",
                    "player_event_sort": "h_launch_speed",
                    "sort_order": "desc",
                    "min_abs": "0",
                    "type": "details",
                    "game_date_gt": start_str,
                    "game_date_lt": end_str
                }
            
            # Request the CSV data
            params["csv"] = "true"
            content = self._get_cached_or_request(url, params)
            
            if content is None:
                logger.warning(f"Failed to retrieve {period_name} data for player {player_id}")
                continue
                
            # Parse the CSV data
            try:
                df = pd.read_csv(io.StringIO(content.decode('utf-8')))
                
                # Calculate period metrics
                metrics = self._calculate_player_metrics(df, player_type)
                trends[period_name] = metrics
            except Exception as e:
                logger.error(f"Error parsing {period_name} data for player {player_id}: {e}")
                trends[period_name] = {}
        
        # Calculate trend indicators by comparing periods
        trend_indicators = self._calculate_trend_indicators(trends)
        
        return {
            "player_id": player_id,
            "metrics": trends,
            "trend_indicators": trend_indicators
        }
    
    def _calculate_player_metrics(self, df: pd.DataFrame, player_type: str) -> Dict[str, Any]:
        """
        Calculate relevant metrics from raw Statcast data.
        
        Args:
            df: DataFrame with raw Statcast data
            player_type: 'batter' or 'pitcher'
            
        Returns:
            Dict: Calculated metrics
        """
        metrics = {}
        
        # Skip if DataFrame is empty
        if df.empty:
            return metrics
        
        # Common metrics for both batters and pitchers
        events = df['events'].dropna().tolist() if 'events' in df.columns else []
        metrics['sample_size'] = len(df)
        
        if player_type == "batter":
            # Batter-specific metrics
            if 'launch_speed' in df.columns:
                metrics['avg_exit_velo'] = df['launch_speed'].dropna().mean()
            
            if 'launch_angle' in df.columns:
                metrics['avg_launch_angle'] = df['launch_angle'].dropna().mean()
            
            # Calculate barrel rate if enough data
            if 'barrel' in df.columns and len(df) > 0:
                barrels = df['barrel'].fillna(0).sum()
                metrics['barrel_count'] = barrels
                metrics['barrel_rate'] = (barrels / len(df)) * 100
            
            # Batted ball distribution
            if 'bb_type' in df.columns:
                gb = df[df['bb_type'] == 'ground_ball'].shape[0]
                fb = df[df['bb_type'] == 'fly_ball'].shape[0]
                ld = df[df['bb_type'] == 'line_drive'].shape[0]
                pu = df[df['bb_type'] == 'popup'].shape[0]
                
                total_batted = gb + fb + ld + pu
                if total_batted > 0:
                    metrics['gb_pct'] = gb / total_batted * 100
                    metrics['fb_pct'] = fb / total_batted * 100
                    metrics['ld_pct'] = ld / total_batted * 100
                    metrics['pu_pct'] = pu / total_batted * 100
            
            # Plate discipline
            if 'description' in df.columns:
                swings = df[df['description'].isin(['hit_into_play', 'swinging_strike', 'foul'])].shape[0]
                takes = df[df['description'].isin(['ball', 'called_strike'])].shape[0]
                whiffs = df[df['description'] == 'swinging_strike'].shape[0]
                
                if swings + takes > 0:
                    metrics['swing_pct'] = swings / (swings + takes) * 100
                
                if swings > 0:
                    metrics['whiff_pct'] = whiffs / swings * 100
            
            # Outcome metrics
            if 'events' in df.columns:
                hits = df[df['events'].isin(['single', 'double', 'triple', 'home_run'])].shape[0]
                at_bats = len([e for e in events if e in ['single', 'double', 'triple', 'home_run', 'field_out', 'strikeout', 'double_play', 'fielders_choice_out', 'fielders_choice']])
                
                if at_bats > 0:
                    metrics['batting_avg'] = hits / at_bats
        
        elif player_type == "pitcher":
            # Pitcher-specific metrics
            if 'release_speed' in df.columns:
                metrics['avg_velo'] = df['release_speed'].dropna().mean()
            
            if 'release_spin_rate' in df.columns:
                metrics['avg_spin_rate'] = df['release_spin_rate'].dropna().mean()
            
            # Pitch mix
            if 'pitch_type' in df.columns:
                pitch_counts = df['pitch_type'].value_counts()
                total_pitches = pitch_counts.sum()
                
                if total_pitches > 0:
                    metrics['pitch_mix'] = {pitch: count/total_pitches*100 for pitch, count in pitch_counts.items()}
            
            # Plate discipline metrics
            if 'description' in df.columns:
                swings = df[df['description'].isin(['hit_into_play', 'swinging_strike', 'foul'])].shape[0]
                takes = df[df['description'].isin(['ball', 'called_strike'])].shape[0]
                whiffs = df[df['description'] == 'swinging_strike'].shape[0]
                
                if swings + takes > 0:
                    metrics['swing_pct'] = swings / (swings + takes) * 100
                
                if swings > 0:
                    metrics['whiff_pct'] = whiffs / swings * 100
            
            # Zone control
            if 'zone' in df.columns:
                in_zone = df[df['zone'] <= 9].shape[0]  # Zones 1-9 are in the strike zone
                out_zone = df[df['zone'] > 9].shape[0]
                
                if in_zone + out_zone > 0:
                    metrics['zone_pct'] = in_zone / (in_zone + out_zone) * 100
            
            # Outcome metrics
            if 'events' in df.columns:
                strikeouts = df[df['events'] == 'strikeout'].shape[0]
                walks = df[df['events'].isin(['walk', 'intent_walk'])].shape[0]
                
                batters_faced = len(events)
                if batters_faced > 0:
                    metrics['k_pct'] = strikeouts / batters_faced * 100
                    metrics['bb_pct'] = walks / batters_faced * 100
        
        return metrics
    
    def _calculate_trend_indicators(self, period_metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate trend indicators by comparing different time periods.
        
        Args:
            period_metrics: Metrics for different time periods
            
        Returns:
            Dict: Trend indicators showing changes between periods
        """
        indicators = {}
        
        # Skip if we don't have enough data
        if not all(k in period_metrics for k in ['last7', 'last15', 'last30']):
            return indicators
        
        # Key metrics to track for trends
        batter_metrics = ['avg_exit_velo', 'barrel_rate', 'ld_pct', 'whiff_pct', 'batting_avg']
        pitcher_metrics = ['avg_velo', 'whiff_pct', 'zone_pct', 'k_pct', 'bb_pct']
        
        # Determine if we're dealing with a batter or pitcher based on available metrics
        is_batter = 'avg_exit_velo' in period_metrics.get('last30', {})
        metrics_to_check = batter_metrics if is_batter else pitcher_metrics
        
        # Compare last 7 days to last 30 days (recent trend)
        for metric in metrics_to_check:
            if metric in period_metrics.get('last7', {}) and metric in period_metrics.get('last30', {}):
                last7 = period_metrics['last7'].get(metric)
                last30 = period_metrics['last30'].get(metric)
                
                if last7 is not None and last30 is not None and last30 != 0:
                    # Calculate percent change
                    pct_change = (last7 - last30) / last30 * 100
                    indicators[f"{metric}_recent_pct_change"] = pct_change
                    
                    # Determine if this is significant (>10% change)
                    is_significant = abs(pct_change) > 10
                    indicators[f"{metric}_trend_significant"] = is_significant
                    
                    # Determine if this is positive or negative
                    # For most metrics, higher is better for batters (except whiff_pct)
                    # For pitchers, higher is better for some (k_pct, whiff_pct) and worse for others (bb_pct)
                    if is_batter:
                        if metric == 'whiff_pct':
                            indicators[f"{metric}_trend_positive"] = pct_change < 0
                        else:
                            indicators[f"{metric}_trend_positive"] = pct_change > 0
                    else:  # pitcher
                        if metric in ['k_pct', 'whiff_pct', 'zone_pct']:
                            indicators[f"{metric}_trend_positive"] = pct_change > 0
                        elif metric == 'bb_pct':
                            indicators[f"{metric}_trend_positive"] = pct_change < 0
                        else:
                            # For velocity, we usually want consistency
                            indicators[f"{metric}_trend_positive"] = abs(pct_change) < 5
        
        # Overall trend indicator
        positive_trends = sum(1 for k, v in indicators.items() if k.endswith('_trend_positive') and v)
        negative_trends = sum(1 for k, v in indicators.items() if k.endswith('_trend_positive') and not v)
        significant_trends = sum(1 for k, v in indicators.items() if k.endswith('_trend_significant') and v)
        
        total_tracked = sum(1 for k in indicators if k.endswith('_trend_positive'))
        
        if total_tracked > 0:
            indicators['overall_trend_score'] = (positive_trends - negative_trends) / total_tracked
            indicators['significant_changes'] = significant_trends
            
            # Overall assessment
            if indicators['overall_trend_score'] > 0.6 and significant_trends >= 2:
                indicators['trend_assessment'] = "Strong positive trend"
            elif indicators['overall_trend_score'] > 0.3:
                indicators['trend_assessment'] = "Positive trend"
            elif indicators['overall_trend_score'] < -0.6 and significant_trends >= 2:
                indicators['trend_assessment'] = "Strong negative trend"
            elif indicators['overall_trend_score'] < -0.3:
                indicators['trend_assessment'] = "Negative trend"
            else:
                indicators['trend_assessment'] = "Stable performance"
        
        return indicators
    
    def get_player_id_mapping(self) -> Dict[str, int]:
        """
        Get mapping of player names to MLB IDs.
        
        Returns:
            Dict: Mapping of player names to MLB IDs
        """
        # This is a simplified implementation - in reality, you would want to use
        # a more comprehensive source for player IDs
        
        # Get batters leaderboard to extract player IDs
        batters_df = self.get_statcast_leaderboard(player_type="batter", min_pa=10)
        pitchers_df = self.get_statcast_leaderboard(player_type="pitcher", min_pitches=10)
        
        mapping = {}
        
        # Process batters
        if not batters_df.empty and 'player_id' in batters_df.columns and 'player_name' in batters_df.columns:
            batters_mapping = dict(zip(batters_df['player_name'], batters_df['player_id']))
            mapping.update(batters_mapping)
        
        # Process pitchers
        if not pitchers_df.empty and 'player_id' in pitchers_df.columns and 'player_name' in pitchers_df.columns:
            pitchers_mapping = dict(zip(pitchers_df['player_name'], pitchers_df['player_id']))
            mapping.update(pitchers_mapping)
        
        return mapping
    
    def find_breakout_candidates(self, player_type: str = "batter", min_sample: int = 20) -> List[Dict[str, Any]]:
        """
        Find players showing signs of potential breakouts based on Statcast metrics.
        
        Args:
            player_type: 'batter' or 'pitcher'
            min_sample: Minimum sample size to consider
            
        Returns:
            List: Potential breakout candidates with supporting metrics
        """
        # Get leaderboard data for the current season
        if player_type == "batter":
            df = self.get_statcast_leaderboard(player_type="batter", min_pa=min_sample)
            key_metrics = ['xba', 'xslg', 'xwoba', 'barrel_batted_rate', 'sweet_spot_percent', 'avg_exit_velocity']
        else:
            df = self.get_statcast_leaderboard(player_type="pitcher", min_pitches=min_sample)
            key_metrics = ['xera', 'xwoba', 'xba', 'barrel_batted_rate', 'sweet_spot_percent', 'avg_exit_velocity']
        
        # Early exit if data retrieval failed
        if df.empty:
            logger.warning(f"Failed to retrieve leaderboard data for {player_type}s")
            return []
        
        # Ensure player_id is available
        if 'player_id' not in df.columns:
            logger.warning("player_id column not found in leaderboard data")
            return []
        
        # Create a subset of players with metrics better than their actual results
        breakout_candidates = []
        
        # For batters, look for players with xStats > actual stats
        if player_type == "batter":
            # Check if the necessary columns exist
            if all(col in df.columns for col in ['player_name', 'player_id', 'ba', 'xba', 'slg', 'xslg', 'woba', 'xwoba']):
                # Calculate differences
                df['ba_diff'] = df['xba'] - df['ba']
                df['slg_diff'] = df['xslg'] - df['slg']
                df['woba_diff'] = df['xwoba'] - df['woba']
                
                # Identify potential breakout candidates
                candidates = df[
                    (df['ba_diff'] > 0.020) |  # Expected BA at least 20 points higher
                    (df['slg_diff'] > 0.050) |  # Expected SLG at least 50 points higher
                    (df['woba_diff'] > 0.030)   # Expected wOBA at least 30 points higher
                ]
                
                # Calculate a composite "breakout score"
                candidates['breakout_score'] = (
                    (candidates['ba_diff'] / 0.020) + 
                    (candidates['slg_diff'] / 0.050) + 
                    (candidates['woba_diff'] / 0.030)
                ) / 3
                
                # Sort by breakout score
                candidates = candidates.sort_values('breakout_score', ascending=False)
                
                # Convert to list of dictionaries
                for _, row in candidates.head(20).iterrows():
                    player_data = {
                        'player_id': row['player_id'],
                        'name': row['player_name'],
                        'team': row.get('team', 'N/A'),
                        'breakout_score': row['breakout_score'],
                        'metrics': {
                            'ba': row['ba'],
                            'xba': row['xba'],
                            'ba_diff': row['ba_diff'],
                            'slg': row['slg'],
                            'xslg': row['xslg'],
                            'slg_diff': row['slg_diff'],
                            'woba': row['woba'],
                            'xwoba': row['xwoba'],
                            'woba_diff': row['woba_diff'],
                            'barrel_rate': row.get('barrel_batted_rate', None),
                            'exit_velo': row.get('avg_exit_velocity', None),
                            'sweet_spot': row.get('sweet_spot_percent', None)
                        },
                        'reason': self._generate_breakout_reason(row, player_type)
                    }
                    breakout_candidates.append(player_data)
        
        # For pitchers, look for pitchers with xStats < actual stats
        else:
            # Check if the necessary columns exist
            if all(col in df.columns for col in ['player_name', 'player_id', 'era', 'xera', 'woba', 'xwoba']):
                # Calculate differences (for pitchers, negative is better)
                df['era_diff'] = df['xera'] - df['era']
                df['woba_diff'] = df['xwoba'] - df['woba']
                
                # Identify potential breakout candidates
                candidates = df[
                    (df['era_diff'] < -0.50) |  # Expected ERA at least 0.50 lower
                    (df['woba_diff'] < -0.020)  # Expected wOBA at least 20 points lower
                ]
                
                # Calculate a composite "breakout score" (negative is better for pitchers)
                candidates['breakout_score'] = (
                    (candidates['era_diff'] / -0.50) + 
                    (candidates['woba_diff'] / -0.020)
                ) / 2
                
                # Convert to positive score for easier interpretation
                candidates['breakout_score'] = candidates['breakout_score'].abs()
                
                # Sort by breakout score
                candidates = candidates.sort_values('breakout_score', ascending=False)
                
                # Convert to list of dictionaries
                for _, row in candidates.head(20).iterrows():
                    player_data = {
                        'player_id': row['player_id'],
                        'name': row['player_name'],
                        'team': row.get('team', 'N/A'),
                        'breakout_score': row['breakout_score'],
                        'metrics': {
                            'era': row['era'],
                            'xera': row['xera'],
                            'era_diff': row['era_diff'],
                            'woba': row['woba'],
                            'xwoba': row['xwoba'],
                            'woba_diff': row['woba_diff'],
                            'whiff_rate': row.get('whiff_percent', None),
                            'k_rate': row.get('k_percent', None),
                            'barrel_rate': row.get('barrel_batted_rate', None)
                        },
                        'reason': self._generate_breakout_reason(row, player_type)
                    }
                    breakout_candidates.append(player_data)
        
        return breakout_candidates
    
    def _generate_breakout_reason(self, player_row: pd.Series, player_type: str) -> str:
        """
        Generate a human-readable explanation for why a player is a breakout candidate.
        
        Args:
            player_row: Row of player data
            player_type: 'batter' or 'pitcher'
            
        Returns:
            str: Explanation for breakout candidacy
        """
        reasons = []
        
        if player_type == "batter":
            # Check for substantial xBA > BA
            if player_row.get('ba_diff', 0) > 0.030:
                reasons.append(f"Expected batting average (.{int(player_row['xba']*1000):03d}) significantly higher than actual (.{int(player_row['ba']*1000):03d})")
            
            # Check for substantial xSLG > SLG
            if player_row.get('slg_diff', 0) > 0.080:
                reasons.append(f"Expected slugging (.{int(player_row['xslg']*1000):03d}) significantly higher than actual (.{int(player_row['slg']*1000):03d})")
            
            # Check for high barrel rate
            if player_row.get('barrel_batted_rate', 0) > 10:
                reasons.append(f"Excellent barrel rate ({player_row['barrel_batted_rate']:.1f}%)")
            
            # Check for high exit velocity
            if player_row.get('avg_exit_velocity', 0) > 90:
                reasons.append(f"Strong exit velocity ({player_row['avg_exit_velocity']:.1f} mph)")
            
            # Check for high sweet spot percentage
            if player_row.get('sweet_spot_percent', 0) > 35:
                reasons.append(f"High sweet spot rate ({player_row['sweet_spot_percent']:.1f}%)")
            
        else:  # pitcher
            # Check for substantial xERA < ERA
            if player_row.get('era_diff', 0) < -0.70:
                reasons.append(f"Expected ERA ({player_row['xera']:.2f}) significantly lower than actual ({player_row['era']:.2f})")
            
            # Check for substantial xwOBA < wOBA
            if player_row.get('woba_diff', 0) < -0.030:
                reasons.append(f"Expected wOBA (.{int(player_row['xwoba']*1000):03d}) significantly lower than actual (.{int(player_row['woba']*1000):03d})")
            
            # Check for high whiff rate
            if player_row.get('whiff_percent', 0) > 30:
                reasons.append(f"Excellent swing-and-miss rate ({player_row['whiff_percent']:.1f}%)")
            
            # Check for low barrel rate
            if player_row.get('barrel_batted_rate', 100) < 5:
                reasons.append(f"Low barrel rate allowed ({player_row['barrel_batted_rate']:.1f}%)")
            
        # If no specific reasons found, provide a general statement
        if not reasons:
            if player_type == "batter":
                reasons.append("Overall expected stats suggest potential for improvement")
            else:
                reasons.append("Overall expected stats suggest better performance than results indicate")
        
        return ". ".join(reasons)