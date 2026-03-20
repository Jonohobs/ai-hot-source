# Clawd's Claws — Screen Pointer Overlay

A pixel art claw in Claude orange that slides out from the screen edge, grabs at whatever you point it at, and talks to you through a speech bubble. Think of it as your AI's physical hand reaching into your screen.

```
                                ████████   <- top prong
                                █
|═══════════════════════════════█          <- arm extends from screen edge
                                █
                                ████████   <- bottom prong
```

## What It Does

- Transparent, always-on-top, click-through overlay (Python/tkinter)
- Claw extends from left or right edge toward any (x, y) coordinate
- Auto-detects which side to come from based on target position
- Smooth ease-out animation with a pulsing white dot at the prong tips
- Speech bubble anchored at the screen edge — the speaker talks from off-screen
- Polls `instruction.json` — update the file, claw repoints

## How to Use It

```bash
# Demo mode
python overlay.py --demo

# Normal mode — watches instruction.json for targets
python overlay.py

# Point at something from another terminal
python point.py 600 400 "Click 'Projects'"
python point.py 1200 300 "Open this menu" right
python point.py hide
```

## Hook It Up to Your Browser

The real play: your AI reads a screenshot, identifies where the user should click, writes `instruction.json`, and the claw points at it. Step-by-step guided walkthroughs with a physical pointer.

```
instruction.json  <-  Your AI writes this (or point.py for testing)
       |
   overlay.py     <-  Polls JSON every 250ms, animates claw to target
```

Press Escape to quit.

## Pixel Art Toolkit

Also in the box: a set of Python scripts for generating and rendering pixel art sprites in the terminal. Define characters as simple text grids, map letters to colours, render as PNGs, ANSI terminal art, or HTML previews.

- `make_clawd.py` — char grid -> scaled PNG (PIL)
- `print_sprite.py` — ANSI half-block renderer (one terminal char = two pixels, zero deps)
- `preview.py` — char grid -> HTML table with coloured cells
- `terminal_preview.py` — ANSI art -> self-contained HTML page
- `analyze_sprite.py` — reverse-engineer sprites from screenshots

**Note:** These are rough. Some parts are unfinished or buggy. The intent is to give you something concrete to improve with your AI.

**Try it:** Tell your AI "Here's a pixel art toolkit with some bugs. Help me get it working and make a new sprite."
