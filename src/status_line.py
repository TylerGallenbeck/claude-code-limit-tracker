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

    # Read JSON input from stdin (Claude Code sends session data)
    stdin_data = {}
    try:
        if not sys.stdin.isatty():
            input_text = sys.stdin.read()
            if input_text:
                stdin_data = json.loads(input_text)
    except:
        pass

    # Get current project name from stdin or working directory
    try:
        project_path = stdin_data.get('workspace', {}).get('current_dir') or os.getcwd()
        project_name = Path(project_path).name

        # If we're in the tracker directory, use that
        if project_name == 'claude-code-usage-tracking':
            project_name = 'usage-tracker'
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
    
    # Current model - prefer stdin data from Claude Code (authoritative)
    current_model = None
    stdin_model = stdin_data.get('model', {})
    if stdin_model:
        current_model = stdin_model.get('display_name')

    # Fallback chain if stdin didn't provide model
    if not current_model:
        model_id = (stdin_model.get('id') or '').lower() if stdin_model else ''
        claude_model = os.environ.get('CLAUDE_MODEL', '').lower()
        combined = model_id + ' ' + claude_model
        if 'opus' in combined:
            current_model = "Opus 4"
        elif 'sonnet' in combined:
            current_model = "Sonnet 4"
        elif 'haiku' in combined:
            current_model = "Haiku"
        else:
            # Last resort: check settings.json
            try:
                settings_path = Path.home() / ".claude" / "settings.json"
                if settings_path.exists():
                    with open(settings_path, 'r') as f:
                        settings = json.load(f)
                        model_setting = settings.get('model', '').lower()
                        if 'opus' in model_setting:
                            current_model = "Opus 4"
                        elif 'sonnet' in model_setting:
                            current_model = "Sonnet 4"
            except:
                pass

    if current_model:
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