
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ===== GEMINI API CONFIGURATION (FREE) =====
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your-api-key-here")
GEMINI_MODEL = "gemini-1.5-flash"  # FREE model
GEMINI_MAX_TOKENS = 512

# ===== WEBOTS CONFIGURATION =====
WEBOTS_ROBOT_NAME = "MyBot"
CAMERA_NAME = "camera"
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_ENABLE_TIME = 100

# ===== ROBOT MOVEMENT CONFIGURATION =====
ROBOT_SPEED = 5.0  # m/s
ROBOT_ANGULAR_SPEED = 1.0  # rad/s
MOVEMENT_TIMEOUT = 30  # seconds

# ===== HOME POSITION =====
HOME_X = 0.0
HOME_Y = 0.0
HOME_ANGLE = 0.0

# ===== FLASK CONFIGURATION =====
FLASK_DEBUG = True
FLASK_PORT = 5000
FLASK_HOST = "0.0.0.0"

# ===== LOGGING CONFIGURATION =====
LOG_LEVEL = "INFO"
LOG_FILE = "robot_activity.log"

# ===== API TIMEOUT =====
API_TIMEOUT = 30  # seconds

# ===== DISTANCE THRESHOLD =====
REACH_THRESHOLD = 0.3  # meters (stop when within 0.3m of target)
