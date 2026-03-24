"""Transparent overlay window with animated sprite."""
import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush


class SpriteOverlay(QWidget):
    """Transparent, click-through overlay with animated guiding sprite."""

    def __init__(self):
        super().__init__()
        self.sprite_pos = QPoint(100, 100)
        self.target_pos = QPoint(100, 100)
        self.animation = None
        self.setup_window()

    def setup_window(self):
        """Configure transparent, click-through overlay."""
        # Make window frameless and stay on top
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )

        # Make window transparent and click-through
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        # Fullscreen
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

    def get_sprite_pos(self):
        """Get current sprite position (for animation)."""
        return self.sprite_pos

    def set_sprite_pos(self, pos):
        """Set sprite position and trigger repaint."""
        self.sprite_pos = pos
        self.update()

    # Property for smooth animation
    sprite_position = pyqtProperty(QPoint, fget=get_sprite_pos, fset=set_sprite_pos)

    def move_sprite_to(self, x, y, duration=1000):
        """Animate sprite to target coordinates.

        Args:
            x: Target X coordinate
            y: Target Y coordinate
            duration: Animation duration in milliseconds
        """
        self.target_pos = QPoint(x, y)

        # Stop existing animation if any
        if self.animation:
            self.animation.stop()

        # Create smooth animation
        self.animation = QPropertyAnimation(self, b"sprite_position")
        self.animation.setDuration(duration)
        self.animation.setStartValue(self.sprite_pos)
        self.animation.setEndValue(self.target_pos)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.start()

    def paintEvent(self, event):
        """Draw the guiding sprite."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw glowing sprite (circle with glow effect)
        x, y = self.sprite_pos.x(), self.sprite_pos.y()

        # Outer glow
        for i in range(3, 0, -1):
            alpha = 50 * (4 - i)
            color = QColor(100, 200, 255, alpha)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(x - 15 * i, y - 15 * i, 30 * i, 30 * i)

        # Inner sprite
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QBrush(QColor(100, 200, 255, 200)))
        painter.drawEllipse(x - 12, y - 12, 24, 24)

        # Center dot
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(x - 4, y - 4, 8, 8)


def test_overlay():
    """Test the overlay with sample animation."""
    app = QApplication(sys.argv)
    overlay = SpriteOverlay()
    overlay.show()

    # Test animation after 1 second
    QTimer.singleShot(1000, lambda: overlay.move_sprite_to(500, 500))
    QTimer.singleShot(3000, lambda: overlay.move_sprite_to(1000, 300))
    QTimer.singleShot(5000, lambda: overlay.move_sprite_to(200, 700))

    sys.exit(app.exec_())


if __name__ == "__main__":
    test_overlay()
