#!/usr/bin/env python3
"""
Test power on timing - measures exact time for TV to turn on.
Run this and use a stopwatch to verify the timing.
"""

import asyncio
import sys
import time
from pyvizio import VizioAsync
from pyvizio.const import DEVICE_CLASS_TV, DEVICE_CLASS_SPEAKER

async def test_timing(host, token, device_type="tv"):
    """Test power on timing."""
    if device_type == "speaker":
        device_class = DEVICE_CLASS_SPEAKER
    else:
        device_class = DEVICE_CLASS_TV
    
    device = VizioAsync('test', host, 'Test', auth_token=token, device_type=device_class)
    
    print('=' * 60)
    print('Power ON Timing Test')
    print('=' * 60)
    print(f'Host: {host}')
    print(f'Token: {token[:10]}...')
    print('=' * 60)
    print()
    
    # Check initial state
    print('1. Checking initial state...')
    state = await device.get_power_state(log_api_exception=False)
    print(f'   Current state: {"ON" if state else "OFF"}')
    print()
    
    if state:
        print('2. TV is ON - turning OFF first...')
        await device.pow_off(log_api_exception=False)
        print('   Power off command sent')
        print('   Waiting 5 seconds for TV to turn off...')
        await asyncio.sleep(5)
        check = await device.get_power_state(log_api_exception=False)
        if check:
            print('   ⚠️  TV is still ON')
            print('   Please turn TV OFF manually using remote')
            print('   Then run this test again')
            return
        else:
            print('   ✓ TV is now OFF')
    else:
        print('2. TV is already OFF - ready to test')
    
    print()
    print('=' * 60)
    print('READY TO TEST')
    print('=' * 60)
    print()
    print('Starting in 3 seconds...')
    print('(Get your stopwatch ready!)')
    print()
    await asyncio.sleep(1)
    print('2...')
    await asyncio.sleep(1)
    print('1...')
    await asyncio.sleep(1)
    print()
    
    # Send power on and start timing
    print('3. Sending power ON command NOW!')
    print('   ⏱️  START YOUR STOPWATCH!')
    print()
    start_time = time.time()
    await device.pow_on(log_api_exception=False)
    command_time = time.time() - start_time
    print(f'   Command sent (took {command_time:.2f}s)')
    print()
    print('4. Checking state every 0.5 seconds...')
    print('   (Watch your TV screen and compare with stopwatch)')
    print()
    print('   Time    State')
    print('   ----    -----')
    
    # Check at frequent intervals
    turned_on = False
    for i in range(20):  # Check for up to 10 seconds
        await asyncio.sleep(0.5)
        elapsed = time.time() - start_time
        check = await device.get_power_state(log_api_exception=False)
        status = "ON" if check else "OFF"
        marker = "✓" if check and not turned_on else " "
        print(f'   {elapsed:5.1f}s  {status} {marker}')
        
        if check and not turned_on:
            turned_on = True
            print()
            print('=' * 60)
            print(f'✓ TV TURNED ON AFTER {elapsed:.1f} SECONDS')
            print('=' * 60)
            print()
            print('Please compare with your stopwatch:')
            print(f'  - Integration detected ON at: {elapsed:.1f} seconds')
            print('  - Your stopwatch shows: ? seconds')
            print('  - TV screen actually turned on at: ? seconds')
            break
    
    if not turned_on:
        print()
        print('⚠️  TV did not turn ON within 10 seconds')
        print('   Check if TV actually turned on')
    
    # Final confirmation
    print()
    final = await device.get_power_state(log_api_exception=False)
    print(f'5. Final state check: {"ON" if final else "OFF"}')
    
    if final:
        total_time = time.time() - start_time
        print()
        print('=' * 60)
        print('TEST COMPLETE')
        print('=' * 60)
        print(f'Total time from command to ON: {total_time:.1f} seconds')
        print()
        print('This timing will help us set the correct delay in the integration.')

async def main():
    """Main function."""
    if len(sys.argv) < 3:
        print("Usage: python test_power_on_timing.py <host> <token> [device_type]")
        print("Example: python test_power_on_timing.py 192.168.1.226 Zl4mv3bab9 tv")
        sys.exit(1)
    
    host = sys.argv[1]
    token = sys.argv[2]
    device_type = sys.argv[3].lower() if len(sys.argv) > 3 else "tv"
    
    await test_timing(host, token, device_type)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

