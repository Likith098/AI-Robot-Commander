import socket
import json
import logging

from utils import setup_logger

logger = setup_logger(__name__)


class WebotsController:
    """
    Flask-side communication controller.

    IMPORTANT:
    This class does NOT create a Webots Robot().
    The actual Robot/Supervisor exists only inside Webots.
    """

    def __init__(self, host="127.0.0.1", port=5001):

        self.host = host
        self.port = port

        self.current_command = None
        self.current_target = None
        self.task_status = "idle"

        logger.info("Webots communication client initialized")

    def _send_request(self, data):
        """
        Send a command to the Webots controller.
        """

        try:

            message = json.dumps(data).encode("utf-8")

            with socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            ) as client:

                client.settimeout(10)

                client.connect(
                    (self.host, self.port)
                )

                client.sendall(message)

                response = client.recv(65536)

            if not response:
                return None

            return json.loads(
                response.decode("utf-8")
            )

        except ConnectionRefusedError:

            logger.error(
                "Cannot connect to Webots controller. "
                "Make sure Webots is running."
            )

            return None

        except socket.timeout:

            logger.error(
                "Webots controller connection timed out."
            )

            return None

        except Exception as e:

            logger.error(
                f"Webots communication error: {e}"
            )

            return None

    def initialize(self):
        """
        Check communication with Webots.
        """

        response = self._send_request({
            "action": "status"
        })

        if response is None:

            self.task_status = "not_initialized"

            return False

        self.task_status = "idle"

        logger.info(
            "Webots controller connected successfully"
        )

        return True

    def capture_image(self):

        response = self._send_request({
            "action": "capture"
        })

        if not response:
            return None

        if response.get("status") != "success":
            return None

        return response.get("image")

    def move(self, left_speed, right_speed):

        response = self._send_request({
            "action": "move",
            "left": left_speed,
            "right": right_speed
        })

        return response

    def stop(self):

        return self._send_request({
            "action": "stop"
        })

    def grab_object(self, object_name="red_mug"):

        response = self._send_request({
            "action": "grab",
            "object": object_name
        })

        return response

    def release_object(self):

        response = self._send_request({
            "action": "release"
        })

        return response

    def return_home(self):

        response = self._send_request({
            "action": "return_home"
        })

        return response

    def process_command(self, command):

        logger.info(
            f"Processing command: {command}"
        )

        self.current_command = command
        self.task_status = "processing"

        response = self._send_request({
            "action": "command",
            "command": command
        })

        if response is None:

            self.task_status = "error"

            return {
                "status": "error",
                "message":
                    "Webots controller is not connected.",
                "command": command
            }

        self.task_status = response.get(
            "status",
            "unknown"
        )

        return response

    def run_step(self):

        """
        Flask does not control Webots simulation steps.

        Webots itself runs the simulation loop.
        """

        return True

    def get_status(self):

        response = self._send_request({
            "action": "status"
        })

        if response is None:

            return {
                "task_status": "not_initialized",
                "current_command":
                    self.current_command,
                "position": {}
            }

        return response