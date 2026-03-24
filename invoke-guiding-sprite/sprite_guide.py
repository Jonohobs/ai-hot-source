"""Main application - AI-powered guiding sprite."""
import sys
import os
import base64
from io import BytesIO
import mss
from PIL import Image
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread, pyqtSignal
from overlay_styled import StyledSpriteOverlay

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class VisionThread(QThread):
    """Background thread for AI Vision API calls (supports Gemini and Claude)."""

    coordinates_found = pyqtSignal(int, int)  # x, y coordinates
    error_occurred = pyqtSignal(str)

    def __init__(self, prompt, screenshot_bytes):
        super().__init__()
        self.prompt = prompt
        self.screenshot_bytes = screenshot_bytes

    def run(self):
        """Call available Vision API to find UI element coordinates."""
        # Check which API to use
        gemini_key = os.environ.get('GEMINI_API_KEY')
        anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
        openai_key = os.environ.get('OPENAI_API_KEY')

        # Priority: Claude > OpenAI > Gemini
        if anthropic_key and ANTHROPIC_AVAILABLE:
            self._use_claude_vision(anthropic_key)
        elif openai_key and OPENAI_AVAILABLE:
            self._use_openai_vision(openai_key)
        elif gemini_key and GEMINI_AVAILABLE:
            self._use_gemini_vision(gemini_key)
        else:
            self.error_occurred.emit(
                "No API key found. Set ANTHROPIC_API_KEY, OPENAI_API_KEY, or GEMINI_API_KEY"
            )

    def _use_claude_vision(self, api_key):
        """Use Claude's vision API."""
        try:
            client = anthropic.Anthropic(api_key=api_key)

            # Convert image to base64
            image_data = base64.b64encode(self.screenshot_bytes).decode('utf-8')

            # Build prompt
            prompt_text = f"""Analyze this screenshot and find the UI element: "{self.prompt}"

Return ONLY the X and Y coordinates of the center of that element in this exact format:
X:1234 Y:567

If you cannot find the element, respond with:
NOT_FOUND"""

            # Call Claude API
            message = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=100,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt_text
                        }
                    ],
                }],
            )

            text = message.content[0].text.strip()
            self._parse_coordinates(text)

        except Exception as e:
            self.error_occurred.emit(f"Claude Vision error: {str(e)}")

    def _use_openai_vision(self, api_key):
        """Use OpenAI GPT-4 Vision API."""
        try:
            client = OpenAI(api_key=api_key)

            # Convert image to base64
            image_data = base64.b64encode(self.screenshot_bytes).decode('utf-8')

            # Build prompt
            prompt_text = f"""Analyze this screenshot and find the UI element: "{self.prompt}"

Return ONLY the X and Y coordinates of the center of that element in this exact format:
X:1234 Y:567

If you cannot find the element, respond with:
NOT_FOUND"""

            # Call OpenAI Vision API
            response = client.chat.completions.create(
                model="gpt-4o",
                max_tokens=100,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_data}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt_text
                            }
                        ]
                    }
                ]
            )

            text = response.choices[0].message.content.strip()
            self._parse_coordinates(text)

        except Exception as e:
            self.error_occurred.emit(f"OpenAI Vision error: {str(e)}")

    def _use_gemini_vision(self, api_key):
        """Use Gemini's vision API."""
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')

            # Prepare image
            image = Image.open(BytesIO(self.screenshot_bytes))

            # Build prompt
            full_prompt = f"""Analyze this screenshot and find the UI element: "{self.prompt}"

Return ONLY the X and Y coordinates of the center of that element in this exact format:
X:1234 Y:567

If you cannot find the element, respond with:
NOT_FOUND"""

            # Generate response
            response = model.generate_content([full_prompt, image])
            text = response.text.strip()

            self._parse_coordinates(text)

        except Exception as e:
            self.error_occurred.emit(f"Gemini Vision error: {str(e)}")

    def _parse_coordinates(self, text):
        """Parse coordinates from API response."""
        try:
            if "NOT_FOUND" in text:
                self.error_occurred.emit(f"Element not found: {self.prompt}")
                return

            # Extract X and Y
            x_part = text.split('X:')[1].split()[0]
            y_part = text.split('Y:')[1].split()[0]
            x = int(x_part)
            y = int(y_part)

            self.coordinates_found.emit(x, y)

        except Exception as e:
            self.error_occurred.emit(f"Failed to parse coordinates: {str(e)}")


class SpriteGuideApp:
    """Main application coordinating screen capture, AI vision, and sprite overlay."""

    def __init__(self, style="gemini_golden"):
        self.app = QApplication(sys.argv)
        self.overlay = StyledSpriteOverlay(style)
        self.overlay.show()
        self.vision_thread = None

    def capture_screenshot(self):
        """Capture current screen as bytes."""
        with mss.mss() as sct:
            # Capture primary monitor
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)

            # Convert to PIL Image
            img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)

            # Convert to bytes
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            return buffer.getvalue()

    def guide_to(self, element_description):
        """Guide sprite to UI element described by user.

        Args:
            element_description: Natural language description (e.g., "the save button")
        """
        print(f"🔍 Looking for: {element_description}")

        # Capture screen
        screenshot_bytes = self.capture_screenshot()

        # Call Vision API in background thread
        self.vision_thread = VisionThread(element_description, screenshot_bytes)
        self.vision_thread.coordinates_found.connect(self.on_coordinates_found)
        self.vision_thread.error_occurred.connect(self.on_error)
        self.vision_thread.start()

    def on_coordinates_found(self, x, y):
        """Handle successful coordinate detection."""
        print(f"✨ Found at ({x}, {y}) - moving sprite...")
        self.overlay.move_sprite_to(x, y)

    def on_error(self, error_msg):
        """Handle errors."""
        print(f"❌ Error: {error_msg}")

    def run(self):
        """Start the application."""
        return self.app.exec_()


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python sprite_guide.py \"element description\" [style]")
        print("Example: python sprite_guide.py \"the save button\"")
        print("         python sprite_guide.py \"the search bar\" cyan_sharp")
        print("\nSet one of these API keys in your environment:")
        print("  ANTHROPIC_API_KEY (Claude) - preferred")
        print("  OPENAI_API_KEY (GPT-4 Vision)")
        print("  GEMINI_API_KEY (Gemini Vision)")
        print("\nAvailable styles: gemini_golden (default), blue_glow, hybrid_pulse,")
        print("                  emerald_soft, purple_rings, red_alert, cyan_sharp")
        sys.exit(1)

    # Get element description from command line
    args = sys.argv[1:]

    # Check if last arg is a style name
    from sprite_styles import STYLES
    style = "gemini_golden"
    if args[-1] in STYLES:
        style = args[-1]
        element_description = " ".join(args[:-1])
    else:
        element_description = " ".join(args)

    # Create and run app
    app = SpriteGuideApp(style=style)

    # Start guiding to element
    app.guide_to(element_description)

    # Run Qt event loop
    sys.exit(app.run())


if __name__ == "__main__":
    main()
