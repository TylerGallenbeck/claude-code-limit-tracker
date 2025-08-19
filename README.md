# Claude Code Usage Tracker (Python Edition)

A high-performance Python-based usage tracking system for Claude Code that integrates with the status line to display real-time quota usage with accurate session time calculation.

## Features

- **Real Session Time Tracking**: Calculates actual conversation hours, not estimates
- **Dual Limit Tracking**: Monitor both 5-hour cycle limits and weekly quotas
- **Model-Specific Usage**: Separate tracking for Sonnet 4 vs Opus 4.1 usage
- **Subscription Tier Support**: Free, Pro ($20), Max 5x ($100), Max 20x ($200)
- **Status Line Integration**: Real-time display in Claude Code status line
- **Accurate Prompt Counting**: Tracks actual prompts from conversation data across ALL projects
- **Cross-Project Aggregation**: Counts usage from all Claude projects, not just current
- **Command Filtering**: Excludes local commands (like model switching) from prompt counts
- **Optimized Performance**: Uses numpy for fast timestamp processing

## Quick Start

### Prerequisites

1. Install `uv` (fast Python package manager):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Ensure Python 3.8+ is installed

### Installation

```bash
# Clone or download this repository
cd claude-code-usage-tracking

# Run the installation script
python install.py
```

The installer will:
1. Create a virtual environment
2. Install numpy for fast calculations
3. Configure your subscription tier
4. Integrate with Claude Code's status line
5. Test the installation

## Usage

The tracker automatically displays usage information in your Claude Code status line:

**For Pro Users (Sonnet 4 only):**
```
📁 project | 🤖 S4 | ⚡15/40 (37%) | 📅 12.5h (31%) | 🔄 2h15m
```

**For Max Users (both models available):**
```
📁 project | 🤖 O4 | ⚡15/200 (7%) | 📅 S4:2.7h (1%) | O4:13.2h (38%) | 🔄 2h15m
```

Where:
- 📁 = Current project name
- 🤖 = Active model (S4=Sonnet 4, O4=Opus 4.1)
- ⚡ = 5-hour cycle prompts with percentage
- 📅 = Weekly hours with percentage
- 🔄 = Time until next 5-hour reset

## Configuration

To reconfigure your subscription tier:

```bash
python configure.py
```

## Limits Overview

### 5-Hour Cycle Limits (Shared Across Models)
The 5-hour limits are **shared** between Sonnet 4 and Opus 4:
- **Free/Pro**: 10-40 prompts per cycle
- **Max 5x**: 50-200 prompts per cycle
- **Max 20x**: 200-800 prompts per cycle

### Weekly Limits (Separate Per Model)
The weekly limits are **separate** for each model and tracked in actual session hours:
- **Free/Pro**: 40-80 hours of Sonnet 4 per week
- **Max 5x**: 140-280 hours Sonnet 4 + 15-35 hours Opus 4 per week  
- **Max 20x**: 240-480 hours Sonnet 4 + 24-40 hours Opus 4 per week

## Project Structure

```
claude-code-usage-tracking/
├── README.md
├── pyproject.toml             # Python package configuration
├── install.py                 # Installation script
├── configure.py              # Reconfigure subscription tier
├── status_line.py            # Status line entry point
├── claude_tracker/
│   ├── __init__.py
│   ├── tracker.py            # Core tracking logic with numpy
│   ├── config.py             # Configuration management
│   ├── status_line.py        # Status line generator
│   └── __main__.py           # CLI entry point
├── config/
│   ├── limits.json           # Subscription tier definitions
│   └── user_config.json      # User's selected tier
└── data/
    └── usage_data.json       # Usage tracking data
```

## How It Works

1. **Session Analysis**: Reads JSONL conversation files from `~/.claude/projects/`
2. **Time Calculation**: Uses numpy to efficiently process timestamps and calculate actual session durations
3. **Model Detection**: Analyzes assistant responses to determine model usage
4. **Cross-Project**: Aggregates usage across all Claude projects for account-wide tracking
5. **Status Line**: Updates in real-time with color-coded warnings based on usage percentage

## Manual Usage

```bash
# Run tracker manually
python -m claude_tracker

# Reconfigure subscription
python -m claude_tracker --configure
```

## Troubleshooting

- **"uv not found"**: Install uv using the curl command above
- **Status line not updating**: Restart Claude Code after installation
- **Wrong limits displayed**: Run `python configure.py` to update subscription tier

## Performance

This Python implementation is significantly faster than the bash version:
- Uses numpy for vectorized timestamp operations
- Implements caching to avoid re-parsing unchanged files
- Processes thousands of messages in milliseconds