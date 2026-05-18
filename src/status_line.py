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


def _format_model_label(model_id):
    """Turn 'claude-opus-4-7' into 'Opus 4.7'; return None on failure."""
    if not isinstance(model_id, str) or not model_id:
        return None
    cleaned = model_id.lower().strip()
    if "[" in cleaned:
        cleaned = cleaned.split("[", 1)[0]
    if cleaned.startswith("claude-"):
        cleaned = cleaned[len("claude-"):]
    families = {"opus": "Opus", "sonnet": "Sonnet", "haiku": "Haiku"}
    family_key = next((k for k in families if k in cleaned), None)
    if not family_key:
        return None
    tail = cleaned.split(family_key, 1)[1]
    digits = [seg for seg in tail.split("-") if seg.isdigit()]
    if len(digits) < 2:
        return None
    return f"{families[family_key]} {digits[0]}.{digits[1]}"


def generate_status_line():
    """Generate status line output for Claude Code."""

    stdin_payload = {}
    if not sys.stdin.isatty():
        try:
            raw = sys.stdin.read()
            if raw.strip():
                stdin_payload = json.loads(raw)
        except (json.JSONDecodeError, OSError, ValueError):
            stdin_payload = {}

    # Get current project name from working directory
    try:
        project_path = os.getcwd()
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
    
    current_model = None

    stdin_model = stdin_payload.get('model')
    if isinstance(stdin_model, dict):
        current_model = _format_model_label(stdin_model.get('id'))

    if not current_model:
        current_model = _format_model_label(os.environ.get('CLAUDE_MODEL'))

    if not current_model:
        try:
            settings_path = Path.home() / ".claude" / "settings.json"
            if settings_path.exists():
                with open(settings_path, 'r') as f:
                    settings = json.load(f)
                    current_model = _format_model_label(settings.get('model'))
        except (OSError, json.JSONDecodeError):
            pass

    if not current_model and usage.sessions:
        recent = usage.sessions[-1]
        if recent.opus_responses > recent.sonnet_responses:
            current_model = "Opus 4"
        elif recent.sonnet_responses > 0:
            current_model = "Sonnet 4"

    if not current_model:
        current_model = "Sonnet 4"

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
        
        parts.append(f"\033[38;2;{sonnet_color[0]};{sonnet_color[1]};{sonnet_color[2]}m📅 Sonnet: {usage.weekly_sonnet_hours:.1f}h/{limits.weekly_sonnet_max}h\033[0m")
        parts.append(f"\033[38;2;{opus_color[0]};{opus_color[1]};{opus_color[2]}mOpus: {usage.weekly_opus_hours:.1f}h/{limits.weekly_opus_max or 0}h\033[0m")
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