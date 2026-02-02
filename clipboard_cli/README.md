# pyvocado

A Python clipboard history tool that stores your clipboard history with timestamps.

## Features

- 📋 Monitor clipboard changes automatically
- 📅 Store clipboard history with dates and timestamps
- 🔍 Search through clipboard history
- 📝 View full history or specific entries
- 📤 Copy any previous entry back to clipboard
- 🗑️ Remove specific entries or clear all history
- 💾 Persistent storage in JSON format

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make the CLI executable (optional):
```bash
chmod +x clipboard_cli.py
```

## Usage

### Monitor Clipboard

#### Foreground Monitoring

Start monitoring your clipboard for changes in the foreground:
```bash
python clipboard_cli.py monitor
```

This will continuously monitor your clipboard and save new entries. Press `Ctrl+C` to stop.

#### Background Monitoring

Start monitoring in the background (recommended for continuous use):
```bash
python clipboard_cli.py start
```

This will start the monitor as a background process. The process will continue running even after you close the terminal.

Stop the background monitor:
```bash
python clipboard_cli.py stop
```

You can also specify a custom polling interval:
```bash
python clipboard_cli.py start --interval 1.0
```

### List History

View all clipboard history:
```bash
python clipboard_cli.py list
```

View last 10 entries:
```bash
python clipboard_cli.py list --limit 10
```

### Search History

Search for entries containing a specific term:
```bash
python clipboard_cli.py search "python"
```

### Show Entry Details

View full content of a specific entry:
```bash
python clipboard_cli.py show 0
```

### Copy from History

Copy a previous entry back to clipboard:
```bash
python clipboard_cli.py copy 0
```

### Remove Entry

Remove a specific entry:
```bash
python clipboard_cli.py remove 0
```

### Clear All History

Clear all clipboard history:
```bash
python clipboard_cli.py clear
```

Force clear without confirmation:
```bash
python clipboard_cli.py clear --force
```

## History Storage

By default, history is stored in `~/.clipboard_history.json`. You can specify a custom location:

```bash
python clipboard_cli.py --history-file /path/to/history.json list
```

## Example Workflow

1. Start monitoring in the background:
   ```bash
   python clipboard_cli.py start
   ```

2. Use your computer normally - all clipboard changes will be saved automatically.

3. In another terminal, view your history:
   ```bash
   python clipboard_cli.py list
   ```

4. Search for something you copied earlier:
   ```bash
   python clipboard_cli.py search "important"
   ```

5. Copy a previous entry back:
   ```bash
   python clipboard_cli.py copy 5
   ```

## History Format

Each entry in the history contains:
- `content`: The clipboard text
- `timestamp`: ISO format timestamp
- `date`: Date in YYYY-MM-DD format
- `time`: Time in HH:MM:SS format

## Notes

- History is limited to 1000 entries (most recent are kept)
- Duplicate consecutive entries are automatically filtered
- The tool works on macOS, Linux, and Windows
- Background monitor PID is stored in `~/.clipboard_monitor.pid`
- If the background process crashes, you may need to manually remove the PID file