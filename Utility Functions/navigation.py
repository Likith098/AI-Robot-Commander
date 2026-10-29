import math
from config import (
    ROBOT_SPEED,
    ROBOT_ANGULAR_SPEED,
    HOME_X,
    HOME_Y,
    HOME_ANGLE,
    REACH_THRESHOLD,
    MOVEMENT_TIMEOUT
)
from utils import setup_logger, calculate_distance, calculate_angle

logger = setup_logger(__name__)

class Navigator:
    """
    Handles robot navigation and movement
    """
    
    def __init__(self, robot_controller=None):
        """
        Initialize navigator
        
        Args:
            robot_controller: Reference to Webots robot controller
        """
        self.robot = robot_controller
        self.current_x = HOME_X
        self.current_y = HOME_Y
        self.current_angle = HOME_ANGLE
        self.is_moving = False
        
        logger.info("✓ Navigator initialized")

    def update_position(self, x, y, angle=None):
        """
        Update robot's current position
        
        Args:
            x: X coordinate
            y: Y coordinate
            angle: Rotation angle (optional)
        """
        self.current_x = x
        self.current_y = y
        if angle is not None:
            self.current_angle = angle
        logger.info(f"📍 Position updated: ({x:.2f}, {y:.2f}), Angle: {angle:.2f}" if angle else f"📍 Position updated: ({x:.2f}, {y:.2f})")

    def go_to(self, target_x, target_y):
        """
        Navigate robot to target coordinates
        
        Args:
            target_x: Target X coordinate
            target_y: Target Y coordinate
        
        Returns:
            True if reached, False otherwise
        """
        logger.info(f"🎯 Navigating to ({target_x:.2f}, {target_y:.2f})")
        
        try:
            self.is_moving = True
            
            # Calculate distance and angle
            distance = calculate_distance(
                self.current_x, self.current_y,
                target_x, target_y
            )
            target_angle = calculate_angle(
                self.current_x, self.current_y,
                target_x, target_y
            )
            
            logger.info(f"Distance to target: {distance:.2f}m")
            logger.info(f"Target angle: {target_angle:.2f} rad")
            
            # Step 1: Rotate to face target
            angle_diff = self._normalize_angle(target_angle - self.current_angle)
            logger.info(f"🔄 Rotating {angle_diff:.2f} radians...")
            self.rotate(angle_diff)
            
            # Step 2: Move forward
            logger.info(f"📍 Moving forward {distance:.2f}m...")
            self.move_forward(distance)
            
            # Update position
            self.current_x = target_x
            self.current_y = target_y
            self.current_angle = target_angle
            
            self.is_moving = False
            logger.info(f"✓ Reached target!")
            return True
        
        except Exception as e:
            logger.error(f"Error in go_to: {e}")
            self.is_moving = False
            return False

    def move_forward(self, distance):
        """
        Move robot forward by specified distance
        
        Args:
            distance: Distance to move (meters)
        """
        try:
            if self.robot is None:
                logger.warning("⚠ No robot controller, simulating movement")
                logger.info(f"[SIM] Moving forward {distance:.2f}m")
                return
            
            # Calculate time needed
            time_needed = distance / ROBOT_SPEED
            logger.info(f"⏱ Moving for {time_needed:.2f} seconds")
            
            # Get left and right motors (Updated device names for E-puck)
            left_motor = self.robot.getDevice("left wheel motor") or self.robot.getDevice("left_motor")
            right_motor = self.robot.getDevice("right wheel motor") or self.robot.getDevice("right_motor")
            
            if left_motor is None or right_motor is None:
                logger.error("❌ Motors not found!")
                return
            
            # Set to velocity control mode
            left_motor.setPosition(float('inf'))
            right_motor.setPosition(float('inf'))

            # Set velocity
            left_motor.setVelocity(ROBOT_SPEED)
            right_motor.setVelocity(ROBOT_SPEED)
            
            # Wait
            start_time = self.robot.getTime()
            while self.robot.getTime() - start_time < time_needed:
                if self.robot.step(100) == -1:
                    break
            
            # Stop
            left_motor.setVelocity(0)
            right_motor.setVelocity(0)
            
            logger.info(f"✓ Forward movement complete")
        
        except Exception as e:
            logger.error(f"Error in move_forward: {e}")

    def rotate(self, angle):
        """
        Rotate robot by specified angle
        
        Args:
            angle: Angle to rotate (radians)
        """
        try:
            if self.robot is None:
                logger.warning("⚠ No robot controller, simulating rotation")
                logger.info(f"[SIM] Rotating {angle:.2f} radians")
                return
            
            # Calculate time needed
            time_needed = abs(angle) / ROBOT_ANGULAR_SPEED
            logger.info(f"⏱ Rotating for {time_needed:.2f} seconds")
            
            # Get motors (Updated device names for E-puck)
            left_motor = self.robot.getDevice("left wheel motor") or self.robot.getDevice("left_motor")
            right_motor = self.robot.getDevice("right wheel motor") or self.robot.getDevice("right_motor")
            
            if left_motor is None or right_motor is None:
                logger.error("❌ Motors not found!")
                return
            
            # Set to velocity control mode
            left_motor.setPosition(float('inf'))
            right_motor.setPosition(float('inf'))

            # Set velocity (opposite directions for rotation)
            if angle > 0:  # Rotate left
                left_motor.setVelocity(-ROBOT_ANGULAR_SPEED)
                right_motor.setVelocity(ROBOT_ANGULAR_SPEED)
            else:  # Rotate right
                left_motor.setVelocity(ROBOT_ANGULAR_SPEED)
                right_motor.setVelocity(-ROBOT_ANGULAR_SPEED)
            
            # Wait
            start_time = self.robot.getTime()
            while self.robot.getTime() - start_time < time_needed:
                if self.robot.step(100) == -1:
                    break
            
            # Stop
            left_motor.setVelocity(0)
            right_motor.setVelocity(0)
            
            self.current_angle += angle
            logger.info(f"✓ Rotation complete")
        
        except Exception as e:
            logger.error(f"Error in rotate: {e}")

    def return_home(self):
        """Return robot to home position"""
        logger.info("🏠 Returning to home position...")
        return self.go_to(HOME_X, HOME_Y)

    def _normalize_angle(self, angle):
        """
        Normalize angle to [-π, π]
        
        Args:
            angle: Angle in radians
        
        Returns:
            Normalized angle
        """
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle