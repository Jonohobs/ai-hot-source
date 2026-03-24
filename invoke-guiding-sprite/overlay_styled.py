"""Flexible styled overlay - supports multiple visual styles."""
import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient
from sprite_styles import STYLES


class StyledSpriteOverlay(QWidget):
    """Transparent overlay with configurable sprite styles."""

    def __init__(self, style_name="gemini_golden"):
        super().__init__()
        self.set_style(style_name)
        self.sprite_pos = QPoint(100, 100)
        self.target_pos = QPoint(100, 100)
        self.animation = None

        # Pulse animation state
        self.pulse_value = 0
        self.pulse_growing = True
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self._pulse_tick)

        self.setup_window()

    def set_style(self, style_name):
        """Apply a visual style from sprite_styles.py"""
        self.style = STYLES.get(style_name, STYLES["gemini_golden"])

    def setup_window(self):
        """Configure transparent, click-through overlay."""
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

    def get_sprite_pos(self):
        return self.sprite_pos

    def set_sprite_pos(self, pos):
        self.sprite_pos = pos
        self.update()

    sprite_position = pyqtProperty(QPoint, fget=get_sprite_pos, fset=set_sprite_pos)

    def move_sprite_to(self, x, y):
        """Animate sprite to target using current style settings."""
        self.target_pos = QPoint(x, y)

        if self.animation:
            self.animation.stop()

        self.animation = QPropertyAnimation(self, b"sprite_position")
        self.animation.setDuration(self.style["duration"])
        self.animation.setStartValue(self.sprite_pos)
        self.animation.setEndValue(self.target_pos)
        self.animation.setEasingCurve(self.style["easing"])

        if self.style["pulse"]:
            self.animation.finished.connect(self._start_pulse)

        self.animation.start()

    def _start_pulse(self):
        """Start pulsing animation."""
        self.pulse_value = 0
        self.pulse_timer.start(50)

    def _stop_pulse(self):
        """Stop pulsing animation."""
        self.pulse_timer.stop()
        self.pulse_value = 0
        self.update()

    def _pulse_tick(self):
        """Update pulse animation."""
        if self.pulse_growing:
            self.pulse_value += 10
            if self.pulse_value >= 100:
                self.pulse_growing = False
        else:
            self.pulse_value -= 10
            if self.pulse_value <= 0:
                self.pulse_growing = True
        self.update()

    def paintEvent(self, event):
        """Draw sprite using current style."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        x, y = self.sprite_pos.x(), self.sprite_pos.y()
        size = self.style["size"]
        color = self.style["color"]

        if self.style["type"] == "radial_gradient":
            self._draw_radial_gradient(painter, x, y, size, color)
        else:  # concentric_rings
            self._draw_concentric_rings(painter, x, y, size, color)

    def _draw_radial_gradient(self, painter, x, y, size, color):
        """Draw radial gradient orb (Gemini style)."""
        gradient = QRadialGradient(x, y, size / 2)

        # Apply pulse to alpha if active
        core_alpha = color.alpha()
        if self.pulse_timer.isActive():
            core_alpha = min(255, core_alpha + int(self.pulse_value * 0.5))

        core_color = QColor(color)
        core_color.setAlpha(core_alpha)

        edge_color = QColor(color)
        edge_color.setAlpha(0)

        gradient.setColorAt(0, core_color)
        gradient.setColorAt(0.6, core_color)
        gradient.setColorAt(1, edge_color)

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(x - size // 2, y - size // 2, size, size)

    def _draw_concentric_rings(self, painter, x, y, size, color):
        """Draw concentric rings with glow (original style)."""
        base_radius = size // 6

        # Outer glow rings
        for i in range(3, 0, -1):
            alpha = 50 * (4 - i)
            ring_color = QColor(color)
            ring_color.setAlpha(alpha)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(ring_color))
            painter.drawEllipse(x - base_radius * i, y - base_radius * i,
                              base_radius * 2 * i, base_radius * 2 * i)

        # Inner sprite
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QBrush(color))
        painter.drawEllipse(x - base_radius, y - base_radius,
                          base_radius * 2, base_radius * 2)

        # Center dot
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(x - 4, y - 4, 8, 8)


def showcase_styles():
    """Demo all styles in sequence."""
    app = QApplication(sys.argv)

    style_names = list(STYLES.keys())
    current_idx = [0]  # Use list for mutable reference

    overlay = StyledSpriteOverlay(style_names[0])
    overlay.show()

    # Show style name in console
    print(f"\n🎨 Style {current_idx[0] + 1}/{len(style_names)}: {STYLES[style_names[current_idx[0]]]['name']}")

    # Test positions
    positions = [(500, 300), (1000, 500), (300, 700)]
    pos_idx = [0]

    def next_position():
        """Move to next position."""
        overlay.move_sprite_to(positions[pos_idx[0]][0], positions[pos_idx[0]][1])
        pos_idx[0] = (pos_idx[0] + 1) % len(positions)

    def next_style():
        """Switch to next style."""
        overlay._stop_pulse()
        current_idx[0] = (current_idx[0] + 1) % len(style_names)
        overlay.set_style(style_names[current_idx[0]])
        print(f"\n🎨 Style {current_idx[0] + 1}/{len(style_names)}: {STYLES[style_names[current_idx[0]]]['name']}")
        pos_idx[0] = 0
        next_position()

    # Initial animation
    QTimer.singleShot(500, next_position)

    # Move every 2 seconds
    move_timer = QTimer()
    move_timer.timeout.connect(next_position)
    move_timer.start(2000)

    # Change style every 6 seconds (3 movements per style)
    style_timer = QTimer()
    style_timer.timeout.connect(next_style)
    style_timer.start(6000)

    sys.exit(app.exec_())


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Use specific style
        style = sys.argv[1]
        app = QApplication(sys.argv)
        overlay = StyledSpriteOverlay(style)
        overlay.show()
        print(f"🎨 Using style: {STYLES.get(style, STYLES['gemini_golden'])['name']}")
        QTimer.singleShot(1000, lambda: overlay.move_sprite_to(500, 500))
        sys.exit(app.exec_())
    else:
        # Showcase all styles
        showcase_styles()
