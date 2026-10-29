
import cv2
import numpy as np
import base64
import logging
from io import BytesIO
from PIL import Image
from datetime import datetime
from config import LOG_LEVEL, LOG_FILE

# ===== LOGGING SETUP =====
def setup_logger(name):
    """Setup logger with file and console output"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, LOG_LEVEL))
    
    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(getattr(logging, LOG_LEVEL))
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logger(__name__)

# ===== IMAGE CONVERSION =====
def webots_image_to_numpy(image_data, width, height):
    """
    Convert Webots camera image to NumPy array
    
    Args:
        image_data: Raw image data from Webots camera
        width: Image width
        height: Image height
    
    Returns:
        NumPy array (BGR format)
    """
    try:
        # Webots returns RGBA, convert to BGR for OpenCV
        raw_array = np.frombuffer(image_data, dtype=np.uint8)
        rgba_image = raw_array.reshape((height, width, 4))
        bgr_image = cv2.cvtColor(rgba_image, cv2.COLOR_RGBA2BGR)
        return bgr_image
    except Exception as e:
        logger.error(f"Error converting Webots image: {e}")
        return None

def numpy_to_jpeg_base64(image_array):
    """
    Convert NumPy array to JPEG Base64 string
    
    Args:
        image_array: NumPy array (BGR format)
    
    Returns:
        Base64 encoded JPEG string
    """
    try:
        # Encode NumPy array to JPEG
        success, buffer = cv2.imencode('.jpg', image_array)
        if not success:
            raise ValueError("Failed to encode image to JPEG")
        
        # Convert to PIL Image (for safety)
        pil_image = Image.open(BytesIO(buffer.tobytes()))
        
        # Convert to Base64
        buffered = BytesIO()
        pil_image.save(buffered, format="JPEG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return img_base64
    except Exception as e:
        logger.error(f"Error converting image to Base64: {e}")
        return None

def save_image_locally(image_array, filename="latest_capture.jpg"):
    """
    Save image locally for debugging
    
    Args:
        image_array: NumPy array
        filename: Output filename
    """
    try:
        cv2.imwrite(filename, image_array)
        logger.info(f"✓ Image saved: {filename}")
    except Exception as e:
        logger.error(f"Error saving image: {e}")

# ===== JSON PARSING =====
def parse_claude_response(response_text):
    """
    Parse Claude's JSON response safely
    
    Args:
        response_text: Raw text from Claude API
    
    Returns:
        Parsed dictionary or None
    """
    import json
    
    try:
        # Remove markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        # Parse JSON
        data = json.loads(response_text)
        logger.info(f"✓ Parsed Claude response: {data}")
        return data
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        logger.error(f"Response was: {response_text}")
        return None
    except Exception as e:
        logger.error(f"Error parsing Claude response: {e}")
        return None

# ===== DISTANCE CALCULATION =====
def calculate_distance(x1, y1, x2, y2):
    """Calculate Euclidean distance between two points"""
    return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def calculate_angle(x1, y1, x2, y2):
    """Calculate angle from point 1 to point 2"""
    delta_x = x2 - x1
    delta_y = y2 - y1
    angle = np.arctan2(delta_y, delta_x)
    return angle

# ===== TIMESTAMP =====
def get_timestamp():
    """Get current timestamp for logging"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ===== FILE OPERATIONS =====
def read_file(filepath):
    """Read file contents"""
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {filepath}: {e}")
        return None

def write_file(filepath, content):
    """Write content to file"""
    try:
        with open(filepath, 'w') as f:
            f.write(content)
        logger.info(f"✓ Written to {filepath}")
    except Exception as e:
        logger.error(f"Error writing to file {filepath}: {e}")
