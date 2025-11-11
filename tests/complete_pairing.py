#!/usr/bin/env python3
"""
Complete an existing Vizio pairing session using direct API.

Use this when a pairing session is already active and you have the PIN.
"""

import asyncio
import json
import sys
import aiohttp

async def complete_pairing(host, device_id, pin, challenge_type=1, pairing_token=None):
    """Complete an existing pairing session."""
    url = f"https://{host}:7345/pairing/pair"
    headers = {"Content-Type": "application/json"}
    
    # If no pairing token provided, try with 0 (sometimes works for existing sessions)
    if pairing_token is None:
        pairing_token = 0
    
    data = {
        "DEVICE_ID": device_id,
        "CHALLENGE_TYPE": challenge_type,
        "RESPONSE_VALUE": pin,
        "PAIRING_REQ_TOKEN": pairing_token
    }
    
    print("=" * 60)
    print("Completing Existing Pairing Session")
    print("=" * 60)
    print(f"Host: {host}")
    print(f"PIN: {pin}")
    print(f"Device ID: {device_id}")
    print(f"Pairing Token: {pairing_token}")
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
                        item = response_data.get("ITEM", {})
                        auth_token = item.get("AUTH_TOKEN")
                        if auth_token:
                            print()
                            print("=" * 60)
                            print("✓ PAIRING SUCCESSFUL!")
                            print("=" * 60)
                            print(f"Access Token: {auth_token}")
                            print()
                            return auth_token
                    else:
                        print(f"✗ Pairing failed: {result}")
                        print(f"  Detail: {status.get('DETAIL', 'Unknown')}")
                else:
                    print(f"✗ HTTP Error: {response.status}")
                
                return None
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    if len(sys.argv) < 4:
        print("Usage: python complete_pairing.py <host> <device_id> <pin> [pairing_token]")
        print("Example: python complete_pairing.py 192.168.1.226 pairing-script 4325")
        print()
        print("Note: If pairing_token is not provided, will try with 0")
        sys.exit(1)
    
    host = sys.argv[1]
    device_id = sys.argv[2]
    pin = sys.argv[3]
    pairing_token = int(sys.argv[4]) if len(sys.argv) > 4 else None
    
    token = await complete_pairing(host, device_id, pin, pairing_token=pairing_token)
    
    if token:
        print("To use this token:")
        print(f"python tests/test_direct_api.py {host} {token} power-on")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

