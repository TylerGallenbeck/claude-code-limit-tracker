#!/usr/bin/env python3
"""
Configuration management for Claude Code usage tracker.
Handles subscription tiers and limits.
"""

import json
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass
import os

@dataclass
class TierLimits:
    """Subscription tier limits."""
    tier: str
    cycle_5h_min: int
    cycle_5h_max: int
    weekly_sonnet_min: int
    weekly_sonnet_max: int
    weekly_opus_min: Optional[int] = None
    weekly_opus_max: Optional[int] = None

class Config:
    """Configuration manager for Claude Code usage tracker."""
    
    # Define tier limits based on Claude's actual limits
    TIER_LIMITS = {
        "free": TierLimits(
            tier="free",
            cycle_5h_min=10,
            cycle_5h_max=40,
            weekly_sonnet_min=40,
            weekly_sonnet_max=80
        ),
        "pro": TierLimits(
            tier="pro", 
            cycle_5h_min=10,
            cycle_5h_max=40,
            weekly_sonnet_min=40,
            weekly_sonnet_max=80
        ),
        "max_5x": TierLimits(
            tier="max_5x",
            cycle_5h_min=50,
            cycle_5h_max=200,
            weekly_sonnet_min=140,
            weekly_sonnet_max=280,
            weekly_opus_min=15,
            weekly_opus_max=35
        ),
        "max_20x": TierLimits(
            tier="max_20x",
            cycle_5h_min=200,
            cycle_5h_max=800,
            weekly_sonnet_min=240,
            weekly_sonnet_max=480,
            weekly_opus_min=24,
            weekly_opus_max=40
        )
    }
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration."""
        self.config_dir = config_dir or Path(__file__).parent.parent / "config"
        self.config_dir.mkdir(exist_ok=True)
        
        self.user_config_path = self.config_dir / "user_config.json"
        self.limits_path = self.config_dir / "limits.json"
        
        # Load or create user config
        self.tier = self._load_user_tier()
        
        # Load git settings with defaults
        self.show_git_info = True
        self.git_cache_duration = 5
        self._load_git_settings()
        
        # Save limits for reference
        self._save_limits()
    
    def _load_user_tier(self) -> str:
        """Load user's subscription tier."""
        if self.user_config_path.exists():
            try:
                with open(self.user_config_path, 'r') as f:
                    data = json.load(f)
                    return data.get('subscription_tier', 'pro')
            except:
                pass
        
        # Default to pro
        return 'pro'
    
    def _load_git_settings(self) -> None:
        """Load git configuration settings."""
        if self.user_config_path.exists():
            try:
                with open(self.user_config_path, 'r') as f:
                    data = json.load(f)
                    git_config = data.get('git_settings', {})
                    
                    self.show_git_info = git_config.get('show_git_info', True)
                    self.git_cache_duration = git_config.get('cache_duration', 5)
            except:
                pass  # Use defaults if loading fails
    
    def _save_limits(self):
        """Save all tier limits to JSON for reference."""
        limits_data = {}
        for tier_name, limits in self.TIER_LIMITS.items():
            limits_data[tier_name] = {
                "5h_cycle": {
                    "min": limits.cycle_5h_min,
                    "max": limits.cycle_5h_max
                },
                "weekly_sonnet": {
                    "min": limits.weekly_sonnet_min,
                    "max": limits.weekly_sonnet_max
                }
            }
            if limits.weekly_opus_min is not None:
                limits_data[tier_name]["weekly_opus"] = {
                    "min": limits.weekly_opus_min,
                    "max": limits.weekly_opus_max
                }
        
        with open(self.limits_path, 'w') as f:
            json.dump(limits_data, f, indent=2)
    
    def get_tier_limits(self) -> TierLimits:
        """Get current tier limits."""
        return self.TIER_LIMITS.get(self.tier, self.TIER_LIMITS['pro'])
    
    def set_tier(self, tier: str):
        """Set subscription tier."""
        if tier not in self.TIER_LIMITS:
            raise ValueError(f"Invalid tier: {tier}. Must be one of: {list(self.TIER_LIMITS.keys())}")
        
        self.tier = tier
        
        # Save to config
        config_data = {
            "subscription_tier": tier,
            "configured": True,
            "git_settings": {
                "show_git_info": self.show_git_info,
                "cache_duration": self.git_cache_duration
            }
        }
        
        with open(self.user_config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def get_usage_color(self, current: float, max_limit: float) -> tuple:
        """
        Get RGB color based on usage percentage.
        Returns tuple of (r, g, b) values.
        """
        percentage = (current / max_limit) * 100 if max_limit > 0 else 0
        
        if percentage < 50:
            # Green
            return (0, 255, 0)
        elif percentage < 75:
            # Yellow
            return (255, 255, 0)
        else:
            # Very Bright Red (highly readable)
            return (255, 150, 150)
    
    def format_time_remaining(self, seconds: float) -> str:
        """Format seconds remaining into human readable format."""
        if seconds <= 0:
            return "resetting..."
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if hours > 0:
            return f"{hours}h{minutes}m"
        else:
            return f"{minutes}m"
    
    def interactive_setup(self):
        """Interactive setup for choosing subscription tier."""
        print("\n=== Claude Code Usage Tracker Configuration ===\n")
        print("Select your Claude subscription tier:\n")
        
        tiers = list(self.TIER_LIMITS.keys())
        for i, tier in enumerate(tiers, 1):
            limits = self.TIER_LIMITS[tier]
            print(f"  {i}. {tier.upper()}")
            print(f"     - 5h cycle: {limits.cycle_5h_min}-{limits.cycle_5h_max} prompts")
            print(f"     - Weekly Sonnet: {limits.weekly_sonnet_min}-{limits.weekly_sonnet_max} hours")
            if limits.weekly_opus_min:
                print(f"     - Weekly Opus: {limits.weekly_opus_min}-{limits.weekly_opus_max} hours")
            print()
        
        while True:
            try:
                choice = input("Enter your choice (1-4): ").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(tiers):
                    selected_tier = tiers[idx]
                    self.set_tier(selected_tier)
                    print(f"\n✓ Configured for {selected_tier.upper()} tier")
                    break
                else:
                    print("Invalid choice. Please enter a number between 1 and 4.")
            except (ValueError, KeyboardInterrupt):
                print("\nCancelled.")
                break
    
    def get_git_settings(self) -> Dict[str, Any]:
        """Get current git configuration settings."""
        return {
            "show_git_info": self.show_git_info,
            "cache_duration": self.git_cache_duration
        }
    
    def update_git_settings(self, show_git_info: Optional[bool] = None, 
                           cache_duration: Optional[int] = None) -> None:
        """
        Update git configuration settings.
        
        Args:
            show_git_info: Whether to show git info in status line
            cache_duration: Cache duration in seconds
        """
        if show_git_info is not None:
            self.show_git_info = show_git_info
        
        if cache_duration is not None:
            self.git_cache_duration = max(1, cache_duration)  # Min 1 second
        
        # Save updated config if we have a tier set
        if hasattr(self, 'tier'):
            self.set_user_tier(self.tier)