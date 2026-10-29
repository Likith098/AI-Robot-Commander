import google.generativeai as genai
import json
import base64
import io

from PIL import Image

from config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_MAX_TOKENS,
    API_TIMEOUT
)

from utils import setup_logger, parse_claude_response


logger = setup_logger(__name__)


class GeminiVisionAPI:
    """
    Wrapper for Gemini Vision API (FREE)
    Handles image analysis and structured responses.
    """

    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.model = GEMINI_MODEL
        self.max_tokens = GEMINI_MAX_TOKENS
        self.timeout = API_TIMEOUT

        # Configure Gemini
        genai.configure(api_key=self.api_key)

        self.client = genai.GenerativeModel(self.model)

        if not self.api_key or self.api_key == "your-api-key-here":
            logger.warning("⚠ GEMINI_API_KEY not properly configured!")
            logger.warning(
                "Set GEMINI_API_KEY environment variable or in config.py"
            )

    def analyze_image(self, image_base64, user_command):
        """
        Send image and command to Gemini for analysis.

        Args:
            image_base64: Base64 encoded image
            user_command: User's natural language command

        Returns:
            Parsed JSON response or None
        """

        try:
            logger.info("🧠 Querying Gemini Vision API...")
            logger.info(f"Command: {user_command}")

            # Convert Base64 to bytes
            image_bytes = base64.b64decode(image_base64)

            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))

            # Build prompt
            prompt = self._build_prompt(user_command)

            # Send request to Gemini
            response = self.client.generate_content(
                [prompt, image],
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=self.max_tokens
                )
            )

            # Extract response text
            message_content = response.text

            logger.info("✓ Gemini responded successfully")

            # Parse JSON response
            #
            # Keeping parse_claude_response here because this function
            # already exists in your utils.py and we don't want to
            # unnecessarily modify another file.
            parsed = parse_claude_response(message_content)

            return parsed

        except Exception as e:
            logger.error(f"❌ Error calling Gemini API: {e}")
            return None

    def _build_prompt(self, user_command):
        """
        Build the prompt for Gemini.
        """

        prompt = f"""
You are controlling a mobile service robot in a Webots simulation.

Analyze this camera image and identify the object requested by the user.

User Command: {user_command}

Analyze the image and return ONLY valid JSON (no explanations, no markdown code blocks).

JSON Response Format:

{{
    "object": "name of the detected object",
    "found": true or false,
    "position": {{
        "x": estimated x coordinate (0-10),
        "y": estimated y coordinate (0-10)
    }},
    "distance": estimated distance in meters (0-10),
    "confidence": confidence score (0.0-1.0),
    "description": "brief description of what you see"
}}

IMPORTANT:
Return ONLY the JSON.
Do not include explanations.
Do not include markdown.
Do not include ```json.
"""

        return prompt


# ============================================================
# SINGLETON INSTANCE
# ============================================================

gemini_api = GeminiVisionAPI()


def query_gemini(image_base64, command):
    """
    Convenience function to query Gemini.

    Args:
        image_base64: Base64 encoded image
        command: User command

    Returns:
        Parsed JSON response
    """

    return gemini_api.analyze_image(
        image_base64,
        command
    )