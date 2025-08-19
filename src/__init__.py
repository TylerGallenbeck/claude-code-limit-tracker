"""Claude Code Usage Tracker - Fast, accurate usage tracking for Claude Code."""

__version__ = "2.0.0"

from .tracker import UsageTracker
from .config import Config

__all__ = ["UsageTracker", "Config"]