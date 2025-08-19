#!/usr/bin/env python3
"""
Git information module for Claude Code status line integration.
Provides git branch, status, and sync information with caching for performance.
"""

import subprocess
import time
import os
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass


@dataclass
class GitStatus:
    """Git repository status information."""
    is_git_repo: bool = False
    branch_name: Optional[str] = None
    ahead_count: int = 0
    behind_count: int = 0
    has_modified: bool = False
    has_untracked: bool = False
    has_staged: bool = False
    error: Optional[str] = None


class GitInfo:
    """Git information provider with caching for performance."""
    
    def __init__(self, cache_duration: int = 5):
        """Initialize GitInfo with cache duration in seconds."""
        self.cache_duration = cache_duration
        self._cache: Dict[str, Any] = {}
        self._cache_time: Dict[str, float] = {}
    
    def get_git_status(self, directory: Optional[str] = None) -> GitStatus:
        """
        Get comprehensive git status for the given directory.
        
        Args:
            directory: Directory to check (defaults to current directory)
            
        Returns:
            GitStatus object with all git information
        """
        directory = directory or os.getcwd()
        cache_key = f"git_status:{directory}"
        
        # Check cache
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        # Get fresh git status
        status = self._fetch_git_status(directory)
        
        # Cache result
        self._cache[cache_key] = status
        self._cache_time[cache_key] = time.time()
        
        return status
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid."""
        if cache_key not in self._cache:
            return False
        
        cache_age = time.time() - self._cache_time.get(cache_key, 0)
        return cache_age < self.cache_duration
    
    def _fetch_git_status(self, directory: str) -> GitStatus:
        """Fetch fresh git status information."""
        status = GitStatus()
        
        try:
            # Check if directory is a git repository
            result = self._run_git_command(
                ["git", "rev-parse", "--is-inside-work-tree"], 
                directory
            )
            
            if result is None or result.strip() != "true":
                return status  # Not a git repo
            
            status.is_git_repo = True
            
            # Get current branch name
            status.branch_name = self._get_branch_name(directory)
            
            # Get working tree status
            self._update_working_tree_status(status, directory)
            
            # Get ahead/behind count (only if we have a branch and remote)
            if status.branch_name:
                self._update_remote_status(status, directory)
                
        except Exception as e:
            status.error = str(e)
        
        return status
    
    def _run_git_command(self, cmd: list, directory: str, timeout: int = 3) -> Optional[str]:
        """
        Run a git command safely with timeout.
        
        Args:
            cmd: Git command as list
            directory: Working directory
            timeout: Command timeout in seconds
            
        Returns:
            Command output as string, or None if failed
        """
        try:
            result = subprocess.run(
                cmd,
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        return None
    
    def _get_branch_name(self, directory: str) -> Optional[str]:
        """Get current branch name."""
        # Try git symbolic-ref first (works for normal branches)
        branch = self._run_git_command(
            ["git", "symbolic-ref", "--short", "HEAD"], 
            directory
        )
        
        if branch:
            return branch
        
        # Fallback for detached HEAD - get commit hash
        commit = self._run_git_command(
            ["git", "rev-parse", "--short", "HEAD"], 
            directory
        )
        
        if commit:
            return f"({commit})"  # Indicate detached HEAD
        
        return None
    
    def _update_working_tree_status(self, status: GitStatus, directory: str) -> None:
        """Update working tree status (modified, untracked, staged files)."""
        output = self._run_git_command(
            ["git", "status", "--porcelain=v1"], 
            directory
        )
        
        if output is None:
            return
        
        for line in output.split('\n'):
            if not line:
                continue
            
            # Git status porcelain format: XY filename
            # X = staged status, Y = working tree status
            if len(line) >= 2:
                staged_status = line[0]
                working_status = line[1]
                
                # Check for staged changes
                if staged_status != ' ' and staged_status != '?':
                    status.has_staged = True
                
                # Check for working tree changes
                if working_status != ' ':
                    if working_status == '?':
                        status.has_untracked = True
                    else:
                        status.has_modified = True
    
    def _update_remote_status(self, status: GitStatus, directory: str) -> None:
        """Update ahead/behind count vs remote tracking branch."""
        if not status.branch_name or status.branch_name.startswith('('):
            return  # Skip for detached HEAD
        
        # Get ahead/behind count
        output = self._run_git_command([
            "git", "rev-list", "--left-right", "--count", 
            f"@{{upstream}}...HEAD"
        ], directory)
        
        if output:
            try:
                parts = output.split()
                if len(parts) == 2:
                    status.behind_count = int(parts[0])
                    status.ahead_count = int(parts[1])
            except (ValueError, IndexError):
                pass
    
    def format_git_info(self, status: GitStatus, max_branch_length: int = 20) -> str:
        """
        Format git status into a compact string for status line.
        
        Args:
            status: GitStatus object
            max_branch_length: Maximum branch name length before truncation
            
        Returns:
            Formatted git info string with colors
        """
        if not status.is_git_repo or not status.branch_name:
            return ""
        
        # Truncate long branch names
        branch_name = status.branch_name
        if len(branch_name) > max_branch_length:
            branch_name = branch_name[:max_branch_length-3] + "..."
        
        # Build status indicators
        indicators = []
        
        # Ahead/behind indicators
        if status.ahead_count > 0:
            indicators.append(f"↑{status.ahead_count}")
        if status.behind_count > 0:
            indicators.append(f"↓{status.behind_count}")
        
        # Working tree status
        if status.has_staged or status.has_modified:
            indicators.append("*")
        if status.has_untracked:
            indicators.append("?")
        
        # Combine branch name with indicators
        status_text = branch_name + "".join(indicators)
        
        # Determine color based on status
        color = self._get_git_color(status)
        
        # Format with color
        return f"\033[38;2;{color[0]};{color[1]};{color[2]}m🌿 {status_text}\033[0m"
    
    def _get_git_color(self, status: GitStatus) -> Tuple[int, int, int]:
        """
        Get RGB color for git status.
        
        Returns:
            RGB tuple (r, g, b)
        """
        # Red for errors
        if status.error:
            return (255, 100, 100)
        
        # Yellow for dirty working tree
        if status.has_modified or status.has_untracked or status.has_staged:
            return (255, 215, 0)
        
        # Blue for ahead of remote
        if status.ahead_count > 0:
            return (100, 150, 255)
        
        # Orange for behind remote
        if status.behind_count > 0:
            return (255, 165, 0)
        
        # Green for clean and up-to-date
        return (0, 255, 0)