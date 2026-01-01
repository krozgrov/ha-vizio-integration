#!/usr/bin/env python3
"""
Test power on timing - measures how long after power off before power on works.
This helps determine optimal wait times for the integration.
"""

import asyncio
import sys
import time
from pyvizio import VizioAsync
from pyvizio.const import DEVICE_CLASS_TV, DEVICE_CLASS_SPEAKER

async def test_power_timing(host, token, device_type="tv"):
    """Test power on timing after power off."""
    if device_type == "speaker":
        device_class = DEVICE_CLASS_SPEAKER
    else:
        device_class = DEVICE_CLASS_TV
    
    device = VizioAsync('test', host, 'Test', auth_token=token, device_type=device_class)
    
    print('=' * 60)
    print('Power On Timing Test')
    print('=' * 60)
    print(f'Host: {host}')
    print(f'Token: {token[:10]}...')
    print('=' * 60)
    print()
    
    # Step 1: Check initial state
    print('1. Checking initial state...')
    initial_state = await device.get_power_state(log_api_exception=False)
    print(f'   Current state: {"ON" if initial_state else "OFF"}')
    print()
    
    # Step 2: Turn off if on
    if initial_state:
        print('2. TV is ON - turning OFF...')
        await device.pow_off(log_api_exception=False)
        print('   Power off command sent')
        
        # Wait for TV to turn off
        print('   Waiting for TV to turn off...')
        for i in range(10):
            await asyncio.sleep(1)
            state = await device.get_power_state(log_api_exception=False)
            if not state:
                print(f'   ✓ TV turned OFF after {i+1} seconds')
                break
            print(f'   Still ON... ({i+1}s)')
        else:
            print('   ⚠️  TV did not turn off within 10 seconds')
            print('   Continuing anyway...')
    else:
        print('2. TV is already OFF')
    
    print()
    print('=' * 60)
    print('READY TO TEST POWER ON')
    print('=' * 60)
    print()
    print('Starting in 3 seconds...')
    print('(Get your stopwatch ready!)')
    await asyncio.sleep(1)
    print('2...')
    await asyncio.sleep(1)
    print('1...')
    await asyncio.sleep(1)
    print()
    
    # Step 3: Send power on and measure time
    print('3. Sending power ON command NOW!')
    print('   ⏱️  START YOUR STOPWATCH!')
    print()
    start_time = time.time()
    
    await device.pow_on(log_api_exception=False)
    command_sent_time = time.time() - start_time
    print(f'   Command sent (took {command_sent_time:.2f}s)')
    print()
    
    print('4. Checking state every 2 seconds...')
    print('   (Watch your TV screen and compare with stopwatch)')
    print()
    print('   Time    State    Notes')
    print('   ----    -----    -----')
    
    # Check at intervals
    turned_on = False
    for i in range(15):  # Check for up to 30 seconds
        await asyncio.sleep(2)
        elapsed = time.time() - start_time
        try:
            check = await device.get_power_state(log_api_exception=False)
            status = "ON" if check else "OFF"
            
            if check and not turned_on:
                turned_on = True
                marker = "✓ TURNED ON!"
                print(f'   {elapsed:5.1f}s  {status:5s}  {marker}')
                print()
                print('=' * 60)
                print(f'✓ TV TURNED ON AFTER {elapsed:.1f} SECONDS')
                print('=' * 60)
                print()
                print('Timing breakdown:')
                print(f'  Command sent: {command_sent_time:.2f}s')
                print(f'  TV detected ON: {elapsed:.1f}s')
                print()
                print('Compare with your observations:')
                print(f'  - API detected ON at: {elapsed:.1f} seconds')
                print('  - Your stopwatch shows: ? seconds')
                print('  - TV screen actually turned on at: ? seconds')
                break
            else:
                marker = ""
                print(f'   {elapsed:5.1f}s  {status:5s}  {marker}')
        except Exception as e:
            print(f'   {elapsed:5.1f}s  ERROR   {e}')
    
    if not turned_on:
        print()
        print('⚠️  TV did not turn ON within 30 seconds')
        print('   Check if TV actually turned on')
    
    # Final confirmation
    print()
    final = await device.get_power_state(log_api_exception=False)
    print(f'5. Final state check: {"ON" if final else "OFF"}')
    
    if final:
        total_time = time.time() - start_time
        print()
        print('=' * 60)
        print(f'Total time from command to ON: {total_time:.1f} seconds')
        print('=' * 60)
        print()
        print('💡 Integration currently waits 8 seconds before first check')
        print(f'   This test shows: {total_time:.1f}s actual time')
        if total_time > 8:
            print(f'   ⚠️  Consider increasing wait time to {int(total_time) + 2}s')
        elif total_time < 6:
            print(f'   ✓ Current 8s wait should be sufficient')

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        print()
        print("Usage: python test_power_timing.py <host> <token> [device_type]")
        print()
        print("Arguments:")
        print("  host: IP address of the Vizio device")
        print("  token: Access token (required for TVs)")
        print("  device_type: 'tv' or 'speaker' (default: 'tv')")
        sys.exit(1)
    
    host = sys.argv[1]
    token = sys.argv[2]
    device_type = sys.argv[3].lower() if len(sys.argv) > 3 else "tv"
    
    asyncio.run(test_power_timing(host, token, device_type))

