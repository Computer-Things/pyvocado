#!/usr/bin/env python3
"""
CLI interface for the clipboard history tool.
"""

import argparse
import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import Optional
from clipboard_history import ClipboardHistory


def format_entry(entry: dict, index: int, show_index: bool = True) -> str:
    """Format a history entry for display."""
    date_str = entry.get('date', 'Unknown')
    time_str = entry.get('time', 'Unknown')
    content = entry.get('content', '')
    
    # Truncate long content for list view
    preview = content[:100] + '...' if len(content) > 100 else content
    preview = preview.replace('\n', '\\n')
    
    if show_index:
        return f"[{index}] {date_str} {time_str} - {preview}"
    else:
        return f"{date_str} {time_str} - {preview}"


def list_history(args):
    """List clipboard history."""
    history = ClipboardHistory(args.history_file)
    entries = history.get_history(limit=args.limit)
    
    if not entries:
        print("No clipboard history found.")
        return
    
    print(f"\nClipboard History ({len(entries)} entries):\n")
    for i, entry in enumerate(entries):
        print(format_entry(entry, i))


def search_history(args):
    """Search clipboard history."""
    history = ClipboardHistory(args.history_file)
    results = history.search_history(args.query, limit=args.limit)
    
    if not results:
        print(f"No entries found matching '{args.query}'.")
        return
    
    print(f"\nFound {len(results)} matching entries:\n")
    for i, entry in enumerate(results):
        # Find original index
        original_index = history.history.index(entry)
        print(format_entry(entry, original_index))


def show_entry(args):
    """Show full content of a specific entry."""
    history = ClipboardHistory(args.history_file)
    entry = history.get_entry_by_index(args.index)
    
    if not entry:
        print(f"Error: Entry at index {args.index} not found.")
        sys.exit(1)
    
    print(f"\nEntry [{args.index}]:")
    print(f"Date: {entry.get('date', 'Unknown')} {entry.get('time', 'Unknown')}")
    print(f"Timestamp: {entry.get('timestamp', 'Unknown')}")
    print(f"\nContent:\n{entry.get('content', '')}")


def copy_entry(args):
    """Copy an entry from history to clipboard."""
    history = ClipboardHistory(args.history_file)
    
    if history.copy_from_history(args.index):
        entry = history.get_entry_by_index(args.index)
        preview = entry['content'][:50] + '...' if len(entry['content']) > 50 else entry['content']
        print(f"Copied entry [{args.index}] to clipboard: {preview}")
    else:
        print(f"Error: Could not copy entry at index {args.index}.")
        sys.exit(1)


def clear_history(args):
    """Clear all clipboard history."""
    if not args.force:
        response = input("Are you sure you want to clear all history? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return
    
    history = ClipboardHistory(args.history_file)
    history.clear_history()
    print("History cleared.")


def remove_entry(args):
    """Remove a specific entry from history."""
    history = ClipboardHistory(args.history_file)
    
    if history.remove_entry(args.index):
        print(f"Removed entry at index {args.index}.")
    else:
        print(f"Error: Entry at index {args.index} not found.")
        sys.exit(1)


def get_pid_file(history_file: Optional[str] = None) -> Path:
    """Get the path to the PID file."""
    if history_file:
        history_path = Path(history_file)
        pid_file = history_path.parent / ".clipboard_monitor.pid"
    else:
        home = Path.home()
        pid_file = home / ".clipboard_monitor.pid"
    return pid_file


def is_process_running(pid: int) -> bool:
    """Check if a process with the given PID is running."""
    try:
        os.kill(pid, 0)  # Signal 0 doesn't kill, just checks if process exists
        return True
    except OSError:
        return False


def start_background(args):
    """Start monitoring clipboard in the background."""
    pid_file = get_pid_file(args.history_file)
    
    # Check if already running
    if pid_file.exists():
        try:
            with open(pid_file, 'r') as f:
                old_pid = int(f.read().strip())
            if is_process_running(old_pid):
                print(f"Monitor is already running (PID: {old_pid})")
                return
            else:
                # Stale PID file, remove it
                pid_file.unlink()
        except (ValueError, IOError):
            # Invalid PID file, remove it
            pid_file.unlink()
    
    # Get the script path
    script_path = Path(__file__).resolve()
    
    # Build command
    cmd = [sys.executable, str(script_path), 'monitor', '--interval', str(args.interval)]
    if args.history_file:
        cmd.extend(['--history-file', args.history_file])
    
    # Start process in background
    try:
        if sys.platform == 'win32':
            # Windows: use CREATE_NO_WINDOW flag if available
            kwargs = {
                'stdout': subprocess.DEVNULL,
                'stderr': subprocess.DEVNULL,
            }
            if hasattr(subprocess, 'CREATE_NO_WINDOW'):
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
            process = subprocess.Popen(cmd, **kwargs)
        else:
            # Unix: detach from terminal
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
        
        # Save PID
        with open(pid_file, 'w') as f:
            f.write(str(process.pid))
        
        print(f"Started clipboard monitor in background (PID: {process.pid})")
        print(f"PID file: {pid_file}")
    except Exception as e:
        print(f"Error starting background process: {e}", file=sys.stderr)
        sys.exit(1)


def stop_background(args):
    """Stop the background monitoring process."""
    pid_file = get_pid_file(args.history_file)
    
    if not pid_file.exists():
        print("No background monitor process found (PID file does not exist).")
        return
    
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        if not is_process_running(pid):
            print(f"Process {pid} is not running. Removing stale PID file.")
            pid_file.unlink()
            return
        
        # Try to kill the process gracefully
        try:
            import time
            # Send termination signal
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.5)
            
            # Check if still running
            if is_process_running(pid):
                # Force kill if still running (Unix only)
                if sys.platform != 'win32':
                    os.kill(pid, signal.SIGKILL)
                else:
                    # On Windows, try taskkill as fallback
                    try:
                        subprocess.run(['taskkill', '/F', '/PID', str(pid)], 
                                      stdout=subprocess.DEVNULL, 
                                      stderr=subprocess.DEVNULL,
                                      check=False)
                    except FileNotFoundError:
                        # taskkill not available, just try SIGTERM again
                        os.kill(pid, signal.SIGTERM)
                print(f"Forcefully killed process {pid}")
            else:
                print(f"Stopped clipboard monitor (PID: {pid})")
        except ProcessLookupError:
            print(f"Process {pid} not found.")
        except PermissionError:
            print(f"Permission denied: Cannot kill process {pid}")
            sys.exit(1)
        
        # Remove PID file
        pid_file.unlink()
        
    except (ValueError, IOError) as e:
        print(f"Error reading PID file: {e}", file=sys.stderr)
        print("Removing invalid PID file.")
        pid_file.unlink()
        sys.exit(1)


def monitor_clipboard(args):
    """Start monitoring clipboard for changes."""
    history = ClipboardHistory(args.history_file)
    history.monitor(interval=args.interval)


def main():
    parser = argparse.ArgumentParser(
        description='Clipboard History Tool - Store and manage clipboard history with timestamps',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list                    # List all history
  %(prog)s list --limit 10         # List last 10 entries
  %(prog)s search "python"         # Search for entries containing "python"
  %(prog)s show 0                  # Show full content of entry 0
  %(prog)s copy 0                  # Copy entry 0 to clipboard
  %(prog)s monitor                 # Start monitoring clipboard (foreground)
  %(prog)s start                   # Start monitoring clipboard (background)
  %(prog)s stop                    # Stop background monitor
  %(prog)s clear                   # Clear all history
        """
    )
    
    parser.add_argument(
        '--history-file',
        help='Path to history file (default: ~/.clipboard_history.json)',
        default=None
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List clipboard history')
    list_parser.add_argument('--limit', type=int, help='Limit number of entries to show')
    list_parser.set_defaults(func=list_history)
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search clipboard history')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--limit', type=int, help='Limit number of results')
    search_parser.set_defaults(func=search_history)
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show full content of an entry')
    show_parser.add_argument('index', type=int, help='Index of the entry')
    show_parser.set_defaults(func=show_entry)
    
    # Copy command
    copy_parser = subparsers.add_parser('copy', help='Copy an entry to clipboard')
    copy_parser.add_argument('index', type=int, help='Index of the entry to copy')
    copy_parser.set_defaults(func=copy_entry)
    
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear all history')
    clear_parser.add_argument('--force', action='store_true', help='Skip confirmation')
    clear_parser.set_defaults(func=clear_history)
    
    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a specific entry')
    remove_parser.add_argument('index', type=int, help='Index of the entry to remove')
    remove_parser.set_defaults(func=remove_entry)
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor clipboard for changes')
    monitor_parser.add_argument(
        '--interval',
        type=float,
        default=0.5,
        help='Polling interval in seconds (default: 0.5)'
    )
    monitor_parser.set_defaults(func=monitor_clipboard)
    
    # Start command (background)
    start_parser = subparsers.add_parser('start', help='Start monitoring clipboard in background')
    start_parser.add_argument(
        '--interval',
        type=float,
        default=0.5,
        help='Polling interval in seconds (default: 0.5)'
    )
    start_parser.set_defaults(func=start_background)
    
    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop background clipboard monitor')
    stop_parser.set_defaults(func=stop_background)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == '__main__':
    main()
