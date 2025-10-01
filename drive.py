from gpiozero import PWMOutputDevice, OutputDevice, Device
import time


class BTS7960Motor:
    """Class to control a single BTS7960 motor driver"""
    def __init__(self, rpmh_pin, lpmh_pin, r_en_pin, l_en_pin):
        self.rpmh = PWMOutputDevice(rpmh_pin)  # Right PWM (forward)
        self.lpmh = PWMOutputDevice(lpmh_pin)  # Left PWM (reverse)
        self.r_en = OutputDevice(r_en_pin)     # Right enable
        self.l_en = OutputDevice(l_en_pin)     # Left enable
        
        # Enable both sides by default
        self.r_en.on()
        self.l_en.on()
    
    def forward(self, speed=0.5):
        """Drive motor forward at specified speed (0.0 to 1.0)"""
        self.lpmh.off()  # Turn off reverse
        # Cap PWM at 0.5
        capped_speed = min(speed, 0.5)
        self.rpmh.value = capped_speed
    
    def backward(self, speed=0.5):
        """Drive motor backward at specified speed (0.0 to 1.0)"""
        self.rpmh.off()  # Turn off forward
        # Cap PWM at 0.5
        capped_speed = min(speed, 0.5)
        self.lpmh.value = capped_speed
    
    def stop(self):
        """Stop the motor"""
        self.rpmh.off()
        self.lpmh.off()
    
    def cleanup(self):
        """Clean up GPIO resources"""
        self.stop()
        self.r_en.close()
        self.l_en.close()
        self.rpmh.close()
        self.lpmh.close()


class Drive:
    def __init__(self):
        # Define BTS7960 motor drivers for each wheel
        # Pin assignments based on your specification
        
        # Front Left Motor
        # RPMH 2 - black, LPMH 3 - white, R-EN 4 - grey, L-EN 17 - purple
        self.front_left_motor = BTS7960Motor(rpmh_pin=2, lpmh_pin=3, r_en_pin=4, l_en_pin=17)
        
        # Front Right Motor  
        # RPMH 27 - yellow, LPMH 22 - orange, R-EN 10 - red, L-EN 9 - brown
        self.front_right_motor = BTS7960Motor(rpmh_pin=27, lpmh_pin=22, r_en_pin=10, l_en_pin=9)
        
        # Rear Left Motor
        # RPMH 11 - green, LPMH 5 - blue, R-EN 6 - purple, L-EN 13 - grey
        self.rear_left_motor = BTS7960Motor(rpmh_pin=11, lpmh_pin=5, r_en_pin=6, l_en_pin=13)
        
        # Rear Right Motor
        # RPMH 19 - white, LPMH 26 - black, R-EN 16 - brown, L-EN 20 - red
        self.rear_right_motor = BTS7960Motor(rpmh_pin=19, lpmh_pin=26, r_en_pin=16, l_en_pin=20)
        
        # Store all motors for easy iteration
        self.motors = {
            'front_left': self.front_left_motor,
            'front_right': self.front_right_motor,
            'rear_left': self.rear_left_motor,
            'rear_right': self.rear_right_motor
        }
    
    def drive_wheel(self, wheel_name, speed=0.5, duration=2):
        """Drive a specific wheel for a given duration, or continuously if duration=None"""
        if wheel_name not in self.motors:
            print(f"Unknown wheel: {wheel_name}")
            return
        
        motor = self.motors[wheel_name]
        
        # Start the motor
        motor.forward(speed)
        
        if duration is not None:
            time.sleep(duration)
            # Stop the motor
            motor.stop()
        # If duration is None, motor keeps running until stop_all() is called
    
    def front_drive(self, left_speed=0.5, right_speed=0.5, duration=2):
        """Drive front wheels with individual speed control, or continuously if duration=None"""
        print(f"Driving front wheels - Left: {left_speed}, Right: {right_speed}")
        
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
            print("Front wheels stopped")
        # If duration is None, motors keep running until stop_all() is called
    
    def back_drive(self, left_speed=0.5, right_speed=0.5, duration=2):
        """Drive back wheels with individual speed control, or continuously if duration=None"""
        print(f"Driving back wheels - Left: {left_speed}, Right: {right_speed}")
        
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
            print("Back wheels stopped")
        # If duration is None, motors keep running until stop_all() is called
    
    def all_drive(self, front_left_speed=0.5, front_right_speed=0.5, rear_left_speed=0.5, rear_right_speed=0.5, duration=2):
        """Drive all wheels with individual speed control for each wheel, or continuously if duration=None"""
        print(f"Driving all wheels - FL: {front_left_speed}, FR: {front_right_speed}, RL: {rear_left_speed}, RR: {rear_right_speed}")
        
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
            print("All wheels stopped")
        # If duration is None, motors keep running until stop_all() is called
    
    def stop_all(self):
        """Stop all motors"""
        for motor in self.motors.values():
            motor.stop()
    
    def cleanup(self):
        """Clean up all motor resources"""
        for motor in self.motors.values():
            motor.cleanup()


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