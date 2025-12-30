#!/usr/bin/env python3
"""
Installation script for Claude Code Usage Tracker.
Integrates with Claude Code's settings and sets up the tracker.
"""

import json
import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

# Fix Windows encoding issue
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def check_dependencies():
    """Check and install required dependencies."""
    print("Checking dependencies...")
    
    # Check for uv
    if shutil.which('uv') is None:
        print("\n❌ 'uv' is not installed.")
        print("Please install uv first: https://github.com/astral-sh/uv")
        print("Quick install: curl -LsSf https://astral.sh/uv/install.sh | sh")
        return False
    
    # Check for Python
    if sys.version_info < (3, 8):
        print("\n❌ Python 3.8+ is required.")
        return False
    
    print("✓ All system dependencies found")
    return True

def setup_virtual_env():
    """Set up virtual environment and install packages."""
    print("\nSetting up Python environment...")

    # Skip if we're already running in a virtual environment
    # (happens when user runs: uv run python install.py)
    if os.environ.get('VIRTUAL_ENV'):
        print("✓ Already running in virtual environment, skipping creation")
        # Still try to sync dependencies
        project_dir = Path(__file__).parent
        print("Syncing dependencies...")
        result = subprocess.run(
            ['uv', 'sync'],
            cwd=project_dir,
            capture_output=True,
            encoding='utf-8',
            errors='replace'
        )
        if result.returncode == 0:
            print("✓ Dependencies synced")
            return True
        # Non-fatal if sync fails
        return True

    project_dir = Path(__file__).parent

    # Create virtual environment using uv
    print("Creating virtual environment...")
    result = subprocess.run(
        ['uv', 'venv', '--clear'],
        cwd=project_dir,
        capture_output=True,
        encoding='utf-8',
        errors='replace'
    )
    if result.returncode != 0:
        print(f"❌ Failed to create virtual environment: {result.stderr}")
        return False

    # Install numpy using uv
    print("Installing numpy...")
    result = subprocess.run(
        ['uv', 'pip', 'install', 'numpy'],
        cwd=project_dir,
        capture_output=True,
        encoding='utf-8',
        errors='replace'
    )
    if result.returncode != 0:
        print(f"❌ Failed to install numpy: {result.stderr}")
        return False

    print("✓ Python environment configured")
    return True

def integrate_with_claude():
    """Integrate tracker with Claude Code settings."""
    print("\nIntegrating with Claude Code...")
    
    claude_settings = Path.home() / ".claude" / "settings.json"
    project_dir = Path(__file__).parent.resolve()
    
    # Create backup
    if claude_settings.exists():
        backup_path = claude_settings.with_suffix('.json.backup')
        print(f"Creating backup: {backup_path}")
        shutil.copy2(claude_settings, backup_path)
        
        with open(claude_settings, 'r') as f:
            settings = json.load(f)
    else:
        settings = {}
    
    # Update status line settings - use uv run to ensure proper environment
    settings['statusLine'] = {
        'type': 'command',
        'command': f'cd {project_dir} && uv run python status_line.py'
    }
    
    # Save updated settings
    claude_settings.parent.mkdir(exist_ok=True)
    with open(claude_settings, 'w') as f:
        json.dump(settings, f, indent=2)
    
    print("✓ Claude Code settings updated")
    return True

def configure_subscription():
    """Configure subscription tier."""
    print("\n⚠️  Skipping interactive configuration...")
    print("    Please run: uv run python configure.py")
    print("    to select your subscription tier.")
    return True  # Return True to continue installation

def test_installation():
    """Test the installation."""
    print("\nTesting installation...")

    project_dir = Path(__file__).parent

    # Determine Python executable
    if sys.platform == "win32":
        python_cmd = project_dir / ".venv" / "Scripts" / "python.exe"
    else:
        python_cmd = project_dir / ".venv" / "bin" / "python"

    # Test status line generation
    test_input = json.dumps({"projectPath": str(project_dir)})

    result = subprocess.run(
        [str(python_cmd), str(project_dir / 'status_line.py')],
        input=test_input,
        capture_output=True,
        encoding='utf-8',
        errors='replace'
    )

    if result.returncode == 0 and result.stdout:
        print("✓ Status line test successful")
        print(f"Sample output: {result.stdout.strip()}")
        return True
    else:
        print("❌ Status line test failed")
        if result.stderr:
            print(f"Error: {result.stderr}")
        return False

def main():
    """Main installation process."""
    print("=" * 60)
    print("Claude Code Usage Tracker - Python Installation")
    print("=" * 60)
    
    # Check if running with --test flag
    test_mode = '--test' in sys.argv
    
    if test_mode:
        print("\n🔍 Running in TEST MODE - no changes will be made")
    
    # Step 1: Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Step 2: Setup virtual environment
    if not test_mode:
        if not setup_virtual_env():
            sys.exit(1)
    
    # Step 3: Configure subscription
    if not test_mode:
        if not configure_subscription():
            print("\n⚠️  Subscription configuration skipped")
    
    # Step 4: Integrate with Claude
    if not test_mode:
        if not integrate_with_claude():
            sys.exit(1)
    
    # Step 5: Test installation
    if not test_mode:
        if not test_installation():
            print("\n⚠️  Test failed but installation may still work")
    
    print("\n" + "=" * 60)
    print("✅ Installation complete!")
    print("\nThe tracker is now integrated with Claude Code.")
    print("Your usage will be displayed in the status line.")
    print("\n⚠️  IMPORTANT: Configure your subscription tier:")
    print("  uv run python configure.py")
    print("\nTo reconfigure later, run:")
    print("  uv run python configure.py")
    print("=" * 60)

if __name__ == "__main__":
    main()