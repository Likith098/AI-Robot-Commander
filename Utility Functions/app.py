
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
from robot_controller import WebotsController
from utils import setup_logger, get_timestamp
from config import FLASK_HOST, FLASK_PORT

logger = setup_logger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize Webots controller (global)
webots_controller = None
command_queue = []
task_history = []

# ===== ERROR HANDLERS =====
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# ===== HOME PAGE =====
@app.route("/", methods=["GET"])
def home():
    """Serve the main chat interface"""
    return render_template("index.html")

# ===== API: INITIALIZE ROBOT =====
@app.route("/api/initialize", methods=["POST"])
def initialize():
    """Initialize Webots robot"""
    try:
        global webots_controller
        
        if webots_controller is not None:
            return jsonify({
                "status": "already_initialized",
                "message": "Robot already initialized"
            }), 200
        
        logger.info("Initializing Webots controller...")
        webots_controller = WebotsController()
        
        logger.info("Robot initialized successfully")
        return jsonify({
            "status": "success",
            "message": "Robot initialized successfully",
            "timestamp": get_timestamp()
        }), 200
    
    except Exception as e:
        logger.error(f"Error initializing robot: {e}")
        return jsonify({
            "status": "error",
            "message": f"Failed to initialize robot: {str(e)}",
            "timestamp": get_timestamp()
        }), 500

# ===== API: SEND COMMAND =====
@app.route("/api/command", methods=["POST"])
def send_command():
    """
    Send a command to the robot
    
    Request body:
    {
        "command": "Bring me the red mug"
    }
    """
    try:
        data = request.json
        command = data.get("command", "").strip()
        
        if not command:
            return jsonify({
                "status": "error",
                "message": "Command cannot be empty"
            }), 400
        
        if webots_controller is None:
            return jsonify({
                "status": "error",
                "message": "Robot not initialized. Call /api/initialize first."
            }), 400
        
        logger.info(f"📢 Received command: {command}")
        
        # Process command
        result = webots_controller.process_command(command)
        
        # Add to history
        task_history.append({
            "timestamp": get_timestamp(),
            "command": command,
            "result": result
        })
        
        logger.info(f"Task result: {result}")
        
        return jsonify({
            "status": "success",
            "result": result,
            "timestamp": get_timestamp()
        }), 200
    
    except Exception as e:
        logger.error(f"Error processing command: {e}")
        return jsonify({
            "status": "error",
            "message": f"Error processing command: {str(e)}",
            "timestamp": get_timestamp()
        }), 500

# ===== API: GET STATUS =====
@app.route("/api/status", methods=["GET"])
def get_status():
    """Get current robot status"""
    try:
        if webots_controller is None:
            return jsonify({
                "status": "not_initialized",
                "message": "Robot not initialized"
            }), 200
        
        status = webots_controller.get_status()
        return jsonify({
            "status": "success",
            "robot_status": status,
            "timestamp": get_timestamp()
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({
            "status": "error",
            "message": f"Error getting status: {str(e)}"
        }), 500

# ===== API: GET HISTORY =====
@app.route("/api/history", methods=["GET"])
def get_history():
    """Get task history"""
    try:
        return jsonify({
            "status": "success",
            "history": task_history,
            "count": len(task_history)
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        return jsonify({
            "status": "error",
            "message": f"Error getting history: {str(e)}"
        }), 500

# ===== API: CLEAR HISTORY =====
@app.route("/api/history/clear", methods=["POST"])
def clear_history():
    """Clear task history"""
    global task_history
    task_history = []
    logger.info("History cleared")
    return jsonify({
        "status": "success",
        "message": "History cleared",
        "timestamp": get_timestamp()
    }), 200

# ===== API: HEALTH CHECK =====
@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "Server is running",
        "timestamp": get_timestamp()
    }), 200

# ===== RUN SERVER =====
if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("🤖 Starting Flask AI Robot Server")
    logger.info("=" * 50)
    logger.info(f"Host: {FLASK_HOST}")
    logger.info(f"Port: {FLASK_PORT}")
    logger.info(f"Debug: {app.debug}")
    logger.info("=" * 50)
    
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=True)
