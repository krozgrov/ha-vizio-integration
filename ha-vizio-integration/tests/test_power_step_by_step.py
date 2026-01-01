#!/usr/bin/env python3
"""
Step-by-step power on/off test for Vizio devices.
Runs through power commands sequentially with detailed output.
"""

import asyncio
import sys
from pyvizio import VizioAsync
from pyvizio.const import DEVICE_CLASS_TV, DEVICE_CLASS_SPEAKER

async def check_state(device, label=""):
    """Check and display power state."""
    try:
        state = await device.get_power_state(log_api_exception=False)
        status = "ON" if state else "OFF"
        print(f"{label}Power state: {status}")
        return state
    except Exception as e:
        print(f"{label}Error checking state: {e}")
        return None

async def power_off_step(device):
    """Step through power off process."""
    print("\n" + "=" * 60)
    print("STEP 1: POWER OFF")
    print("=" * 60)
    
    # Check initial state
    print("\n1. Checking initial state...")
    initial = await check_state(device)
    
    if not initial:
        print("   Device is already OFF, skipping power off test")
        return True
    
    # Send power off command
    print("\n2. Sending power OFF command...")
    try:
        await device.pow_off(log_api_exception=False)
        print("   ✓ Command sent successfully")
    except Exception as e:
        print(f"   ✗ Error sending command: {e}")
        return False
    
    # Check state at intervals
    print("\n3. Checking state after power off command...")
    for delay in [0.5, 1.0, 2.0, 3.0, 5.0]:
        await asyncio.sleep(delay - (0.5 if delay > 0.5 else 0))
        state = await check_state(device, f"   After {delay}s: ")
        if not state:
            print(f"   ✓ Device turned OFF after {delay}s")
            return True
    
    # Final check
    final = await check_state(device, "\n4. Final state: ")
    if not final:
        print("   ✓ Device is OFF")
        return True
    else:
        print("   ⚠️  Device is still ON")
        return False

async def power_on_step(device):
    """Step through power on process."""
    print("\n" + "=" * 60)
    print("STEP 2: POWER ON")
    print("=" * 60)
    
    # Check initial state
    print("\n1. Checking initial state...")
    initial = await check_state(device)
    
    if initial:
        print("   Device is already ON, skipping power on test")
        return True
    
    # Send power on command
    print("\n2. Sending power ON command...")
    try:
        await device.pow_on(log_api_exception=False)
        print("   ✓ Command sent successfully")
    except Exception as e:
        print(f"   ✗ Error sending command: {e}")
        return False
    
    # Check state at intervals
    print("\n3. Checking state after power on command...")
    for delay in [0.1, 0.3, 0.5, 1.0, 2.0, 3.0, 5.0]:
        await asyncio.sleep(delay - (0.1 if delay > 0.1 else 0))
        state = await check_state(device, f"   After {delay}s: ")
        if state:
            print(f"   ✓ Device turned ON after {delay}s")
            return True
    
    # Final check
    final = await check_state(device, "\n4. Final state: ")
    if final:
        print("   ✓ Device is ON")
        return True
    else:
        print("   ✗ Device did not turn ON")
        return False

async def main():
    """Main test function."""
    if len(sys.argv) < 3:
        print("Usage: python test_power_step_by_step.py <host> <token> [device_type]")
        print("Example: python test_power_step_by_step.py 192.168.1.226 Zg777hqj9g tv")
        sys.exit(1)
    
    host = sys.argv[1]
    token = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else None
    device_type = sys.argv[3].lower() if len(sys.argv) > 3 else "tv"
    
    if device_type == "speaker":
        device_class = DEVICE_CLASS_SPEAKER
    else:
        device_class = DEVICE_CLASS_TV
    
    print("=" * 60)
    print("Vizio Power Control - Step by Step Test")
    print("=" * 60)
    print(f"Host: {host}")
    print(f"Device Type: {device_type}")
    print(f"Token: {'***' if token else 'Not required'}")
    print("=" * 60)
    
    # Create device instance
    device = VizioAsync(
        "test-script",
        host,
        "Test Device",
        auth_token=token,
        device_type=device_class,
    )
    
    # Initial state
    print("\nInitial device state:")
    initial_state = await check_state(device)
    print()
    
    # Run power off test
    power_off_result = await power_off_step(device)
    
    # Wait a bit between tests
    if power_off_result:
        print("\nWaiting 3 seconds before power on test...")
        await asyncio.sleep(3)
    
    # Run power on test
    power_on_result = await power_on_step(device)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Power OFF: {'✓ SUCCESS' if power_off_result else '✗ FAILED'}")
    print(f"Power ON:  {'✓ SUCCESS' if power_on_result else '✗ FAILED'}")
    print("=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

