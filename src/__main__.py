#!/usr/bin/env python3
"""
Main entry point for Claude Code usage tracker CLI.
"""

from tracker import UsageTracker
from config import Config
import sys

def main():
    """Main CLI entry point."""
    if '--configure' in sys.argv:
        config = Config()
        config.interactive_setup()
    else:
        tracker = UsageTracker()
        usage = tracker.update()
        
        print("Claude Code Usage Statistics")
        print("=" * 40)
        print(f"5-hour cycle: {usage.current_5h_prompts} prompts")
        print(f"Weekly Sonnet: {usage.weekly_sonnet_hours:.1f} hours")
        print(f"Weekly Opus: {usage.weekly_opus_hours:.1f} hours")
        print(f"Total prompts this week: {usage.weekly_prompts}")
        print(f"Sessions analyzed: {len(usage.sessions)}")

if __name__ == "__main__":
    main()