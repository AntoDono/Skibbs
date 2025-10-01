from gpiozero import PWMOutputDevice, OutputDevice, Device
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BTS7960Motor:
    """Class to control a single BTS7960 motor driver"""
    def __init__(self, rpmh_pin, lpmh_pin, r_en_pin, l_en_pin):
        self.rpmh = None
        self.lpmh = None
        self.r_en = None
        self.l_en = None
        self.initialized = False
        
        try:
            logger.info(f"Initializing motor with pins: RPMH={rpmh_pin}, LPMH={lpmh_pin}, R_EN={r_en_pin}, L_EN={l_en_pin}")
            self.rpmh = PWMOutputDevice(rpmh_pin)  # Right PWM (forward)
            self.lpmh = PWMOutputDevice(lpmh_pin)  # Left PWM (reverse)
            self.r_en = OutputDevice(r_en_pin)     # Right enable
            self.l_en = OutputDevice(l_en_pin)     # Left enable
            
            # Enable both sides by default
            self.r_en.on()
            self.l_en.on()
            self.initialized = True
            logger.info(f"Motor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize motor: {e}")
            self.cleanup()
            raise
    
    def forward(self, speed=0.5):
        """Drive motor forward at specified speed (0.0 to 1.0)"""
        if not self.initialized:
            logger.warning("Motor not initialized, cannot drive forward")
            return
            
        try:
            self.lpmh.off()  # Turn off reverse
            # Cap PWM at 0.5
            capped_speed = min(speed, 0.5)
            self.rpmh.value = capped_speed
        except Exception as e:
            logger.error(f"Error driving forward: {e}")
    
    def backward(self, speed=0.5):
        """Drive motor backward at specified speed (0.0 to 1.0)"""
        if not self.initialized:
            logger.warning("Motor not initialized, cannot drive backward")
            return
            
        try:
            self.rpmh.off()  # Turn off forward
            # Cap PWM at 0.5
            capped_speed = min(speed, 0.5)
            self.lpmh.value = capped_speed
        except Exception as e:
            logger.error(f"Error driving backward: {e}")
    
    def stop(self):
        """Stop the motor"""
        if not self.initialized:
            return
            
        try:
            if self.rpmh:
                self.rpmh.off()
            if self.lpmh:
                self.lpmh.off()
        except Exception as e:
            logger.error(f"Error stopping motor: {e}")
    
    def cleanup(self):
        """Clean up GPIO resources"""
        try:
            self.stop()
            if self.r_en:
                self.r_en.close()
            if self.l_en:
                self.l_en.close()
            if self.rpmh:
                self.rpmh.close()
            if self.lpmh:
                self.lpmh.close()
            self.initialized = False
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


class Drive:
    def __init__(self):
        # Define BTS7960 motor drivers for each wheel
        # Pin assignments based on your specification
        self.motors = {}
        self.initialized_motors = []
        
        try:
            logger.info("Initializing Drive system...")
            
            # Front Left Motor (flipped pins for correct direction)
            # LPMH 2 - black, RPMH 3 - white, R-EN 4 - grey, L-EN 17 - purple
            logger.info("Initializing front left motor...")
            self.front_left_motor = BTS7960Motor(rpmh_pin=3, lpmh_pin=2, r_en_pin=4, l_en_pin=17)
            self.motors['front_left'] = self.front_left_motor
            self.initialized_motors.append('front_left')
            
            # Front Right Motor  
            # RPMH 27 - yellow, LPMH 22 - orange, R-EN 10 - red, L-EN 9 - brown
            logger.info("Initializing front right motor...")
            self.front_right_motor = BTS7960Motor(rpmh_pin=27, lpmh_pin=22, r_en_pin=10, l_en_pin=9)
            self.motors['front_right'] = self.front_right_motor
            self.initialized_motors.append('front_right')
            
            # Rear Left Motor (flipped pins for correct direction)
            # LPMH 11 - green, RPMH 5 - blue, R-EN 6 - purple, L-EN 13 - grey
            logger.info("Initializing rear left motor...")
            self.rear_left_motor = BTS7960Motor(rpmh_pin=5, lpmh_pin=11, r_en_pin=6, l_en_pin=13)
            self.motors['rear_left'] = self.rear_left_motor
            self.initialized_motors.append('rear_left')
            
            # Rear Right Motor
            # RPMH 19 - white, LPMH 26 - black, R-EN 16 - brown, L-EN 20 - red
            logger.info("Initializing rear right motor...")
            self.rear_right_motor = BTS7960Motor(rpmh_pin=19, lpmh_pin=26, r_en_pin=16, l_en_pin=20)
            self.motors['rear_right'] = self.rear_right_motor
            self.initialized_motors.append('rear_right')
            
            logger.info(f"Drive system initialized with {len(self.initialized_motors)} motors")
            
        except Exception as e:
            logger.error(f"Failed to initialize Drive system: {e}")
            self.cleanup()
            raise
    
    def drive_wheel(self, wheel_name, speed=0.5, duration=2):
        """Drive a specific wheel for a given duration, or continuously if duration=None"""
        if wheel_name not in self.motors:
            logger.warning(f"Unknown wheel: {wheel_name}")
            return
        
        if wheel_name not in self.initialized_motors:
            logger.warning(f"Wheel {wheel_name} not initialized, cannot drive")
            return
        
        motor = self.motors[wheel_name]
        
        try:
            # Start the motor
            motor.forward(speed)
            
            if duration is not None:
                time.sleep(duration)
                # Stop the motor
                motor.stop()
            # If duration is None, motor keeps running until stop_all() is called
        except Exception as e:
            logger.error(f"Error driving wheel {wheel_name}: {e}")
    
    def front_drive(self, left_speed=0.5, right_speed=0.5, duration=2):
        """Drive front wheels with individual speed control, or continuously if duration=None"""
        
        # Start front motors
        front_left_motor = self.motors['front_left']
        front_right_motor = self.motors['front_right']
        
        front_left_motor.forward(left_speed)
        front_right_motor.forward(right_speed)
        
        if duration is not None:
            time.sleep(duration)
            # Stop front motors
            front_left_motor.stop()
            front_right_motor.stop()
        # If duration is None, motors keep running until stop_all() is called
    
    def back_drive(self, left_speed=0.5, right_speed=0.5, duration=2):
        """Drive back wheels with individual speed control, or continuously if duration=None"""
        
        # Start back motors
        rear_left_motor = self.motors['rear_left']
        rear_right_motor = self.motors['rear_right']
        
        rear_left_motor.forward(left_speed)
        rear_right_motor.forward(right_speed)
        
        if duration is not None:
            time.sleep(duration)
            # Stop back motors
            rear_left_motor.stop()
            rear_right_motor.stop()
        # If duration is None, motors keep running until stop_all() is called
    
    def all_drive(self, front_left_speed=0.5, front_right_speed=0.5, rear_left_speed=0.5, rear_right_speed=0.5, duration=2):
        """Drive all wheels with individual speed control for each wheel, or continuously if duration=None"""
        
        # Start all motors with individual speeds
        self.motors['front_left'].forward(front_left_speed)
        self.motors['front_right'].forward(front_right_speed)
        self.motors['rear_left'].forward(rear_left_speed)
        self.motors['rear_right'].forward(rear_right_speed)
        
        if duration is not None:
            time.sleep(duration)
            # Stop all motors
            for motor in self.motors.values():
                motor.stop()
        # If duration is None, motors keep running until stop_all() is called
    
    def all_drive_backward(self, front_left_speed=0.5, front_right_speed=0.5, rear_left_speed=0.5, rear_right_speed=0.5, duration=2):
        """Drive all wheels backward with individual speed control for each wheel, or continuously if duration=None"""
        
        # Start all motors with individual speeds in reverse
        self.motors['front_left'].backward(front_left_speed)
        self.motors['front_right'].backward(front_right_speed)
        self.motors['rear_left'].backward(rear_left_speed)
        self.motors['rear_right'].backward(rear_right_speed)
        
        if duration is not None:
            time.sleep(duration)
            # Stop all motors
            for motor in self.motors.values():
                motor.stop()
        # If duration is None, motors keep running until stop_all() is called
    
    def stop_all(self):
        """Stop all motors"""
        for motor_name, motor in self.motors.items():
            if motor_name in self.initialized_motors:
                try:
                    motor.stop()
                except Exception as e:
                    logger.error(f"Error stopping {motor_name}: {e}")
    
    def cleanup(self):
        """Clean up all motor resources"""
        logger.info("Cleaning up Drive system...")
        for motor_name, motor in self.motors.items():
            if motor_name in self.initialized_motors:
                try:
                    motor.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up {motor_name}: {e}")
        
        # Clear the pin factory to release all GPIO resources
        try:
            if Device.pin_factory is not None:
                Device.pin_factory.reset()
                logger.info("GPIO pin factory reset")
        except Exception as e:
            logger.error(f"Error resetting GPIO pin factory: {e}")


if __name__ == "__main__":
    # Clear GPIO pins cache before initialization
    print("Clearing GPIO pins cache...")
    try:
        if Device.pin_factory is not None:
            Device.pin_factory.reset()
        else:
            print("Pin factory not initialized, skipping reset")
    except Exception as e:
        print(f"GPIO reset warning: {e}")
    
    # Create drive instance
    drive = Drive()
    
    try:
        print("Testing each wheel individually...")
        
        # Test each wheel one by one
        for wheel_name in drive.motors.keys():
            print(f"Driving {wheel_name}...")
            drive.drive_wheel(wheel_name, speed=0.5, duration=2)
            
        time.sleep(1)  # Brief pause between wheels
        
        print("All wheel tests completed!")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    finally:
        # Ensure all motors are stopped and cleaned up
        drive.stop_all()
        drive.cleanup()
        print("GPIO cleanup completed")