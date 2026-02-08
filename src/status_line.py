#!/usr/bin/env python3
"""
Status line generator for Claude Code integration.
Reads JSON input from stdin and outputs formatted status line.
Fetches real usage data from Anthropic's OAuth API.
"""

import json
import subprocess
import sys
import time
import os
from pathlib import Path
from datetime import datetime, timezone
from tracker import UsageTracker
from config import Config
from git_info import GitInfo

# Cache usage API results to avoid hitting it on every status line update
USAGE_CACHE_FILE = Path(__file__).parent.parent / "data" / "usage_cache.json"
USAGE_CACHE_MAX_AGE = 60  # seconds


def fetch_usage():
    """Fetch usage data from Anthropic OAuth API with caching.

    Returns dict with five_hour, seven_day, etc. or None on failure.
    Caches results to disk for USAGE_CACHE_MAX_AGE seconds.
    """
    # Check cache first
    try:
        if USAGE_CACHE_FILE.exists():
            age = time.time() - USAGE_CACHE_FILE.stat().st_mtime
            if age < USAGE_CACHE_MAX_AGE:
                with open(USAGE_CACHE_FILE, 'r') as f:
                    return json.load(f)
    except:
        pass

    # Fetch from API
    try:
        creds_raw = subprocess.run(
            ['security', 'find-generic-password', '-s', 'Claude Code-credentials', '-w'],
            capture_output=True, text=True, timeout=5
        )
        if creds_raw.returncode != 0:
            return None

        creds = json.loads(creds_raw.stdout.strip())
        token = creds['claudeAiOauth']['accessToken']

        result = subprocess.run(
            ['curl', '-s', '--max-time', '5',
             '-H', f'Authorization: Bearer {token}',
             '-H', 'anthropic-beta: oauth-2025-04-20',
             '-H', 'User-Agent: claude-code/2.0.31',
             'https://api.anthropic.com/api/oauth/usage'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return None

        usage = json.loads(result.stdout)

        # Cache it (only usage data, never credentials)
        USAGE_CACHE_FILE.parent.mkdir(exist_ok=True)
        with open(USAGE_CACHE_FILE, 'w') as f:
            json.dump(usage, f)

        return usage
    except:
        return None


def format_api_reset_time(resets_at):
    """Format an ISO reset timestamp as relative duration."""
    if not resets_at:
        return None
    try:
        reset_dt = datetime.fromisoformat(resets_at)
        now = datetime.now(timezone.utc)
        remaining = (reset_dt - now).total_seconds()
        if remaining <= 0:
            return "resetting..."
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        if hours > 24:
            days = hours // 24
            hours = hours % 24
            return f"{days}d{hours}h"
        elif hours > 0:
            return f"{hours}h{minutes}m"
        else:
            return f"{minutes}m"
    except:
        return None


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

    # Get JSONL-based usage data (used as fallback if API unavailable)
    tracker_usage = tracker.update()
    limits = config.get_tier_limits()

    # Fetch real usage from Anthropic API
    api_usage = fetch_usage()

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

    # Usage data: prefer API, fall back to JSONL tracker
    if api_usage:
        # 5-hour cycle from API
        five_hour = api_usage.get('five_hour', {})
        if five_hour:
            pct = int(five_hour.get('utilization', 0) or 0)
            color = config.get_usage_color(pct, 100)
            reset = format_api_reset_time(five_hour.get('resets_at'))
            parts.append(f"\033[38;2;{color[0]};{color[1]};{color[2]}m⚡5h: {pct}%\033[0m")
            if reset:
                parts.append(f"🔄 {reset}")

        # 7-day overall from API
        seven_day = api_usage.get('seven_day', {})
        if seven_day:
            pct = int(seven_day.get('utilization', 0) or 0)
            color = config.get_usage_color(pct, 100)
            reset = format_api_reset_time(seven_day.get('resets_at'))
            reset_str = f" 🔄{reset}" if reset else ""
            parts.append(f"\033[38;2;{color[0]};{color[1]};{color[2]}m📅 7d: {pct}%{reset_str}\033[0m")
    else:
        # Fallback: JSONL-based tracking
        color = config.get_usage_color(tracker_usage.current_5h_prompts, limits.cycle_5h_max)
        percentage = int((tracker_usage.current_5h_prompts / limits.cycle_5h_max) * 100) if limits.cycle_5h_max > 0 else 0
        parts.append(f"\033[38;2;{color[0]};{color[1]};{color[2]}m⚡{tracker_usage.current_5h_prompts}/{limits.cycle_5h_max}p ({percentage}%)\033[0m")

        # Weekly usage based on tier
        if config.tier in ['max_5x', 'max_20x']:
            sonnet_color = config.get_usage_color(tracker_usage.weekly_sonnet_hours, limits.weekly_sonnet_max)
            opus_color = config.get_usage_color(tracker_usage.weekly_opus_hours, limits.weekly_opus_max or 0)
            parts.append(f"\033[38;2;{sonnet_color[0]};{sonnet_color[1]};{sonnet_color[2]}m📅 S4: {tracker_usage.weekly_sonnet_hours:.1f}h/{limits.weekly_sonnet_max}h\033[0m")
            parts.append(f"\033[38;2;{opus_color[0]};{opus_color[1]};{opus_color[2]}mO4: {tracker_usage.weekly_opus_hours:.1f}h/{limits.weekly_opus_max or 0}h\033[0m")
        else:
            color = config.get_usage_color(tracker_usage.weekly_sonnet_hours, limits.weekly_sonnet_max)
            parts.append(f"\033[38;2;{color[0]};{color[1]};{color[2]}m📅 {tracker_usage.weekly_sonnet_hours:.1f}h/{limits.weekly_sonnet_max}h\033[0m")

        # Time until reset (JSONL-based)
        now = time.time()
        cycle_end = tracker_usage.current_5h_start + (5 * 3600)
        time_remaining = cycle_end - now
        parts.append(f"🔄 {config.format_time_remaining(time_remaining)}")

    # Context window remaining (from stdin data)
    ctx_win = stdin_data.get('context_window', {})
    ctx_remaining = ctx_win.get('remaining_percentage')
    if ctx_remaining is None:
        used_pct = ctx_win.get('used_percentage')
        if used_pct is not None:
            ctx_remaining = 100 - int(used_pct)
    if ctx_remaining is not None:
        ctx_remaining = int(ctx_remaining)
        if ctx_remaining > 50:
            ctx_color = (0, 255, 0)
        elif ctx_remaining > 25:
            ctx_color = (255, 255, 0)
        else:
            ctx_color = (255, 150, 150)
        parts.append(f"\033[38;2;{ctx_color[0]};{ctx_color[1]};{ctx_color[2]}m🧠 ctx: {ctx_remaining}%\033[0m")

    # Output the status line
    status_line = " | ".join(parts)
    print(status_line)

if __name__ == "__main__":
    generate_status_line()
