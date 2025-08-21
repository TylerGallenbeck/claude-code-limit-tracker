# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a high-performance Python-based Claude Code usage tracking system that integrates with Claude Code's status line to display real-time quota usage information with accurate session time calculation. It tracks both 5-hour cycle limits and weekly quotas across different subscription tiers (Free, Pro, Max 5x, Max 20x) and models (Sonnet 4, Opus 4.1).

## Key Commands

### Installation and Setup
- `python install.py` - Main installation script that integrates with Claude Code settings
- `python install.py --test` - Test installation without making changes
- `python configure.py` - Interactive configuration for subscription tier selection

### Manual Operations
- `python -m claude_tracker` - Run usage tracking manually and display stats
- `python -m claude_tracker --configure` - Interactive configuration
- `python status_line.py` - Generate status line output (takes JSON input via stdin)

## Architecture

### Core Components

**Python Modules:**
- `claude_tracker/tracker.py` - Core tracking logic with numpy optimization for fast session analysis
- `claude_tracker/status_line.py` - Status line integration that generates formatted output for Claude Code
- `claude_tracker/config.py` - Configuration management for subscription tiers and limits
- `claude_tracker/__main__.py` - CLI entry point for manual usage

**Entry Points:**
- `install.py` - Installation script using uv for virtual environment and dependencies
- `configure.py` - Standalone configuration script
- `status_line.py` - Wrapper script for Claude Code status line integration

**Configuration:**
- `config/limits.json` - Subscription tier definitions with 5-hour and weekly limits
- `config/user_config.json` - User's selected subscription tier and preferences
- `data/usage_data.json` - Current usage tracking data (5-hour cycles and weekly totals)
- `pyproject.toml` - Python package configuration

### Data Flow

1. **Session Analysis**: `tracker.py` analyzes Claude conversation JSONL files in `~/.claude/projects/*/` to calculate actual session hours and count prompts
2. **Cross-Project Aggregation**: Counts usage across ALL projects, not just the current one, for account-wide tracking
3. **Model Detection**: Identifies which model (Sonnet vs Opus) was used by analyzing assistant responses and response ratios
4. **Command Filtering**: Excludes local command messages (model switching, etc.) that contain `<command-name>` or `<local-command-stdout>` tags
5. **Real Session Time**: Uses numpy to efficiently process timestamps and calculate actual conversation duration in hours
6. **Cycle Management**: Automatically resets 5-hour cycles (shared) and weekly cycles (per-model) based on timestamps
7. **Status Display**: `status_line.py` reads usage data and formats it appropriately for the user's subscription tier
8. **Integration**: Installation script updates `~/.claude/settings.json` to use the Python status line script

### Key Technical Details

- **Dependencies**: Requires Python 3.8+, numpy for fast array operations, uv for package management
- **Performance**: Uses numpy for vectorized timestamp operations and implements caching to avoid re-parsing unchanged files
- **Time Tracking**: Uses millisecond timestamps, calculates 5-hour cycles from epoch, tracks real session hours
- **Model Detection**: Analyzes assistant message models and calculates time ratios based on response counts
- **Color Coding**: Uses RGB color codes for status indication (green/yellow/red based on usage percentage)
- **Session Time Calculation**: Each JSONL file represents one session; duration calculated from first to last timestamp
- **Prompt Counting**: Accurately counts actual prompts from Claude conversation JSONL files, excluding meta messages and commands

### Subscription Tier Support

The system supports four subscription tiers with different limits:

**5-Hour Cycle Limits (Shared):**
- **Free/Pro**: 10-40 prompts total, Sonnet 4 only
- **Max 5x**: 50-200 prompts total across both models
- **Max 20x**: 200-800 prompts total across both models

**Weekly Limits (Separate per Model, in Actual Session Hours):**
- **Free/Pro**: 40-80 hours Sonnet 4 only
- **Max 5x**: 140-280 hours Sonnet 4 + 15-35 hours Opus 4
- **Max 20x**: 240-480 hours Sonnet 4 + 24-40 hours Opus 4

## Status Line Format

The system displays different formats based on subscription tier:

**Pro Users (Sonnet 4 only):**
`📁 project | 🤖 S4 | ⚡prompts/limit (%) | 📅 hours (%) | 🔄 time`

**Max Users (both models available):**
`📁 project | 🤖 model | ⚡prompts/limit (%) | 📅 S4:hours (%) | O4:hours (%) | 🔄 time`

Where:
- 📁 = Current project name
- 🤖 = Active model (S4=Sonnet 4, O4=Opus 4.1)
- ⚡ = 5-hour cycle prompts with percentage (shared across models)
- 📅 = Weekly session hours per model with percentage (e.g., S4:2.7h (1%), O4:13.2h (38%))
- 🔄 = Time until next 5-hour reset (e.g., 2h15m)

## File Locations

- **Claude Settings**: `~/.claude/settings.json` (backup created during install)
- **Claude Conversation Data**: `~/.claude/projects/[project-path]/*.jsonl` (JSONL files containing conversation history)
- **Virtual Environment**: `.venv/` (created by installation script)
- **Usage Data**: `data/usage_data.json` (usage statistics)
- **Configuration**: `config/user_config.json` (user's subscription tier)

## Performance Characteristics

This Python implementation provides significant performance improvements:
- **Fast Analysis**: Uses numpy for vectorized timestamp processing
- **Efficient Caching**: 5-second cache prevents re-parsing unchanged files
- **Real-Time Updates**: Updates usage data in milliseconds
- **Memory Efficient**: Processes thousands of messages without significant memory usage
- **Cross-Platform**: Works on macOS, Linux, and Windows with Python 3.8+
- Use uv run as a prefix in order to run files in this project