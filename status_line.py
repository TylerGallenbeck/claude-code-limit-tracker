#!/usr/bin/env python3
"""
Standalone status line script for Claude Code integration.
"""

import sys
import os

# Add src directory to path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from status_line import generate_status_line

if __name__ == "__main__":
    # Let the function use environment variables or os.getcwd()
    generate_status_line()