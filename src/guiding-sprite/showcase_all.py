"""Display all 7 sprite styles simultaneously for comparison."""
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from overlay_styled import StyledSpriteOverlay
from sprite_styles import STYLES


def showcase_all_styles():
    """Show all 7 styles at once in a grid layout."""
    app = QApplication(sys.argv)

    # Get screen dimensions
    screen = QApplication.primaryScreen().geometry()
    width, height = screen.width(), screen.height()

    # Calculate grid positions (3x3 grid, using 7 of 9 spots)
    # Grid: 25%, 50%, 75% horizontal and vertical
    positions = [
        (int(width * 0.25), int(height * 0.25)),  # Top-left
        (int(width * 0.50), int(height * 0.25)),  # Top-center
        (int(width * 0.75), int(height * 0.25)),  # Top-right
        (int(width * 0.25), int(height * 0.50)),  # Middle-left
        (int(width * 0.50), int(height * 0.50)),  # Middle-center
        (int(width * 0.75), int(height * 0.50)),  # Middle-right
        (int(width * 0.50), int(height * 0.75)),  # Bottom-center
    ]

    # Create overlays for each style
    overlays = []
    style_names = list(STYLES.keys())

    for i, style_name in enumerate(style_names):
        overlay = StyledSpriteOverlay(style_name)
        overlay.show()
        overlays.append(overlay)

        # Position sprite at grid location
        x, y = positions[i]
        print(f"> {STYLES[style_name]['name']}: ({x}, {y})")

        # Delay each sprite's movement slightly for visual effect
        QTimer.singleShot(100 * i, lambda x=x, y=y, o=overlay: o.move_sprite_to(x, y))

    print(f"\nDisplaying all {len(overlays)} styles simultaneously")
    print("Press Ctrl+C in terminal to exit")

    sys.exit(app.exec_())


if __name__ == "__main__":
    showcase_all_styles()
