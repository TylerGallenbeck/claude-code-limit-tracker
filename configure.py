#!/usr/bin/env python3
"""
Configuration script for Claude Code Usage Tracker.
Allows reconfiguring subscription tier after installation.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from config import Config

def main():
    """Run interactive configuration."""
    print("Claude Code Usage Tracker - Configuration")
    print("=" * 50)
    
    config = Config()
    config.interactive_setup()
    
    print("\nConfiguration complete!")
    print("Your status line will now reflect the new tier limits.")

if __name__ == "__main__":
    main()