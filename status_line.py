#!/usr/bin/env python3
"""
Standalone status line script for Claude Code integration.
"""

import sys
import os

# Get the current working directory before changing to script directory
current_cwd = os.getcwd()

# Add src directory to path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# Set environment variable for the current directory
os.environ['CLAUDE_CURRENT_DIR'] = current_cwd

from status_line import generate_status_line

if __name__ == "__main__":
    # Pass the current directory directly to the function
    generate_status_line(current_cwd)