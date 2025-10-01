#!/usr/bin/env python3
"""
GPIO Test Script for Skibbs Robot
This script tests GPIO pins individually to identify which ones cause bus errors
"""

import sys
import time
import logging
from gpiozero import PWMOutputDevice, OutputDevice, Device

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_single_pin(pin_number, pin_type="output"):
    """Test a single GPIO pin"""
    device = None
    try:
        logger.info(f"Testing pin {pin_number} as {pin_type}")
        
        if pin_type == "pwm":
            device = PWMOutputDevice(pin_number)
            device.value = 0.1  # Low PWM value
            time.sleep(0.5)
            device.off()
        else:
            device = OutputDevice(pin_number)
            device.on()
            time.sleep(0.5)
            device.off()
        
        logger.info(f"Pin {pin_number} test successful")
        return True
        
    except Exception as e:
        logger.error(f"Pin {pin_number} test failed: {e}")
        return False
    finally:
        if device:
            try:
                device.close()
            except:
                pass

def test_motor_pins():
    """Test all motor pins individually"""
    # Pin assignments from your drive.py
    motor_pins = {
        'front_left': {
            'rpmh': 2, 'lpmh': 3, 'r_en': 4, 'l_en': 17
        },
        'front_right': {
            'rpmh': 27, 'lpmh': 22, 'r_en': 10, 'l_en': 9
        },
        'rear_left': {
            'rpmh': 11, 'lpmh': 5, 'r_en': 6, 'l_en': 13
        },
        'rear_right': {
            'rpmh': 19, 'lpmh': 26, 'r_en': 16, 'l_en': 20
        }
    }
    
    results = {}
    
    for motor_name, pins in motor_pins.items():
        logger.info(f"\n=== Testing {motor_name} motor ===")
        results[motor_name] = {}
        
        for pin_type, pin_num in pins.items():
            pin_type_str = "pwm" if pin_type in ['rpmh', 'lpmh'] else "output"
            success = test_single_pin(pin_num, pin_type_str)
            results[motor_name][pin_type] = success
            
            if not success:
                logger.error(f"FAILED: {motor_name} {pin_type} (pin {pin_num})")
            else:
                logger.info(f"PASSED: {motor_name} {pin_type} (pin {pin_num})")
            
            time.sleep(0.1)  # Small delay between tests
    
    return results

def main():
    logger.info("Starting GPIO pin testing...")
    logger.info("This will test each motor pin individually to identify problematic pins")
    
    try:
        # Clear any existing GPIO state
        logger.info("Clearing GPIO pin factory...")
        if Device.pin_factory is not None:
            Device.pin_factory.reset()
        
        # Test all motor pins
        results = test_motor_pins()
        
        # Print summary
        logger.info("\n=== TEST SUMMARY ===")
        for motor_name, pins in results.items():
            logger.info(f"\n{motor_name.upper()}:")
            for pin_type, success in pins.items():
                status = "PASS" if success else "FAIL"
                logger.info(f"  {pin_type}: {status}")
        
        # Check for any failures
        all_passed = all(
            all(pins.values()) for pins in results.values()
        )
        
        if all_passed:
            logger.info("\n✅ All GPIO pins tested successfully!")
        else:
            logger.warning("\n⚠️  Some GPIO pins failed testing")
            logger.warning("Check the failed pins above - these may be causing the bus error")
            
    except Exception as e:
        logger.error(f"Test script failed: {e}")
        return 1
    
    finally:
        # Final cleanup
        try:
            if Device.pin_factory is not None:
                Device.pin_factory.reset()
                logger.info("GPIO cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
