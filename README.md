# Claude Code Usage Tracker

Track your Claude usage with real-time quota monitoring in your status line. Shows actual conversation hours, not estimates.

## Quick Start

1. **Install uv** (Python package manager):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Clone and install**:
```bash
git clone https://github.com/TylerGallenbeck/claude-code-limit-tracker.git
cd claude-code-limit-tracker
uv run python install.py
```

That's it! Your status line will now show usage information.

## Status Line Display

**Pro Users:**
```
📁 project | 🌿 main* | 🤖 Sonnet 4 | ⚡15/40p (37%) | 📅 12.5h/80h | 🔄 2h15m
```

**Max Users:**
```
📁 project | 🌿 feature↑2? | 🤖 Opus 4 | ⚡15/200p (7%) | 📅 S4: 2.7h/280h | O4: 13.2h/35h | 🔄 2h15m
```

**Legend:**
- 📁 Current project directory
- 🌿 Git branch and status (see Git Status below)
- 🤖 Active model (Sonnet 4 or Opus 4)
- ⚡ 5-hour cycle prompts/limit (percentage)
- 📅 Weekly hours/limit for each model
- 🔄 Time until 5-hour cycle resets

### Git Status Indicators

The git branch display shows:

**Branch Examples:**
- `🌿 main` - Clean branch, up to date
- `🌿 feature` - Clean branch (long names auto-truncated)
- `🌿 (abc123)` - Detached HEAD state

**Status Indicators:**
- `*` - Modified files (uncommitted changes)
- `?` - Untracked files present
- `↑2` - 2 commits ahead of remote
- `↓3` - 3 commits behind remote  
- `↑1↓2` - Diverged (1 ahead, 2 behind)

**Color Coding:**
- 🟢 **Green** - Clean and up-to-date
- 🟡 **Yellow** - Dirty working tree (modified/untracked files)
- 🔵 **Blue** - Ahead of remote (commits to push)
- 🟠 **Orange** - Behind remote (need to pull)
- 🔴 **Red** - Git errors or conflicts

**Examples:**
- `🌿 main*` - Modified files on main branch
- `🌿 feature↑2*?` - Feature branch: 2 commits ahead, modified files, untracked files
- `🌿 main↓1` - Behind remote by 1 commit

## Features

- **Real session time tracking** - Calculates actual conversation hours
- **Git integration** - Shows current branch, status, and sync information
- **Cross-project monitoring** - Tracks usage across all Claude projects
- **Model-specific limits** - Separate weekly quotas for Sonnet 4 and Opus 4
- **All subscription tiers** - Works with Free, Pro, Max 5x, Max 20x
- **Smart filtering** - Excludes commands and system messages from counts
- **Fast performance** - Optimized with numpy for instant updates

## Configuration

Change your subscription tier anytime:
```bash
uv run python configure.py
```

## Usage Limits

### 5-Hour Cycles (Shared)
Limits shared between both models:
- **Free/Pro**: 10-40 prompts per cycle
- **Max 5x**: 50-200 prompts per cycle
- **Max 20x**: 200-800 prompts per cycle

### Weekly Limits (Per Model)
Separate limits for each model in actual hours:
- **Free/Pro**: 40-80 hours Sonnet 4 only
- **Max 5x**: 140-280h Sonnet 4 + 15-35h Opus 4
- **Max 20x**: 240-480h Sonnet 4 + 24-40h Opus 4

## Manual Usage

```bash
# View current usage stats
uv run python -m src

# Reconfigure subscription tier  
uv run python -m src --configure
```

## Troubleshooting

- **Status line not showing?** Restart Claude Code
- **Wrong limits?** Run `uv run python configure.py` to update your tier
- **Installation issues?** Make sure Python 3.8+ and uv are installed

## How It Works

The tracker analyzes your Claude conversation files (`~/.claude/projects/`) to calculate:
- Real session durations using timestamps
- Accurate prompt counts excluding system messages
- Model-specific usage by analyzing assistant responses
- Account-wide totals across all projects

Uses color coding (green/yellow/red) to warn when approaching limits.