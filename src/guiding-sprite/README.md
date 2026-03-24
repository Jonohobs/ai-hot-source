# Invoke Guiding Sprite

AI-powered screen overlay that guides your cursor to UI elements using natural language.

## How It Works

1. **You describe** what you're looking for: "the save button", "the login field", etc.
2. **AI Vision** (Claude, GPT-4, or Gemini) analyzes your screen and finds the coordinates
3. **Animated sprite** smoothly guides you to the element

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set one of these API keys (any will work):

# Option 1: Claude (preferred)
export ANTHROPIC_API_KEY="your-api-key-here"  # Linux/Mac
set ANTHROPIC_API_KEY=your-api-key-here       # Windows CMD
$env:ANTHROPIC_API_KEY="your-api-key-here"    # Windows PowerShell

# Option 2: OpenAI GPT-4 Vision
export OPENAI_API_KEY="your-api-key-here"
set OPENAI_API_KEY=your-api-key-here
$env:OPENAI_API_KEY="your-api-key-here"

# Option 3: Gemini Vision
export GEMINI_API_KEY="your-api-key-here"
set GEMINI_API_KEY=your-api-key-here
$env:GEMINI_API_KEY="your-api-key-here"
```

## Usage

```bash
# Guide to an element (uses golden orb by default)
python sprite_guide.py "the save button"
python sprite_guide.py "the search bar"
python sprite_guide.py "the red X button in the top right"

# Use a different visual style
python sprite_guide.py "the file menu" cyan_sharp
python sprite_guide.py "the login button" purple_rings
```

## Available Styles

- **gemini_golden** (default) - Golden radial gradient with pulse + bounce
- **blue_glow** - Blue concentric rings with smooth animation
- **hybrid_pulse** - Blue gradient with pulsing effect
- **emerald_soft** - Soft green glow with gentle pulse
- **purple_rings** - Purple energy rings with elastic bounce
- **red_alert** - Urgent red with aggressive bounce
- **cyan_sharp** - Bright cyan, fast & focused

## Test Visuals

```bash
# See all 7 styles cycle through (42 seconds)
python overlay_styled.py

# Test a specific style
python overlay_styled.py gemini_golden
python overlay_styled.py purple_rings

# Test original blue glow (archived version)
python archive/overlay_v1_blue_glow.py
```

## Architecture

```
sprite_guide.py  → Main app (CLI, screen capture, orchestration)
overlay.py       → PyQt5 transparent overlay with animated sprite
requirements.txt → Dependencies
```

## Features

- **Transparent overlay**: Click-through, stays on top
- **Smooth animation**: 1 second ease-in-out movement
- **Glowing sprite**: Visible against any background
- **Natural language**: Describe elements however you want

## Troubleshooting

**Sprite doesn't appear:**
- Check that PyQt5 is installed correctly
- Try running `python overlay.py` to test without AI

**"Element not found" error:**
- Make description more specific
- Ensure the element is visible on screen
- Try different wording

**API errors:**
- Verify one of these is set: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or `GEMINI_API_KEY`
- Check your API quota (Anthropic Console, OpenAI Dashboard, or Google AI Studio)
- Ensure you have vision API access enabled for your key

## Next Steps (Future Enhancements)

- [ ] Hotkey to invoke sprite (Win+G or similar)
- [ ] Voice command support
- [ ] Screenshot cleanup logic
- [ ] Multiple sprite styles
- [ ] Persistent sprite for step-by-step guides
