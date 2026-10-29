from controller import Supervisor
from PIL import Image
import os
import base64
import socket
import json
import threading
import queue
import math


# ============================================================
# WEBOTS SUPERVISOR
# ============================================================

robot = Supervisor()
timestep = int(robot.getBasicTimeStep())

print("==============================================")
print("       WEBOTS VISION CONTROLLER STARTED")
print("==============================================")


# ============================================================
# FIXED HOME POSITION
# ============================================================
#
# IMPORTANT:
# These are the coordinates where HOME should be.
#
# Webots uses:
# X = horizontal
# Y = vertical
# Z = horizontal
#
# Change these two values if your desired home position
# is somewhere else.
#

HOME_X = 0.0
HOME_Z = 0.0

print("==============================================")
print("FIXED HOME POSITION")
print(f"HOME X = {HOME_X:.3f}")
print(f"HOME Z = {HOME_Z:.3f}")
print("==============================================")


# ============================================================
# IMAGE SETTINGS
# ============================================================

SAVE_DIR = "captured"
IMAGE_PATH = os.path.join(
    SAVE_DIR,
    "scene.png"
)

os.makedirs(
    SAVE_DIR,
    exist_ok=True
)


# ============================================================
# CAMERA
# ============================================================

camera = robot.getDevice("camera")

if camera is None:
    print("ERROR: Camera not found!")
    raise SystemExit

camera.enable(timestep)

print("CAMERA INITIALIZED")


# ============================================================
# MOTORS
# ============================================================

left_motor = robot.getDevice(
    "left wheel motor"
)

right_motor = robot.getDevice(
    "right wheel motor"
)

if left_motor is None:
    print("ERROR: Left wheel motor not found!")
    raise SystemExit

if right_motor is None:
    print("ERROR: Right wheel motor not found!")
    raise SystemExit


# Velocity control
left_motor.setPosition(float("inf"))
right_motor.setPosition(float("inf"))


# Robot starts stopped
left_motor.setVelocity(0.0)
right_motor.setVelocity(0.0)

print("MOTORS INITIALIZED")
print("ROBOT IS STOPPED")


# ============================================================
# ROBOT NODE
# ============================================================

robot_node = robot.getSelf()

if robot_node is None:
    print("ERROR: Could not get robot node!")
    raise SystemExit

print("ROBOT NODE FOUND")


# ============================================================
# MOVE ROBOT TO FIXED HOME POSITION
# ============================================================
#
# This is different from your old code.
#
# OLD:
#   HOME = robot's starting position
#
# NEW:
#   HOME = fixed coordinates above
#

def set_robot_home_position():

    try:

        translation_field = robot_node.getField(
            "translation"
        )

        if translation_field is None:

            print(
                "ERROR: Robot translation field "
                "not found!"
            )

            return False

        current_translation = (
            robot_node.getPosition()
        )

        print("==============================================")
        print("SETTING ROBOT TO FIXED HOME")
        print(
            f"OLD X = {current_translation[0]:.3f}"
        )
        print(
            f"OLD Z = {current_translation[2]:.3f}"
        )
        print(
            f"NEW X = {HOME_X:.3f}"
        )
        print(
            f"NEW Z = {HOME_Z:.3f}"
        )
        print("==============================================")


        # Keep current Y height
        y_position = current_translation[1]

        translation_field.setSFVec3f(
            [
                HOME_X,
                y_position,
                HOME_Z
            ]
        )


        # Reset robot rotation
        rotation_field = robot_node.getField(
            "rotation"
        )

        if rotation_field is not None:

            rotation_field.setSFRotation(
                [
                    0,
                    1,
                    0,
                    0
                ]
            )


        print("ROBOT PLACED AT FIXED HOME")

        return True


    except Exception as e:

        print(
            f"ERROR SETTING HOME POSITION: {e}"
        )

        return False


# ============================================================
# SET ROBOT AT HOME ON STARTUP
# ============================================================

set_robot_home_position()


# ============================================================
# OBJECT STATE
# ============================================================

held_object = None


# ============================================================
# COMMAND QUEUE
# ============================================================

command_queue = queue.Queue()


# ============================================================
# FIND OBJECT BY NAME
# ============================================================

def find_object_by_name(object_name):

    try:

        root = robot.getRoot()

        children_field = root.getField(
            "children"
        )

        if children_field is None:

            print(
                "ERROR: World children field "
                "not found!"
            )

            return None


        count = children_field.getCount()


        for i in range(count):

            node = children_field.getMFNode(i)

            if node is None:
                continue


            name_field = node.getField(
                "name"
            )

            if name_field is None:
                continue


            name = name_field.getSFString()


            if name == object_name:

                return node


        return None


    except Exception as e:

        print(
            f"ERROR finding object: {e}"
        )

        return None


# ============================================================
# GET OBJECT POSITION
# ============================================================

def get_object_position(object_node):

    try:

        if object_node is None:
            return None


        position = object_node.getPosition()


        return {
            "x": position[0],
            "y": position[2]
        }


    except Exception as e:

        print(
            f"ERROR getting object position: {e}"
        )

        return None


# ============================================================
# GRAB OBJECT
# ============================================================

def grab_object(object_name):

    global held_object


    print("==============================================")
    print(
        f"LOOKING FOR OBJECT: {object_name}"
    )
    print("==============================================")


    object_node = find_object_by_name(
        object_name
    )


    if object_node is None:

        print(
            f"ERROR: Object '{object_name}' "
            "was not found!"
        )

        return False


    held_object = object_node


    print("==============================================")
    print(
        f"OBJECT GRABBED: {object_name}"
    )
    print("==============================================")


    return True


# ============================================================
# RELEASE OBJECT
# ============================================================

def release_object():

    global held_object


    if held_object is None:

        print(
            "NO OBJECT CURRENTLY HELD"
        )

        return False


    print("==============================================")
    print("OBJECT RELEASED")
    print("==============================================")


    held_object = None


    return True


# ============================================================
# UPDATE HELD OBJECT
# ============================================================

def update_held_object():

    global held_object


    if held_object is None:
        return


    try:

        robot_position = (
            robot_node.getPosition()
        )


        translation_field = (
            held_object.getField(
                "translation"
            )
        )


        if translation_field is not None:

            translation_field.setSFVec3f(
                [
                    robot_position[0],
                    0.06,
                    robot_position[2]
                ]
            )


    except Exception as e:

        print(
            f"ERROR updating held object: {e}"
        )


# ============================================================
# STOP ROBOT
# ============================================================

def stop_robot():

    left_motor.setVelocity(0.0)
    right_motor.setVelocity(0.0)

    print("ROBOT STOPPED")


# ============================================================
# MOVE FORWARD
# ============================================================

def move_forward(speed=3.0):

    left_motor.setVelocity(speed)
    right_motor.setVelocity(speed)

    print(
        f"MOVING FORWARD: {speed}"
    )


# ============================================================
# MOVE BACKWARD
# ============================================================

def move_backward(speed=3.0):

    left_motor.setVelocity(-speed)
    right_motor.setVelocity(-speed)

    print(
        f"MOVING BACKWARD: {speed}"
    )


# ============================================================
# TURN LEFT
# ============================================================

def turn_left(speed=3.0):

    left_motor.setVelocity(-speed)
    right_motor.setVelocity(speed)

    print(
        f"TURNING LEFT: {speed}"
    )


# ============================================================
# TURN RIGHT
# ============================================================

def turn_right(speed=3.0):

    left_motor.setVelocity(speed)
    right_motor.setVelocity(-speed)

    print(
        f"TURNING RIGHT: {speed}"
    )


# ============================================================
# GET ROBOT ANGLE
# ============================================================

def get_robot_angle():

    try:

        rotation_field = robot_node.getField(
            "rotation"
        )

        if rotation_field is None:
            return 0.0


        rotation = (
            rotation_field.getSFRotation()
        )


        # Webots:
        # [axis_x, axis_y, axis_z, angle]

        return rotation[3]


    except Exception as e:

        print(
            f"ERROR getting robot angle: {e}"
        )

        return 0.0


# ============================================================
# NORMALIZE ANGLE
# ============================================================

def normalize_angle(angle):

    while angle > math.pi:

        angle -= 2 * math.pi


    while angle < -math.pi:

        angle += 2 * math.pi


    return angle


# ============================================================
# NAVIGATE TO TARGET
# ============================================================

def navigate_to(
    target_x,
    target_z,
    tolerance=0.08
):

    print("==============================================")
    print(
        f"NAVIGATING TO "
        f"X={target_x:.3f}, "
        f"Z={target_z:.3f}"
    )
    print("==============================================")


    forward_speed = 3.0
    turn_speed = 2.0

    max_steps = 1000
    steps = 0


    while robot.step(timestep) != -1:

        steps += 1


        if steps > max_steps:

            print(
                "NAVIGATION TIMEOUT"
            )

            stop_robot()

            return False


        position = robot_node.getPosition()


        current_x = position[0]
        current_z = position[2]


        dx = target_x - current_x
        dz = target_z - current_z


        distance = math.sqrt(
            dx * dx +
            dz * dz
        )


        print(
            f"POSITION "
            f"X={current_x:.2f} "
            f"Z={current_z:.2f} "
            f"DISTANCE={distance:.3f}"
        )


        # ----------------------------------------------------
        # TARGET REACHED
        # ----------------------------------------------------

        if distance <= tolerance:

            stop_robot()

            print(
                "=============================================="
            )
            print("TARGET REACHED")
            print(
                "=============================================="
            )

            return True


        # ----------------------------------------------------
        # GET CURRENT ANGLE
        # ----------------------------------------------------

        current_angle = (
            get_robot_angle()
        )


        # ----------------------------------------------------
        # CALCULATE TARGET ANGLE
        # ----------------------------------------------------

        target_angle = math.atan2(
            -dx,
            -dz
        )


        angle_error = normalize_angle(
            target_angle -
            current_angle
        )


        # ----------------------------------------------------
        # TURN
        # ----------------------------------------------------

        if abs(angle_error) > 0.20:

            if angle_error > 0:

                turn_left(
                    turn_speed
                )

                print(
                    "TURNING LEFT "
                    "TOWARD TARGET"
                )

            else:

                turn_right(
                    turn_speed
                )

                print(
                    "TURNING RIGHT "
                    "TOWARD TARGET"
                )


        # ----------------------------------------------------
        # MOVE FORWARD
        # ----------------------------------------------------

        else:

            move_forward(
                forward_speed
            )

            print(
                "MOVING TOWARD TARGET"
            )


        # Keep object attached
        update_held_object()


    stop_robot()

    return False


# ============================================================
# RETURN HOME
# ============================================================

def return_home():

    print("==============================================")
    print("RETURNING TO FIXED HOME POSITION")
    print("==============================================")

    print(
        f"HOME TARGET: "
        f"X={HOME_X:.3f}, "
        f"Z={HOME_Z:.3f}"
    )


    success = navigate_to(
        HOME_X,
        HOME_Z
    )


    if success:

        stop_robot()

        print(
            "=============================================="
        )
        print("ROBOT RETURNED HOME")
        print(
            "=============================================="
        )

        return True


    print(
        "=============================================="
    )
    print("FAILED TO RETURN HOME")
    print(
        "=============================================="
    )


    stop_robot()

    return False


# ============================================================
# CAPTURE IMAGE
# ============================================================

def capture_image():

    try:

        image_data = camera.getImage()


        if image_data is None:

            print(
                "WARNING: CAMERA RETURNED NO IMAGE"
            )

            return None


        width = camera.getWidth()
        height = camera.getHeight()


        image = Image.frombytes(
            "RGBA",
            (
                width,
                height
            ),
            image_data
        )


        image = image.convert(
            "RGB"
        )


        image.save(
            IMAGE_PATH
        )


        with open(
            IMAGE_PATH,
            "rb"
        ) as img_file:

            base64_string = (
                base64.b64encode(
                    img_file.read()
                ).decode("utf-8")
            )


        print(
            "=============================================="
        )
        print(
            "IMAGE CAPTURED SUCCESSFULLY"
        )
        print(
            f"Resolution: "
            f"{width} x {height}"
        )
        print(
            f"Saved to: {IMAGE_PATH}"
        )
        print(
            "=============================================="
        )


        return base64_string


    except Exception as e:

        print(
            f"ERROR capturing image: {e}"
        )

        return None


# ============================================================
# STATUS
# ============================================================

def get_status():

    try:

        position = (
            robot_node.getPosition()
        )


        return {

            "status": "success",

            "task_status": "idle",

            "current_command": "None",

            "position": {

                "x": float(position[0]),

                "y": float(position[2])

            },

            "target": {

                "x": float(HOME_X),

                "y": float(HOME_Z)

            },

            "holding_object":
                held_object is not None

        }


    except Exception as e:

        return {

            "status": "error",

            "message": str(e)

        }


# ============================================================
# PROCESS NATURAL LANGUAGE COMMAND
# ============================================================

def process_natural_command(
    command_text
):

    command_text = (
        command_text
        .strip()
        .lower()
    )


    print(
        "=============================================="
    )

    print(
        f"NATURAL LANGUAGE COMMAND: "
        f"{command_text}"
    )

    print(
        "=============================================="
    )


    if not command_text:

        return {

            "status": "error",

            "message":
                "Command is empty"

        }


    # ========================================================
    # HOME COMMANDS
    # ========================================================

    home_commands = [

        "go home",

        "return home",

        "come back",

        "come back home",

        "return to start",

        "go back to start",

        "return to starting position",

        "go back home",

        "go to starting position",

        "return to my position"

    ]


    if any(
        phrase in command_text
        for phrase in home_commands
    ):

        print(
            "HOME COMMAND DETECTED"
        )


        success = return_home()


        if success:

            return {

                "status": "success",

                "message":
                    "Robot returned to "
                    "fixed home position",

                "action": "home",

                "target": {

                    "x": HOME_X,

                    "y": HOME_Z

                }

            }


        return {

            "status": "error",

            "message":
                "Robot failed to return home",

            "action": "home",

            "target": {

                "x": HOME_X,

                "y": HOME_Z

            }

        }


    # ========================================================
    # STOP COMMANDS
    # ========================================================

    stop_commands = [

        "stop",

        "stop robot",

        "halt",

        "freeze",

        "stay"

    ]


    if any(
        phrase in command_text
        for phrase in stop_commands
    ):

        stop_robot()


        return {

            "status": "success",

            "message":
                "Robot stopped",

            "action": "stop"

        }


    # ========================================================
    # RELEASE COMMANDS
    # ========================================================

    release_commands = [

        "release",

        "release object",

        "drop object",

        "place object",

        "put it down"

    ]


    if any(
        phrase in command_text
        for phrase in release_commands
    ):

        success = release_object()


        return {

            "status":
                "success"
                if success
                else "error",

            "message":
                "Object released"
                if success
                else
                "No object currently held",

            "action": "release"

        }


    # ========================================================
    # KNOWN OBJECTS
    # ========================================================

    known_objects = [

        "red_mug",

        "blue_ball",

        "yellow_cup",

        "green_box"

    ]


    object_name = None


    # ========================================================
    # FIND OBJECT FROM COMMAND
    # ========================================================

    for obj in known_objects:

        readable_name = obj.replace(
            "_",
            " "
        )


        if (
            obj in command_text
            or readable_name in command_text
        ):

            object_name = obj

            break


    # ========================================================
    # OBJECT NOT RECOGNIZED
    # ========================================================

    if object_name is None:

        print(
            "ERROR: Could not identify object"
        )


        return {

            "status": "error",

            "message":
                "Could not identify an object "
                "from the command",

            "action": "none"

        }


    print(
        f"OBJECT IDENTIFIED: "
        f"{object_name}"
    )


    # ========================================================
    # FIND OBJECT
    # ========================================================

    object_node = find_object_by_name(
        object_name
    )


    if object_node is None:

        return {

            "status": "error",

            "message":
                f"Object '{object_name}' "
                "was not found",

            "object": object_name,

            "action": "grab"

        }


    # ========================================================
    # GET OBJECT POSITION
    # ========================================================

    object_position = (
        get_object_position(
            object_node
        )
    )


    # ========================================================
    # GRAB OBJECT
    # ========================================================

    success = grab_object(
        object_name
    )


    if not success:

        return {

            "status": "error",

            "message":
                f"Could not grab "
                f"'{object_name}'",

            "object": object_name,

            "action": "grab"

        }


    # ========================================================
    # RETURN SUCCESS
    # ========================================================

    response = {

        "status": "success",

        "message":
            f"Command understood. "
            f"Object '{object_name}' grabbed.",

        "action": "grab",

        "object": object_name,

        "confidence": 1.0

    }


    # Add target only if available
    if object_position is not None:

        response["target"] = {

            "x": float(
                object_position["x"]
            ),

            "y": float(
                object_position["y"]
            )

        }


    return response


# ============================================================
# EXECUTE REQUEST
# ============================================================
#
# This function runs ONLY in the Webots main thread.
#

def execute_request(request):

    action = request.get(
        "action",
        ""
    )


    print(
        "=============================================="
    )

    print(
        f"EXECUTING ACTION: {action}"
    )

    print(
        "=============================================="
    )


    # ========================================================
    # STATUS
    # ========================================================

    if action == "status":

        return get_status()


    # ========================================================
    # CAPTURE
    # ========================================================

    elif action == "capture":

        image = capture_image()


        if image:

            return {

                "status": "success",

                "image": image

            }


        return {

            "status": "error",

            "message":
                "Camera capture failed"

        }


    # ========================================================
    # DIRECT MOVEMENT
    # ========================================================

    elif action == "move":

        try:

            left = float(
                request.get(
                    "left",
                    0
                )
            )


            right = float(
                request.get(
                    "right",
                    0
                )
            )


            left_motor.setVelocity(
                left
            )


            right_motor.setVelocity(
                right
            )


            return {

                "status": "success",

                "message":
                    "Movement command executed",

                "left": left,

                "right": right

            }


        except (
            ValueError,
            TypeError
        ):

            return {

                "status": "error",

                "message":
                    "Invalid motor speed"

            }


    # ========================================================
    # STOP
    # ========================================================

    elif action == "stop":

        stop_robot()


        return {

            "status": "success",

            "message":
                "Robot stopped"

        }


    # ========================================================
    # GRAB
    # ========================================================

    elif action == "grab":

        object_name = request.get(
            "object",
            "red_mug"
        )


        object_node = find_object_by_name(
            object_name
        )


        if object_node is None:

            return {

                "status": "error",

                "message":
                    "Object not found",

                "object": object_name

            }


        object_position = (
            get_object_position(
                object_node
            )
        )


        success = grab_object(
            object_name
        )


        response = {

            "status":
                "success"
                if success
                else "error",

            "message":
                "Object grabbed"
                if success
                else
                "Object not found",

            "object": object_name,

            "confidence": 1.0

        }


        if object_position is not None:

            response["target"] = {

                "x": float(
                    object_position["x"]
                ),

                "y": float(
                    object_position["y"]
                )

            }


        return response


    # ========================================================
    # RELEASE
    # ========================================================

    elif action == "release":

        success = release_object()


        return {

            "status":
                "success"
                if success
                else "error",

            "message":
                "Object released"
                if success
                else
                "No object currently held"

        }


    # ========================================================
    # NATURAL LANGUAGE
    # ========================================================

    elif action == "command":

        command_text = request.get(
            "command",
            ""
        )


        return process_natural_command(
            command_text
        )


    # ========================================================
    # UNKNOWN ACTION
    # ========================================================

    else:

        return {

            "status": "error",

            "message":
                f"Unknown action: {action}"

        }


# ============================================================
# COMMAND SERVER
# ============================================================

def command_server():

    server = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )


    server.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )


    try:

        server.bind(
            (
                "127.0.0.1",
                5001
            )
        )


        server.listen(5)


        print(
            "=============================================="
        )

        print(
            "COMMAND SERVER STARTED"
        )

        print(
            "HOST: 127.0.0.1"
        )

        print(
            "PORT: 5001"
        )

        print(
            "=============================================="
        )


        while True:

            connection = None


            try:

                connection, address = (
                    server.accept()
                )


                print(
                    f"CLIENT CONNECTED: "
                    f"{address}"
                )


                data = connection.recv(
                    65536
                )


                if not data:

                    connection.close()

                    continue


                request = json.loads(
                    data.decode(
                        "utf-8"
                    )
                )


                print(
                    f"REQUEST: {request}"
                )


                # ==================================================
                # REQUEST OBJECT
                # ==================================================

                request_data = {

                    "request": request,

                    "response": None,

                    "event":
                        threading.Event()

                }


                # ==================================================
                # PUT REQUEST INTO WEBOTS QUEUE
                # ==================================================

                command_queue.put(
                    request_data
                )


                # ==================================================
                # WAIT FOR MAIN THREAD
                # ==================================================

                request_data[
                    "event"
                ].wait(
                    timeout=120
                )


                # ==================================================
                # GET RESPONSE
                # ==================================================

                response = request_data[
                    "response"
                ]


                if response is None:

                    response = {

                        "status": "error",

                        "message":
                            "Command timed out"

                    }


                # ==================================================
                # SEND RESPONSE
                # ==================================================

                connection.sendall(
                    json.dumps(
                        response
                    ).encode(
                        "utf-8"
                    )
                )


                print(
                    f"RESPONSE SENT: "
                    f"{response}"
                )


            except json.JSONDecodeError:

                print(
                    "ERROR: Invalid JSON received"
                )


                response = {

                    "status": "error",

                    "message":
                        "Invalid JSON"

                }


                if connection:

                    connection.sendall(
                        json.dumps(
                            response
                        ).encode(
                            "utf-8"
                        )
                    )


            except Exception as e:

                print(
                    "COMMAND SERVER ERROR: "
                    f"{e}"
                )


                try:

                    response = {

                        "status": "error",

                        "message": str(e)

                    }


                    if connection:

                        connection.sendall(
                            json.dumps(
                                response
                            ).encode(
                                "utf-8"
                            )
                        )


                except Exception:

                    pass


            finally:

                if connection:

                    try:

                        connection.close()

                    except Exception:

                        pass


    except Exception as e:

        print(
            f"SERVER START ERROR: {e}"
        )


    finally:

        try:

            server.close()

        except Exception:

            pass


# ============================================================
# START SERVER THREAD
# ============================================================

server_thread = threading.Thread(
    target=command_server,
    daemon=True
)

server_thread.start()


# ============================================================
# INITIAL CAMERA WAIT
# ============================================================

print(
    "WAITING FOR CAMERA..."
)


for _ in range(10):

    if robot.step(timestep) == -1:

        raise SystemExit


# ============================================================
# INITIAL IMAGE
# ============================================================

print(
    "CAPTURING INITIAL IMAGE..."
)

capture_image()


# ============================================================
# CONTROLLER READY
# ============================================================

print(
    "=============================================="
)

print(
    "CONTROLLER READY"
)

print(
    "ROBOT IS AT FIXED HOME POSITION"
)

print(
    f"HOME X = {HOME_X:.3f}"
)

print(
    f"HOME Z = {HOME_Z:.3f}"
)

print(
    "ROBOT WILL REMAIN STOPPED"
)

print(
    "WAITING FOR COMMAND..."
)

print(
    "=============================================="
)


# ============================================================
# MAIN WEBOTS LOOP
# ============================================================

while robot.step(timestep) != -1:

    # --------------------------------------------------------
    # Keep held object attached
    # --------------------------------------------------------

    update_held_object()


    # --------------------------------------------------------
    # Check command queue
    # --------------------------------------------------------

    try:

        request_data = (
            command_queue.get_nowait()
        )

    except queue.Empty:

        request_data = None


    # --------------------------------------------------------
    # Execute request
    # --------------------------------------------------------

    if request_data is not None:

        try:

            request = request_data[
                "request"
            ]


            response = execute_request(
                request
            )


            request_data[
                "response"
            ] = response


        except Exception as e:

            print(
                "REQUEST EXECUTION ERROR: "
                f"{e}"
            )


            request_data[
                "response"
            ] = {

                "status": "error",

                "message": str(e)

            }


        finally:

            request_data[
                "event"
            ].set()