from gpiozero import Motor, PWMOutputDevice, OutputDevice, Device
import time


class Drive:
    def __init__(self):
        # Define GPIO pins for each motor
        # Front Left Motor
        self.front_left_motor = Motor(forward=22, backward=23)
        self.front_left_enable = PWMOutputDevice(20)
        
        # Front Right Motor
        self.front_right_motor = Motor(forward=27, backward=17)
        self.front_right_enable = PWMOutputDevice(4)
        
        # Rear Left Motor
        self.rear_left_motor = Motor(forward=24, backward=25)
        self.rear_left_enable = PWMOutputDevice(13)
        
        # Rear Right Motor
        self.rear_right_motor = Motor(forward=5, backward=6)
        self.rear_right_enable = PWMOutputDevice(19)
        
        # Store all motors and enables for easy iteration
        self.motors = {
            'front_left': (self.front_left_motor, self.front_left_enable),
            'front_right': (self.front_right_motor, self.front_right_enable),
            'rear_left': (self.rear_left_motor, self.rear_left_enable),
            'rear_right': (self.rear_right_motor, self.rear_right_enable)
        }
    
    def drive_wheel(self, wheel_name, speed=0.5, duration=2):
        """Drive a specific wheel for a given duration, or continuously if duration=None"""
        if wheel_name not in self.motors:
            print(f"Unknown wheel: {wheel_name}")
            return
        
        motor, enable = self.motors[wheel_name]
        
        # Start the motor
        motor.forward()
        enable.value = speed
        
        if duration is not None:
            time.sleep(duration)
            # Stop the motor
            enable.value = 0
            motor.stop()
        # If duration is None, motor keeps running until stop_all() is called
    
    def front_drive(self, left_speed=0.5, right_speed=0.5, duration=2):
        """Drive front wheels with individual speed control, or continuously if duration=None"""
        print(f"Driving front wheels - Left: {left_speed}, Right: {right_speed}")
        
        # Start front motors
        front_left_motor, front_left_enable = self.motors['front_left']
        front_right_motor, front_right_enable = self.motors['front_right']
        
        front_left_motor.forward()
        front_right_motor.forward()
        front_left_enable.value = left_speed
        front_right_enable.value = right_speed
        
        if duration is not None:
            time.sleep(duration)
            # Stop front motors
            front_left_enable.value = 0
            front_right_enable.value = 0
            front_left_motor.stop()
            front_right_motor.stop()
            print("Front wheels stopped")
        # If duration is None, motors keep running until stop_all() is called
    
    def back_drive(self, left_speed=0.5, right_speed=0.5, duration=2):
        """Drive back wheels with individual speed control, or continuously if duration=None"""
        print(f"Driving back wheels - Left: {left_speed}, Right: {right_speed}")
        
        # Start back motors
        rear_left_motor, rear_left_enable = self.motors['rear_left']
        rear_right_motor, rear_right_enable = self.motors['rear_right']
        
        rear_left_motor.forward()
        rear_right_motor.forward()
        rear_left_enable.value = left_speed
        rear_right_enable.value = right_speed
        
        if duration is not None:
            time.sleep(duration)
            # Stop back motors
            rear_left_enable.value = 0
            rear_right_enable.value = 0
            rear_left_motor.stop()
            rear_right_motor.stop()
            print("Back wheels stopped")
        # If duration is None, motors keep running until stop_all() is called
    
    def all_drive(self, front_left_speed=0.5, front_right_speed=0.5, rear_left_speed=0.5, rear_right_speed=0.5, duration=2):
        """Drive all wheels with individual speed control for each wheel, or continuously if duration=None"""
        print(f"Driving all wheels - FL: {front_left_speed}, FR: {front_right_speed}, RL: {rear_left_speed}, RR: {rear_right_speed}")
        
        # Start all motors
        for wheel_name, (motor, enable) in self.motors.items():
            motor.forward()
        
        # Set individual speeds
        self.motors['front_left'][1].value = front_left_speed
        self.motors['front_right'][1].value = front_right_speed
        self.motors['rear_left'][1].value = rear_left_speed
        self.motors['rear_right'][1].value = rear_right_speed
        
        if duration is not None:
            time.sleep(duration)
            # Stop all motors
            for wheel_name, (motor, enable) in self.motors.items():
                enable.value = 0
                motor.stop()
            print("All wheels stopped")
        # If duration is None, motors keep running until stop_all() is called
    
    def stop_all(self):
        """Stop all motors"""
        for wheel_name, (motor, enable) in self.motors.items():
            enable.value = 0
            motor.stop()


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
            drive.drive_wheel(wheel_name, speed=0.5, duration=2)
            time.sleep(1)  # Brief pause between wheels
        
        print("All wheel tests completed!")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    finally:
        # Ensure all motors are stopped
        drive.stop_all()