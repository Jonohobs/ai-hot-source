# Voice — Push to Talk Setup

Talk to your AI instead of typing. A background Python daemon listens for a hotkey (e.g. Ctrl+Alt hold-to-record), captures mic audio, transcribes via Groq's Whisper API (~1 second), and types the result into your active window.

## How It Works

1. **Daemon** runs silently on startup (VBS/systemd launcher, singleton lock)
2. **Hold hotkey** to record, release to stop
3. **Silence gate** skips empty clips (RMS threshold)
4. **Groq Whisper** transcribes (free tier, 240x real-time speed)
5. **Text injected** at cursor position in whatever app is focused
6. **Corrections dictionary** fixes words it always gets wrong

## Dependencies

```bash
pip install groq pyaudiowpatch pynput keyboard numpy python-dotenv
```

Set your `GROQ_API_KEY` in `.env` or environment. No ffmpeg needed — `pyaudiowpatch` captures audio directly.

## Auto-Start on Login

- **Windows:** VBS script in `Shell:Startup` that runs `pythonw.exe voice-daemon.py` (hidden, no console window)
- **Linux/Mac:** systemd user service or launchd plist

## Offline Alternative

`whisper.cpp` with Vulkan — slightly slower but zero API calls.
