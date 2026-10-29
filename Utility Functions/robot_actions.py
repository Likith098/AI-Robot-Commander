from utils import setup_logger


logger = setup_logger(__name__)


class RobotActions:
    """
    Handles simulated object manipulation for the e-puck.

    The e-puck does not have a physical gripper, so picking up
    an object is simulated using the Webots Supervisor controller.
    """

    def __init__(self, robot_controller=None):
        """
        Initialize robot actions.

        Args:
            robot_controller: Reference to the Webots Supervisor controller.
        """

        self.robot = robot_controller

        self.gripper_open = True
        self.holding_object = False
        self.held_object_name = None

        logger.info("✓ Robot Actions initialized")


    def open_gripper(self):
        """
        Simulate opening the gripper.

        There is no physical gripper on the e-puck.
        """

        logger.info("🔓 Simulated gripper opened")

        self.gripper_open = True


    def close_gripper(self):
        """
        Simulate closing the gripper.
        """

        logger.info("🔒 Simulated gripper closed")

        self.gripper_open = False


    def pick_up_object(self, object_name):
        """
        Simulate picking up an object.

        The actual object attachment is handled by the
        Webots Supervisor controller.
        """

        try:

            logger.info(f"🧲 Attempting to pick up {object_name}...")


            if self.robot is None:

                logger.warning(
                    "⚠ No robot controller available"
                )

                return False


            # Open simulated gripper
            self.open_gripper()


            # Find the object in Webots
            object_node = self.robot.getFromDef(object_name)


            if object_node is None:

                logger.error(
                    f"❌ Object '{object_name}' not found in Webots"
                )

                return False


            # Store object state
            self.holding_object = True
            self.held_object_name = object_name


            # Close simulated gripper
            self.close_gripper()


            logger.info(
                f"✓ Successfully picked up {object_name}"
            )

            return True


        except Exception as e:

            logger.error(
                f"Error picking up object: {e}"
            )

            return False


    def drop_object(self):
        """
        Simulate releasing the currently held object.
        """

        try:

            if not self.holding_object:

                logger.warning(
                    "⚠ Robot is not holding an object"
                )

                return False


            object_name = self.held_object_name


            logger.info(
                f"📦 Releasing {object_name}..."
            )


            # Open simulated gripper
            self.open_gripper()


            # Clear holding state
            self.holding_object = False
            self.held_object_name = None


            logger.info(
                f"✓ Released {object_name}"
            )

            return True


        except Exception as e:

            logger.error(
                f"Error dropping object: {e}"
            )

            return False


    def get_status(self):
        """
        Get current robot action status.
        """

        return {
            "gripper_open": self.gripper_open,
            "holding_object": self.holding_object,
            "held_object": self.held_object_name
        }