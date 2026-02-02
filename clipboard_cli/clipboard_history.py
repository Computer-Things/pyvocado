#!/usr/bin/env python3
"""
Clipboard History Tool
A tool that monitors and stores clipboard history with timestamps.
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import pyperclip


class ClipboardHistory:
    """Manages clipboard history with timestamps."""
    
    def __init__(self, history_file: Optional[str] = None):
        """
        Initialize the clipboard history manager.
        
        Args:
            history_file: Path to the JSON file storing history. 
                         Defaults to ~/.clipboard_history.json
        """
        if history_file is None:
            home = Path.home()
            history_file = str(home / ".clipboard_history.json")
        
        self.history_file = Path(history_file)
        self.history: List[Dict[str, str]] = []
        self.last_clipboard_content = None
        self.load_history()
    
    def load_history(self) -> None:
        """Load history from the JSON file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading history: {e}", file=sys.stderr)
                self.history = []
        else:
            self.history = []
    
    def save_history(self) -> None:
        """Save history to the JSON file."""
        try:
            # Create directory if it doesn't exist
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving history: {e}", file=sys.stderr)
    
    def add_entry(self, content: str) -> None:
        """
        Add a new entry to the history.
        
        Args:
            content: The clipboard content to add.
        """
        if not content or content == self.last_clipboard_content:
            return
        
        # Remove duplicates (if the same content exists, remove old entry)
        self.history = [entry for entry in self.history if entry['content'] != content]
        
        # Add new entry at the beginning
        entry = {
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M:%S')
        }
        self.history.insert(0, entry)
        
        # Limit history size (keep last 1000 entries)
        if len(self.history) > 1000:
            self.history = self.history[:1000]
        
        self.last_clipboard_content = content
        self.save_history()
    
    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Get clipboard history.
        
        Args:
            limit: Maximum number of entries to return.
        
        Returns:
            List of history entries.
        """
        if limit:
            return self.history[:limit]
        return self.history
    
    def search_history(self, query: str, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Search history by content.
        
        Args:
            query: Search query (case-insensitive).
            limit: Maximum number of results to return.
        
        Returns:
            List of matching history entries.
        """
        query_lower = query.lower()
        results = [
            entry for entry in self.history
            if query_lower in entry['content'].lower()
        ]
        
        if limit:
            return results[:limit]
        return results
    
    def get_entry_by_index(self, index: int) -> Optional[Dict[str, str]]:
        """
        Get a specific entry by its index.
        
        Args:
            index: Index of the entry (0-based).
        
        Returns:
            History entry or None if index is invalid.
        """
        if 0 <= index < len(self.history):
            return self.history[index]
        return None
    
    def clear_history(self) -> None:
        """Clear all history."""
        self.history = []
        self.save_history()
    
    def remove_entry(self, index: int) -> bool:
        """
        Remove an entry by index.
        
        Args:
            index: Index of the entry to remove.
        
        Returns:
            True if entry was removed, False otherwise.
        """
        if 0 <= index < len(self.history):
            self.history.pop(index)
            self.save_history()
            return True
        return False
    
    def monitor(self, interval: float = 0.5) -> None:
        """
        Monitor clipboard for changes.
        
        Args:
            interval: Polling interval in seconds.
        """
        print(f"Monitoring clipboard (press Ctrl+C to stop)...")
        print(f"History file: {self.history_file}")
        
        try:
            while True:
                try:
                    current_content = pyperclip.paste()
                    if current_content:
                        self.add_entry(current_content)
                except Exception as e:
                    print(f"Error reading clipboard: {e}", file=sys.stderr)
                
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nStopped monitoring clipboard.")
    
    def copy_from_history(self, index: int) -> bool:
        """
        Copy an entry from history to clipboard.
        
        Args:
            index: Index of the entry to copy.
        
        Returns:
            True if entry was copied, False otherwise.
        """
        entry = self.get_entry_by_index(index)
        if entry:
            try:
                pyperclip.copy(entry['content'])
                return True
            except Exception as e:
                print(f"Error copying to clipboard: {e}", file=sys.stderr)
        return False
