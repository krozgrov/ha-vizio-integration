#!/usr/bin/env python3
"""
Test script to determine appropriate power on steps for Vizio devices.

This script tests different power on methods and configurations to help
determine the best approach for different Vizio TV models.

Usage:
    python test_power_on.py <host> <token> [device_type]

Arguments:
    host: IP address or hostname of the Vizio device
    token: Access token (leave empty for speakers, required for TVs)
    device_type: 'tv' or 'speaker' (default: 'tv')
"""

import asyncio
import sys
import time
from typing import Any

try:
    from pyvizio import VizioAsync
    from pyvizio.const import DEVICE_CLASS_SPEAKER, DEVICE_CLASS_TV
except ImportError:
    print("ERROR: pyvizio not installed. Install with: pip install pyvizio")
    sys.exit(1)


async def test_power_state(device: VizioAsync, label: str) -> bool | None:
    """Test getting power state."""
    try:
        print(f"  {label}: Getting power state...", end=" ")
        state = await device.get_power_state(log_api_exception=False)
        print(f"✓ Result: {state}")
        return state
    except Exception as e:
        print(f"✗ Error: {e}")
        return None


async def test_power_on_method(
    device: VizioAsync, method_name: str, delay: float = 0.5, verify: bool = True
) -> bool:
    """Test a power on method."""
    print(f"\n  Testing: {method_name}")
    print(f"    Sending power on command...", end=" ")
    
    try:
        await device.pow_on(log_api_exception=False)
        print("✓ Command sent")
    except Exception as e:
        print(f"✗ Error sending command: {e}")
        return False
    
    # Wait for device to respond
    if delay > 0:
        print(f"    Waiting {delay}s for device to respond...")
        await asyncio.sleep(delay)
    
    # Verify power state
    if verify:
        print("    Verifying power state...", end=" ")
        try:
            power_state = await device.get_power_state(log_api_exception=False)
            if power_state:
                print(f"✓ Device is ON")
                return True
            else:
                print(f"✗ Device is still OFF")
                return False
        except Exception as e:
            print(f"✗ Error checking state: {e}")
            return False
    
    return True


async def test_multiple_attempts(
    device: VizioAsync, num_attempts: int = 3, delay_between: float = 1.0
) -> bool:
    """Test multiple power on attempts."""
    print(f"\n  Testing: Multiple attempts ({num_attempts} attempts, {delay_between}s between)")
    
    for attempt in range(num_attempts):
        print(f"    Attempt {attempt + 1}/{num_attempts}...", end=" ")
        try:
            await device.pow_on(log_api_exception=False)
            print("✓ Command sent")
            
            if attempt < num_attempts - 1:
                await asyncio.sleep(delay_between)
        except Exception as e:
            print(f"✗ Error: {e}")
            if attempt < num_attempts - 1:
                await asyncio.sleep(delay_between)
            continue
    
    # Wait a bit longer after all attempts
    print(f"    Waiting 2s after all attempts...")
    await asyncio.sleep(2.0)
    
    # Check final state
    print("    Checking final power state...", end=" ")
    try:
        power_state = await device.get_power_state(log_api_exception=False)
        if power_state:
            print(f"✓ Device is ON")
            return True
        else:
            print(f"✗ Device is still OFF")
            return False
    except Exception as e:
        print(f"✗ Error checking state: {e}")
        return False


async def test_with_verification_delays(
    device: VizioAsync, delays: list[float] = [0.5, 1.0, 2.0]
) -> bool:
    """Test power on with different verification delays."""
    print(f"\n  Testing: Power on with verification delays {delays}")
    
    try:
        await device.pow_on(log_api_exception=False)
        print("    ✓ Power on command sent")
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False
    
    for delay in delays:
        print(f"    Checking after {delay}s delay...", end=" ")
        await asyncio.sleep(delay)
        try:
            power_state = await device.get_power_state(log_api_exception=False)
            if power_state:
                print(f"✓ Device is ON (responded after {delay}s)")
                return True
            else:
                print("OFF")
        except Exception as e:
            print(f"Error: {e}")
    
    print("    ✗ Device did not turn on with any delay")
    return False


async def main() -> None:
    """Main test function."""
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    host = sys.argv[1]
    token = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else None
    device_type = sys.argv[3].lower() if len(sys.argv) > 3 else "tv"
    
    if device_type == "speaker":
        device_class = DEVICE_CLASS_SPEAKER
    else:
        device_class = DEVICE_CLASS_TV
    
    print("=" * 60)
    print("Vizio Power On Test Script")
    print("=" * 60)
    print(f"Host: {host}")
    print(f"Device Type: {device_type}")
    print(f"Token: {'***' if token else 'Not required (speaker)'}")
    print("=" * 60)
    
    # Create device instance
    device = VizioAsync(
        "test-script",
        host,
        "Test Device",
        auth_token=token,
        device_type=device_class,
    )
    
    # Initial state check
    print("\n1. Initial Power State Check")
    print("-" * 60)
    initial_state = await test_power_state(device, "Initial state")
    
    if initial_state:
        print("\n⚠️  Device is already ON. Turning it off first...")
        try:
            await device.pow_off(log_api_exception=False)
            print("    Power off command sent, waiting 3s...")
            await asyncio.sleep(3.0)
            # Verify it's off
            power_state = await device.get_power_state(log_api_exception=False)
            if power_state:
                print("    Warning: Device still appears to be ON")
            else:
                print("    ✓ Device is now OFF - ready to test power on")
        except Exception as e:
            print(f"    Error turning off device: {e}")
            print("    Continuing with test anyway...")
    else:
        print("\n✓ Device is OFF - ready to test power on")
    
    # Test different methods
    print("\n" + "=" * 60)
    print("2. Testing Power On Methods")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Single attempt with immediate verification
    results["single_immediate"] = await test_power_on_method(
        device, "Single attempt, immediate verification", delay=0.5, verify=True
    )
    
    # Turn off before next test
    if results["single_immediate"]:
        print("\n    Turning device off for next test...")
        await device.pow_off(log_api_exception=False)
        await asyncio.sleep(2)
    
    # Test 2: Single attempt with longer delay
    results["single_delayed"] = await test_power_on_method(
        device, "Single attempt, 2s delay", delay=2.0, verify=True
    )
    
    # Turn off before next test
    if results["single_delayed"]:
        print("\n    Turning device off for next test...")
        await device.pow_off(log_api_exception=False)
        await asyncio.sleep(2)
    
    # Test 3: Multiple attempts
    results["multiple_attempts"] = await test_multiple_attempts(device, num_attempts=3, delay_between=1.0)
    
    # Turn off before next test
    if results["multiple_attempts"]:
        print("\n    Turning device off for next test...")
        await device.pow_off(log_api_exception=False)
        await asyncio.sleep(2)
    
    # Test 4: Power on with progressive verification delays
    results["progressive_delays"] = await test_with_verification_delays(
        device, delays=[0.5, 1.0, 2.0, 3.0]
    )
    
    # Summary
    print("\n" + "=" * 60)
    print("3. Test Results Summary")
    print("=" * 60)
    
    for method, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"  {method:25s}: {status}")
    
    successful_methods = [m for m, s in results.items() if s]
    
    if successful_methods:
        print(f"\n✓ Successful methods: {', '.join(successful_methods)}")
        print("\nRecommendation: Use the first successful method for your device.")
    else:
        print("\n✗ No methods succeeded. Possible issues:")
        print("  - Device may not support power on via SmartCast API")
        print("  - Device may require Wake-on-LAN (WOL)")
        print("  - Network connectivity issues")
        print("  - Incorrect access token")
    
    print("\n" + "=" * 60)
    print("Test Complete")
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

