#!/usr/bin/env python3
"""
Test Codeset 7 key commands for input selection.

Codeset 7 is used for input selection, but specific codes are not documented.
This script tests various codes to find which ones work for cycling to HDMI-1.

Usage:
    python test_codeset7_input.py <host> <token> [current_input]
    
Examples:
    python test_codeset7_input.py 192.168.1.226 Z0jxq5qp8j HDMI-2
    python test_codeset7_input.py 192.168.1.226 Z0jxq5qp8j CAST
"""

import asyncio
import json
import logging
import sys
from typing import Any

import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
_LOGGER = logging.getLogger(__name__)

# API endpoints
ENDPOINT_KEY_COMMAND = "/key_command/"
ENDPOINT_TV_INFORMATION = "/menu_native/dynamic/tv_settings/system/tv_information/tv"

KEY_CODESET_INPUT = 7


class StandaloneVizioAPIClient:
    """Standalone API client for testing."""
    
    def __init__(self, host: str, port: int, token: str):
        # Handle host:port format
        if ":" in host:
            host, port_str = host.rsplit(":", 1)
            port = int(port_str)
        
        self.host = host
        self.port = port
        self.token = token
        self.base_url = f"https://{host}:{port}"
        self.timeout = aiohttp.ClientTimeout(total=5)
    
    async def _request(self, method: str, endpoint: str, data: dict[str, Any] | None = None) -> dict[str, Any] | None:
        """Make an API request."""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "AUTH": self.token,
            "Content-Type": "application/json",
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    headers=headers,
                    json=data,
                    ssl=False,
                    timeout=self.timeout,
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        text = await resp.text()
                        _LOGGER.error(f"API request failed: {method} {endpoint} - Status {resp.status}: {text}")
                        return None
        except Exception as e:
            _LOGGER.error(f"API request error: {method} {endpoint} - {e}")
            return None
    
    async def send_key_command(self, codeset: int, code: int) -> bool:
        """Send a key command."""
        data = {
            "KEYLIST": [
                {
                    "CODESET": codeset,
                    "CODE": code,
                    "ACTION": "KEYPRESS"
                }
            ]
        }
        
        response = await self._request("PUT", ENDPOINT_KEY_COMMAND, data)
        if response:
            status = response.get("STATUS", {})
            result = status.get("RESULT")
            if result == "SUCCESS":
                return True
            else:
                detail = status.get("DETAIL", "Unknown error")
                _LOGGER.warning(f"Key command failed: CODESET={codeset}, CODE={code} - {detail}")
                return False
        return False
    
    async def get_current_input(self) -> str | None:
        """Get current input name from TV information."""
        response = await self._request("GET", ENDPOINT_TV_INFORMATION)
        if response and "ITEMS" in response:
            for item in response["ITEMS"]:
                if item.get("CNAME") == "input":
                    return item.get("VALUE", "")
        return None


async def test_codeset7_codes(host: str, token: str, current_input: str | None = None):
    """Test various Codeset 7 codes to find input selection."""
    client = StandaloneVizioAPIClient(host, 7345, token)
    
    # Get current input if not provided
    if current_input is None:
        _LOGGER.info("Getting current input...")
        current_input = await client.get_current_input()
        if current_input:
            _LOGGER.info(f"Current input: {current_input}")
        else:
            _LOGGER.warning("Could not determine current input")
            current_input = "UNKNOWN"
    
    _LOGGER.info(f"\nStarting input selection test...")
    _LOGGER.info(f"Current input: {current_input}")
    _LOGGER.info(f"Target: HDMI-1")
    _LOGGER.info(f"Testing Codeset 7 codes...\n")
    
    # Common input codes to try (these are guesses based on typical patterns)
    # Codes 0-9 are often used for direct input selection
    # Codes 10-20 might be for cycling/next/previous
    test_codes = [
        # Direct input codes (common pattern)
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9,
        # Next/Previous/Cycle codes
        10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
        # Additional common codes
        21, 22, 23, 24, 25, 30, 40, 50,
    ]
    
    target_input = "HDMI-1"
    found_working_codes = []
    
    for code in test_codes:
        _LOGGER.info(f"Testing CODE={code}...")
        
        # Send the key command
        success = await client.send_key_command(KEY_CODESET_INPUT, code)
        
        if success:
            # Wait a moment for the TV to process
            await asyncio.sleep(1.5)
            
            # Check if input changed
            new_input = await client.get_current_input()
            if new_input:
                _LOGGER.info(f"  ✓ Command succeeded. Current input: {new_input}")
                
                if new_input.upper() == target_input.upper() or "HDMI-1" in new_input.upper():
                    _LOGGER.info(f"  *** SUCCESS! CODE={code} changed input to {new_input} ***")
                    found_working_codes.append(code)
                elif new_input != current_input:
                    _LOGGER.info(f"  → Input changed from {current_input} to {new_input} (not target)")
            else:
                _LOGGER.info(f"  ✓ Command succeeded but couldn't verify input change")
        else:
            _LOGGER.info(f"  ✗ Command failed")
        
        # Small delay between tests
        await asyncio.sleep(0.5)
    
    # Summary
    _LOGGER.info(f"\n{'='*60}")
    _LOGGER.info("Test Summary:")
    _LOGGER.info(f"  Current input: {current_input}")
    _LOGGER.info(f"  Target input: {target_input}")
    if found_working_codes:
        _LOGGER.info(f"  Working codes: {found_working_codes}")
    else:
        _LOGGER.info("  No working codes found")
    _LOGGER.info(f"{'='*60}")


async def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    host = sys.argv[1]
    token = sys.argv[2]
    current_input = sys.argv[3] if len(sys.argv) > 3 else None
    
    await test_codeset7_codes(host, token, current_input)


if __name__ == "__main__":
    asyncio.run(main())

