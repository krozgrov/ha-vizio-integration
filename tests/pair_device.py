#!/usr/bin/env python3
"""
Pair with a Vizio device to get a new access token.
"""

import asyncio
import sys
from pyvizio import VizioAsync
from pyvizio.const import DEVICE_CLASS_TV, DEVICE_CLASS_SPEAKER

async def pair_device(host, device_type="tv", pin=None, pairing_token=None, challenge_type=None):
    """Pair with device and get access token."""
    if device_type == "speaker":
        device_class = DEVICE_CLASS_SPEAKER
    else:
        device_class = DEVICE_CLASS_TV
    
    print("=" * 60)
    print("Vizio Device Pairing")
    print("=" * 60)
    print(f"Host: {host}")
    print(f"Device Type: {device_type}")
    if pin:
        print(f"PIN: {pin}")
    if pairing_token:
        print(f"Pairing Token: {pairing_token}")
    print("=" * 60)
    print()
    
    # Create device without token
    device = VizioAsync(
        "pairing-script",
        host,
        "Pairing Device",
        auth_token=None,
        device_type=device_class,
    )
    
    # If we have pairing token and challenge type, skip start_pair and go straight to pair
    if pairing_token is not None and challenge_type is not None and pin:
        print("Completing existing pairing session...")
        print()
        try:
            pair_result = await device.pair(challenge_type, pairing_token, pin)
            if pair_result:
                auth_token = pair_result.auth_token
                print()
                print("=" * 60)
                print("✓ PAIRING SUCCESSFUL!")
                print("=" * 60)
                print(f"Access Token: {auth_token}")
                print()
                return auth_token
            else:
                print("✗ Pairing failed - incorrect PIN or device error")
                return None
        except Exception as e:
            print(f"✗ Pairing failed: {e}")
            return None
    
    print("Step 1: Starting pairing process...")
    print("   (This will display a PIN on your TV)")
    print()
    
    try:
        # Start pairing
        pair_data = await device.start_pair()
        if not pair_data:
            # Check if pairing is blocked (active session exists)
            print("⚠ Pairing session may already be active")
            print("   If you see a PIN on your TV, try completing it:")
            print(f"   python tests/pair_device.py {host} {device_type} <PIN>")
            print()
            print("   Or cancel the pairing on your TV and try again")
            return None
        
        print(f"✓ Pairing started")
        print(f"   Challenge type: {pair_data.ch_type}")
        print(f"   Pairing token: {pair_data.token}")
        print()
        
        # Get PIN from user or command line
        if pin is None:
            print("Step 2: Enter the PIN displayed on your TV")
            print("   (Look for a 4-digit code on your TV screen)")
            print()
            try:
                pin = input("Enter PIN: ").strip()
            except EOFError:
                print()
                print("⚠ No PIN provided and cannot read from stdin")
                print("   Please run with PIN as argument:")
                print(f"   python tests/pair_device.py {host} {device_type} <PIN>")
                print()
                print("   Or complete the existing session:")
                print(f"   python tests/pair_device.py {host} {device_type} <PIN> --token {pair_data.token} --challenge {pair_data.ch_type}")
                return None
        else:
            print(f"Step 2: Using provided PIN: {pin}")
        
        print()
        print("Step 3: Completing pairing...")
        pair_result = await device.pair(pair_data.ch_type, pair_data.token, pin)
        
        if not pair_result:
            print("✗ Pairing failed - incorrect PIN or device error")
            return None
        
        auth_token = pair_result.auth_token
        
        print()
        print("=" * 60)
        print("✓ PAIRING SUCCESSFUL!")
        print("=" * 60)
        print(f"Access Token: {auth_token}")
        print()
        print("Save this token and use it in your Home Assistant integration.")
        print("=" * 60)
        
        return auth_token
        
    except Exception as e:
        error_msg = str(e)
        if "BLOCKED" in error_msg or "blocked" in error_msg:
            print()
            print("=" * 60)
            print("⚠ PAIRING SESSION ALREADY ACTIVE")
            print("=" * 60)
            print("There is already an active pairing session on your TV.")
            print()
            print("Options:")
            print("1. If you see a PIN on your TV screen:")
            print(f"   python tests/pair_device.py {host} {device_type} <PIN>")
            print()
            print("2. Cancel the pairing on your TV:")
            print("   - Press BACK or EXIT on your TV remote")
            print("   - Wait a few seconds")
            print("   - Run this script again")
            print()
            print("3. The pairing session will timeout after a few minutes")
            return None
        else:
            print()
            print("=" * 60)
            print("✗ PAIRING FAILED")
            print("=" * 60)
            print(f"Error: {e}")
            print()
            print("Troubleshooting:")
            print("1. Make sure your TV is on and connected to the network")
            print("2. Make sure you entered the correct PIN")
            print("3. Make sure your TV supports SmartCast (2016 or newer)")
            print("4. Try restarting your TV and running this script again")
            return None

async def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python pair_device.py <host> [device_type] [pin] [--token <token>] [--challenge <type>]")
        print("Example: python pair_device.py 192.168.1.226 tv")
        print("Example: python pair_device.py 192.168.1.226 tv 1234")
        print()
        print("Device types: tv (default) or speaker")
        print("If PIN is provided, pairing will be completed automatically")
        print()
        print("To complete an existing pairing session:")
        print("  python pair_device.py <host> <device_type> <pin> --token <token> --challenge <type>")
        sys.exit(1)
    
    host = sys.argv[1]
    device_type = "tv"
    pin = None
    pairing_token = None
    challenge_type = None
    
    # Parse arguments
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--token" and i + 1 < len(sys.argv):
            pairing_token = int(sys.argv[i + 1])
            i += 2
        elif arg == "--challenge" and i + 1 < len(sys.argv):
            challenge_type = int(sys.argv[i + 1])
            i += 2
        elif arg in ["tv", "speaker"]:
            device_type = arg
            i += 1
        elif arg.isdigit() and pin is None:
            # This is likely the PIN
            pin = arg
            i += 1
        else:
            i += 1
    
    if pin:
        print("PIN provided via command line, will complete pairing automatically")
        print()
    
    token = await pair_device(host, device_type, pin, pairing_token, challenge_type)
    
    if token:
        print()
        print("To use this token in Home Assistant:")
        print("1. Go to Settings → Devices & Services")
        print("2. Find your Vizio integration")
        print("3. Click Configure")
        print("4. Update the access token to:", token)
        print()
        print("To use this token in the test script:")
        print(f"python tests/test_direct_api.py {host} {token} power-state")
        print(f"python tests/test_direct_api.py {host} {token} power-on")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nPairing cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

