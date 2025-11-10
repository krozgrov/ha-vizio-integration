#!/usr/bin/env python3
"""
Pair with a Vizio device to get a new access token.
"""

import asyncio
import sys
from pyvizio import VizioAsync
from pyvizio.const import DEVICE_CLASS_TV, DEVICE_CLASS_SPEAKER

async def pair_device(host, device_type="tv"):
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
    
    print("Step 1: Starting pairing process...")
    print("   (This will display a PIN on your TV)")
    print()
    
    try:
        # Start pairing
        pair_data = await device.start_pair()
        if not pair_data:
            print("✗ Failed to start pairing - device may not be reachable")
            return None
        
        print(f"✓ Pairing started")
        print(f"   Challenge type: {pair_data.ch_type}")
        print()
        
        print("Step 2: Enter the PIN displayed on your TV")
        print("   (Look for a 4-digit code on your TV screen)")
        print()
        pin = input("Enter PIN: ").strip()
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
        print("Usage: python pair_device.py <host> [device_type]")
        print("Example: python pair_device.py 192.168.1.226 tv")
        print()
        print("Device types: tv (default) or speaker")
        sys.exit(1)
    
    host = sys.argv[1]
    device_type = sys.argv[2].lower() if len(sys.argv) > 2 else "tv"
    
    token = await pair_device(host, device_type)
    
    if token:
        print()
        print("To use this token in Home Assistant:")
        print("1. Go to Settings → Devices & Services")
        print("2. Find your Vizio integration")
        print("3. Click Configure")
        print("4. Update the access token to:", token)
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

