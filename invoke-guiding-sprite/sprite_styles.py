"""Visual style configurations for the guiding sprite."""
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QEasingCurve

STYLES = {
    "gemini_golden": {
        "name": "Gemini's Golden Orb",
        "type": "radial_gradient",
        "color": QColor(255, 220, 0, 180),
        "size": 100,
        "pulse": True,
        "easing": QEasingCurve.OutBack,
        "duration": 1500,
    },
    "blue_glow": {
        "name": "Blue Concentric Glow (Original)",
        "type": "concentric_rings",
        "color": QColor(100, 200, 255, 200),
        "size": 80,
        "pulse": False,
        "easing": QEasingCurve.InOutCubic,
        "duration": 1000,
    },
    "hybrid_pulse": {
        "name": "Golden Gradient + Blue Pulse",
        "type": "radial_gradient",
        "color": QColor(100, 200, 255, 180),
        "size": 100,
        "pulse": True,
        "easing": QEasingCurve.OutBack,
        "duration": 1200,
    },
    "emerald_soft": {
        "name": "Emerald Soft Glow",
        "type": "radial_gradient",
        "color": QColor(80, 255, 150, 160),
        "size": 90,
        "pulse": True,
        "easing": QEasingCurve.InOutQuad,
        "duration": 1300,
    },
    "purple_rings": {
        "name": "Purple Energy Rings",
        "type": "concentric_rings",
        "color": QColor(200, 100, 255, 200),
        "size": 80,
        "pulse": False,
        "easing": QEasingCurve.OutElastic,
        "duration": 1400,
    },
    "red_alert": {
        "name": "Red Alert Pulse",
        "type": "radial_gradient",
        "color": QColor(255, 80, 80, 180),
        "size": 110,
        "pulse": True,
        "easing": QEasingCurve.OutBounce,
        "duration": 1000,
    },
    "cyan_sharp": {
        "name": "Cyan Sharp Focus",
        "type": "concentric_rings",
        "color": QColor(0, 255, 255, 220),
        "size": 70,
        "pulse": False,
        "easing": QEasingCurve.InOutCubic,
        "duration": 800,
    },
}
