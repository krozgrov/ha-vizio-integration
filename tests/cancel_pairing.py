#!/usr/bin/env python3
"""
Cancel an existing Vizio pairing session using direct API.
"""

import asyncio
import json
import sys
import aiohttp

async def cancel_pairing(host, device_id="pairing-script"):
    """Cancel an existing pairing session."""
    url = f"https://{host}:7345/pairing/cancel"
    headers = {"Content-Type": "application/json"}
    
    data = {
        "DEVICE_ID": device_id,
        "CHALLENGE_TYPE": 1,
        "RESPONSE_VALUE": "1111",  # Hard-coded per API docs
        "PAIRING_REQ_TOKEN": 0
    }
    
    print("=" * 60)
    print("Canceling Pairing Session")
    print("=" * 60)
    print(f"Host: {host}")
    print("=" * 60)
    print()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.put(
                url,
                json=data,
                headers=headers,
                ssl=False,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                print(f"Response Status: {response.status}")
                response_data = await response.json()
                print(f"Response: {json.dumps(response_data, indent=2)}")
                
                if response.status == 200:
                    status = response_data.get("STATUS", {})
                    result = status.get("RESULT", "")
                    
                    if result == "SUCCESS":
                        print()
                        print("✓ Pairing session canceled successfully")
                        print("   You can now start a new pairing session")
                        return True
                    else:
                        print(f"✗ Cancel failed: {result}")
                        print(f"  Detail: {status.get('DETAIL', 'Unknown')}")
                else:
                    print(f"✗ HTTP Error: {response.status}")
                
                return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    if len(sys.argv) < 2:
        print("Usage: python cancel_pairing.py <host> [device_id]")
        print("Example: python cancel_pairing.py 192.168.1.226")
        sys.exit(1)
    
    host = sys.argv[1]
    device_id = sys.argv[2] if len(sys.argv) > 2 else "pairing-script"
    
    success = await cancel_pairing(host, device_id)
    
    if success:
        print()
        print("Now you can start a new pairing:")
        print(f"python tests/pair_device.py {host} tv")
        sys.exit(0)
    else:
        print()
        print("You may need to cancel the pairing manually on your TV:")
        print("1. Press BACK or EXIT on your TV remote")
        print("2. Wait a few seconds")
        print("3. Try pairing again")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

