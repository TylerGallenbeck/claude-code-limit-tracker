#!/usr/bin/env python3
"""
Status line generator for Claude Code integration.
Reads JSON input from stdin and outputs formatted status line.
"""

import json
import sys
import time
import os
from pathlib import Path
from tracker import UsageTracker
from config import Config
from git_info import GitInfo

def generate_status_line():
    """Generate status line output for Claude Code."""

    # Try to get project path from stdin JSON (provided by Claude Code)
    project_path = None
    try:
        if not sys.stdin.isatty():
            stdin_data = sys.stdin.read().strip()
            if stdin_data:
                data = json.loads(stdin_data)
                project_path = data.get('projectPath') or data.get('project_path')
    except (json.JSONDecodeError, IOError):
        pass

    # Fallback to current working directory
    if not project_path:
        project_path = os.getcwd()

    # Get project name
    try:
        project_name = Path(project_path).name
    except:
        project_name = 'unknown'
    
    # Initialize components
    config = Config()
    tracker = UsageTracker()
    git_info = GitInfo(cache_duration=config.git_cache_duration)
    
    # Get current usage data
    usage = tracker.update()
    limits = config.get_tier_limits()
    
    # Calculate time remaining in 5h cycle
    now = time.time()
    cycle_end = usage.current_5h_start + (5 * 3600)
    time_remaining = cycle_end - now
    
    # Format parts
    parts = []
    
    # Project name
    parts.append(f"📁 {project_name}")
    
    # Add git information if enabled
    if config.show_git_info:
        git_status = git_info.get_git_status(project_path)
        git_display = git_info.format_git_info(git_status)
        if git_display:
            parts.append(git_display)
    
    # Current model - try multiple detection methods
    current_model = "Sonnet 4.5"  # Default

    # Method 1: Check Claude stats cache for most recent model
    try:
        stats_cache = Path.home() / ".claude" / "stats-cache.json"
        if stats_cache.exists():
            with open(stats_cache, 'r') as f:
                stats = json.load(f)
                model_usage = stats.get('modelUsage', {})

                # Filter for Claude models only
                claude_models = {
                    'claude-sonnet-4': 'Sonnet 4',
                    'claude-sonnet-4.5': 'Sonnet 4.5',
                    'claude-opus-4': 'Opus 4',
                    'claude-opus-4.1': 'Opus 4.1',
                    'claude-opus-4.5': 'Opus 4.5',
                }

                # Find most recently used Claude model
                for model in model_usage.keys():
                    model_lower = model.lower()
                    if 'sonnet' in model_lower or 'opus' in model_lower:
                        if 'opus' in model_lower:
                            if '4.5' in model_lower or '4_5' in model_lower:
                                current_model = "Opus 4.5"
                            elif '4.1' in model_lower or '4_1' in model_lower:
                                current_model = "Opus 4.1"
                            else:
                                current_model = "Opus 4"
                        elif 'sonnet' in model_lower:
                            if '4.5' in model_lower or '4_5' in model_lower:
                                current_model = "Sonnet 4.5"
                            else:
                                current_model = "Sonnet 4"
                        break  # Use first match
    except:
        pass

    # Method 2: Check environment variables
    if current_model == "Sonnet 4.5":  # Still default, try env var
        claude_model = os.environ.get('CLAUDE_MODEL', '').lower()
        if 'opus' in claude_model:
            if '4.5' in claude_model or '4_5' in claude_model:
                current_model = "Opus 4.5"
            else:
                current_model = "Opus 4"
        elif 'sonnet' in claude_model:
            if '4.5' in claude_model or '4_5' in claude_model:
                current_model = "Sonnet 4.5"
            else:
                current_model = "Sonnet 4"

    # Method 3: Check Claude settings.json
    if current_model == "Sonnet 4.5":  # Still default, try settings
        try:
            settings_path = Path.home() / ".claude" / "settings.json"
            if settings_path.exists():
                with open(settings_path, 'r') as f:
                    settings = json.load(f)
                    model_setting = settings.get('model', '').lower()
                    if 'opus' in model_setting:
                        if '4.5' in model_setting or '4_5' in model_setting:
                            current_model = "Opus 4.5"
                        else:
                            current_model = "Opus 4"
                    elif 'sonnet' in model_setting:
                        if '4.5' in model_setting or '4_5' in model_setting:
                            current_model = "Sonnet 4.5"
                        else:
                            current_model = "Sonnet 4"
        except:
            pass
    
    parts.append(f"🤖 {current_model}")
    
    # 5-hour cycle usage
    color = config.get_usage_color(usage.current_5h_prompts, limits.cycle_5h_max)
    percentage = int((usage.current_5h_prompts / limits.cycle_5h_max) * 100) if limits.cycle_5h_max > 0 else 0
    parts.append(f"\033[38;2;{color[0]};{color[1]};{color[2]}m⚡{usage.current_5h_prompts}/{limits.cycle_5h_max}p ({percentage}%)\033[0m")
    
    # Weekly usage based on tier
    if config.tier in ['max_5x', 'max_20x']:
        # Show both Sonnet and Opus
        sonnet_color = config.get_usage_color(usage.weekly_sonnet_hours, limits.weekly_sonnet_max)
        opus_color = config.get_usage_color(usage.weekly_opus_hours, limits.weekly_opus_max or 0)
        
        parts.append(f"\033[38;2;{sonnet_color[0]};{sonnet_color[1]};{sonnet_color[2]}m📅 S4: {usage.weekly_sonnet_hours:.1f}h/{limits.weekly_sonnet_max}h\033[0m")
        parts.append(f"\033[38;2;{opus_color[0]};{opus_color[1]};{opus_color[2]}mO4: {usage.weekly_opus_hours:.1f}h/{limits.weekly_opus_max or 0}h\033[0m")
    else:
        # Free/Pro - Sonnet only
        color = config.get_usage_color(usage.weekly_sonnet_hours, limits.weekly_sonnet_max)
        parts.append(f"\033[38;2;{color[0]};{color[1]};{color[2]}m📅 {usage.weekly_sonnet_hours:.1f}h/{limits.weekly_sonnet_max}h\033[0m")
    
    # Time until reset
    parts.append(f"🔄 {config.format_time_remaining(time_remaining)}")
    
    # Output the status line
    status_line = " | ".join(parts)
    print(status_line)

if __name__ == "__main__":
    generate_status_line()