#!/usr/bin/env python3
"""
Standalone Vizio SmartCast API Test Tool

Test direct API calls to Vizio devices without Home Assistant.
This allows rapid development and testing of API functionality.

Usage:
    python test_direct_api.py <host> <token> [command] [args...]

Commands:
    power-state          Get current power state
    power-on             Turn device on
    power-off            Turn device off
    volume-up [n]        Volume up (n times, default 1)
    volume-down [n]      Volume down (n times, default 1)
    mute                 Toggle mute
    current-input        Get current input
    input-list           List available inputs
    set-input <name>     Set input by name
    audio-settings       Get all audio settings
    device-info          Get device information
    test-all             Run all tests

Examples:
    python test_direct_api.py 192.168.1.226 Za8cqlwuz0 power-state
    python test_direct_api.py 192.168.1.226 Za8cqlwuz0 power-on
    python test_direct_api.py 192.168.1.226 Za8cqlwuz0 set-input HDMI-1
    python test_direct_api.py 192.168.1.226 Za8cqlwuz0 test-all
"""

import asyncio
import json
import logging
import sys
from typing import Any

import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
_LOGGER = logging.getLogger(__name__)

# API endpoints
ENDPOINT_KEY_COMMAND = "/key_command/"
ENDPOINT_POWER_MODE = "/state/device/power_mode"
ENDPOINT_CURRENT_INPUT = "/state/device/current_input"
ENDPOINT_INPUT_LIST = "/menu_native/dynamic/tv_settings/devices/name_input"
ENDPOINT_CHANGE_INPUT = "/menu_native/dynamic/tv_settings/devices/current_input"
ENDPOINT_GET_AUDIO_SETTING = "/menu_native/dynamic/tv_settings/audio"
ENDPOINT_TV_INFORMATION = "/menu_native/dynamic/tv_settings/system/tv_information/tv"
ENDPOINT_DEVICE_INFO = "/state/device/info"
ENDPOINT_DEVICE_NAME = "/state/device/name"
ENDPOINT_DEVICE_VERSION = "/state/device/version"
ENDPOINT_DEVICE_MODEL = "/state/device/model"
ENDPOINT_DEVICE_SERIAL = "/state/device/serial"
ENDPOINT_DEVICE_MAC = "/state/device/mac"
ENDPOINT_DEVICE_UPTIME = "/state/device/uptime"
ENDPOINT_DEVICE_RESOLUTION = "/state/device/resolution"


class StandaloneVizioAPIClient:
    """Standalone Vizio API client (no Home Assistant dependencies)."""

    def __init__(
        self,
        host: str,
        auth_token: str | None,
        port: int = 7345,
        timeout: int = 8,
    ) -> None:
        """Initialize the API client."""
        self.auth_token = auth_token
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        
        # Handle host that might already include port
        if ":" in host and not host.startswith("["):
            parts = host.rsplit(":", 1)
            self.host = parts[0]
            try:
                self.port = int(parts[1])
            except (ValueError, IndexError):
                self.host = host
                self.port = port
        else:
            self.host = host
            self.port = port
        
        self.base_url = f"https://{self.host}:{self.port}"
        _LOGGER.debug("API client initialized: host=%s, port=%d, base_url=%s", 
                     self.host, self.port, self.base_url)

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Make an API request."""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if self.auth_token:
            headers["AUTH"] = self.auth_token
            # Also try lowercase 'auth' header (some APIs are case-sensitive)
            # headers["auth"] = self.auth_token  # Uncomment if needed
        
        _LOGGER.debug("Request: %s %s", method, url)
        if data:
            _LOGGER.debug("Request data: %s", json.dumps(data, indent=2))
        if self.auth_token:
            _LOGGER.debug("Auth token present: %s...%s", self.auth_token[:4] if len(self.auth_token) > 8 else "***", self.auth_token[-4:] if len(self.auth_token) > 8 else "")
        else:
            _LOGGER.debug("No auth token provided")

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.request(
                    method,
                    url,
                    json=data,
                    headers=headers,
                    ssl=False,  # Vizio uses self-signed certs
                ) as response:
                    _LOGGER.debug("Response status: %d", response.status)
                    
                    if response.status == 200:
                        try:
                            json_data = await response.json()
                            _LOGGER.debug("Response JSON: %s", json.dumps(json_data, indent=2))
                            return json_data
                        except Exception as json_err:
                            text = await response.text()
                            _LOGGER.error("JSON parse error: %s", json_err)
                            _LOGGER.error("Response text: %s", text[:500])
                            return None
                    else:
                        text = await response.text()
                        _LOGGER.error("HTTP error %d: %s", response.status, text[:500])
                        return None
        except asyncio.TimeoutError:
            _LOGGER.error("Request timeout")
            return None
        except Exception as err:
            _LOGGER.error("Request error: %s", err, exc_info=True)
            return None

    async def get_power_state(self) -> bool | None:
        """Get current power state."""
        response = await self._request("GET", ENDPOINT_POWER_MODE)
        if response and "ITEMS" in response:
            for item in response["ITEMS"]:
                if item.get("CNAME") == "power_mode":
                    value = item.get("VALUE")
                    if value is not None:
                        return value == 1
                    return False
        return None

    async def power_on(self) -> bool:
        """Send power on command."""
        return await self._send_key_command(11, 1)

    async def power_off(self) -> bool:
        """Send power off command."""
        return await self._send_key_command(11, 0)

    async def _send_key_command(self, codeset: int, code: int) -> bool:
        """Send a key command."""
        data = {
            "KEYLIST": [
                {
                    "CODESET": codeset,
                    "CODE": code,
                    "ACTION": "KEYPRESS",
                }
            ]
        }
        response = await self._request("PUT", ENDPOINT_KEY_COMMAND, data)
        if response:
            status = response.get("STATUS", {})
            result = status.get("RESULT", "").upper() if status.get("RESULT") else ""
            return result == "SUCCESS"
        return False

    async def volume_up(self, num: int = 1) -> bool:
        """Increase volume."""
        for _ in range(num):
            if not await self._send_key_command(5, 2):
                return False
        return True

    async def volume_down(self, num: int = 1) -> bool:
        """Decrease volume."""
        for _ in range(num):
            if not await self._send_key_command(5, 3):
                return False
        return True

    async def mute(self) -> bool:
        """Toggle mute."""
        return await self._send_key_command(5, 4)

    async def get_current_input(self) -> dict[str, Any] | None:
        """Get current input information."""
        response = await self._request("GET", ENDPOINT_CURRENT_INPUT)
        if response and "ITEMS" in response:
            for item in response["ITEMS"]:
                if item.get("CNAME") == "current_input":
                    return {
                        "name": item.get("VALUE", ""),
                        "id": item.get("HASHVAL"),
                    }
        return None

    async def get_input_list(self) -> list[dict[str, Any]]:
        """Get list of available inputs."""
        response = await self._request("GET", ENDPOINT_INPUT_LIST)
        inputs = []
        if response and "ITEMS" in response:
            for item in response["ITEMS"]:
                # Handle both T_VALUE_V1 (standard) and T_DEVICE_V1 (some models)
                item_type = item.get("TYPE")
                if item_type in ("T_VALUE_V1", "T_DEVICE_V1"):
                    # Try to get name from VALUE or NAME field
                    name = item.get("VALUE") or item.get("NAME", "")
                    # Try to get HASHVAL directly or from CNAME
                    hashval = item.get("HASHVAL")
                    cname = item.get("CNAME", "")
                    
                    # Some models don't provide HASHVAL directly
                    # We'll use CNAME as identifier if HASHVAL is missing
                    if name and (hashval is not None or cname):
                        inputs.append({
                            "name": name,
                            "id": hashval if hashval is not None else cname,
                            "cname": cname,
                        })
        return inputs

    async def set_input(self, input_name: str) -> bool:
        """Set input by name.
        
        According to API docs:
        - VALUE: ITEMS[x].NAME from name_input endpoint
        - HASHVAL: Current HashValue from a GET of current_input endpoint
        """
        # Step 1: Get current_input to extract HASHVAL
        current_input_response = await self._request("GET", ENDPOINT_CHANGE_INPUT)
        current_hashval = None
        
        if current_input_response:
            # Per API docs and user feedback: HASHVAL should be in ITEMS[0].HASHVAL
            # This is the correct way to get the current input HASHVAL
            if "ITEMS" in current_input_response and len(current_input_response["ITEMS"]) > 0:
                item0 = current_input_response["ITEMS"][0]
                hashval = item0.get("HASHVAL")
                if hashval is not None:
                    current_hashval = int(hashval)
                    _LOGGER.debug("Found current input HASHVAL in ITEMS[0]: %d", current_hashval)
        
        if current_hashval is None:
            _LOGGER.error(
                "Could not extract current input HASHVAL from ITEMS[0].HASHVAL. "
                "This TV model may not support programmatic input selection. "
                "The current_input endpoint must return ITEMS[0].HASHVAL for input selection to work."
            )
            return False
        
        # Step 2: Get input list to find target input NAME
        input_list = await self.get_input_list()
        if not input_list:
            _LOGGER.error("Could not retrieve input list")
            return False
        
        # Find the target input (match by name or CNAME)
        target_input = None
        input_name_upper = input_name.upper()
        for inp in input_list:
            if (
                inp["name"].upper() == input_name_upper
                or inp.get("cname", "").upper() == input_name_upper.replace("-", "").replace("_", "")
            ):
                target_input = inp
                break
        
        if not target_input:
            _LOGGER.error("Input '%s' not found", input_name)
            return False
        
        # Try lowercase CNAME first (as per user feedback), fallback to NAME
        # User example uses "hdmi2" (lowercase CNAME), not "HDMI-2" (NAME)
        target_value = target_input.get("cname", "").lower()
        if not target_value:
            target_value = target_input["name"]
        
        # Step 3: Set input with current HASHVAL and target VALUE
        data = {
            "REQUEST": "MODIFY",
            "VALUE": target_value,  # Use lowercase CNAME (e.g., "hdmi2") or NAME as fallback
            "HASHVAL": current_hashval,  # Use HASHVAL from ITEMS[0] of current_input GET
        }
        
        response = await self._request("PUT", ENDPOINT_CHANGE_INPUT, data)
        if response:
            status = response.get("STATUS", {})
            result = status.get("RESULT")
            return result == "SUCCESS"
        return False

    async def get_device_info(self) -> dict[str, Any]:
        """Get device information by querying multiple endpoints."""
        info = {}
        
        # First check if device is on (some endpoints may require device to be on)
        power_state = await self.get_power_state()
        info["power_state"] = "ON" if power_state else "OFF" if power_state is False else "UNKNOWN"
        
        # Try common device info endpoints
        endpoints = {
            "info": ENDPOINT_DEVICE_INFO,
            "name": ENDPOINT_DEVICE_NAME,
            "version": ENDPOINT_DEVICE_VERSION,
            "model": ENDPOINT_DEVICE_MODEL,
            "serial": ENDPOINT_DEVICE_SERIAL,
            "mac": ENDPOINT_DEVICE_MAC,
            "uptime": ENDPOINT_DEVICE_UPTIME,
            "resolution": ENDPOINT_DEVICE_RESOLUTION,
        }
        
        successful_endpoints = []
        failed_endpoints = []
        
        for key, endpoint in endpoints.items():
            response = await self._request("GET", endpoint)
            if response:
                if "STATUS" in response:
                    status_result = response.get("STATUS", {}).get("RESULT", "")
                    if status_result == "SUCCESS":
                        successful_endpoints.append(key)
                        if "ITEMS" in response:
                            # Parse ITEMS array
                            items_data = {}
                            for item in response["ITEMS"]:
                                cname = item.get("CNAME", "")
                                value = item.get("VALUE", "")
                                if cname:
                                    items_data[cname] = value
                            if items_data:
                                info[key] = items_data
                        elif "ITEM" in response:
                            # Single ITEM object
                            info[key] = response["ITEM"]
                        else:
                            # Store full response if structure is different
                            info[key] = response
                    else:
                        failed_endpoints.append(f"{key} ({status_result})")
                else:
                    # No STATUS field, store response anyway
                    info[key] = response
                    successful_endpoints.append(key)
            else:
                failed_endpoints.append(f"{key} (no response)")
        
        info["_summary"] = {
            "successful": successful_endpoints,
            "failed": failed_endpoints,
        }
        
        return info

    async def get_audio_settings(self) -> dict[str, Any] | None:
        """Get all audio settings."""
        response = await self._request("GET", ENDPOINT_GET_AUDIO_SETTING)
        if response and "ITEMS" in response:
            settings = {}
            for item in response["ITEMS"]:
                cname = item.get("CNAME")
                if cname:
                    settings[cname] = item.get("VALUE")
            return settings
        return None

    async def get_model_name(self) -> str | None:
        """Get device model name."""
        response = await self._request("GET", ENDPOINT_TV_INFORMATION)
        if response and "ITEMS" in response:
            for item in response["ITEMS"]:
                if item.get("CNAME") == "model_name":
                    return item.get("VALUE")
        return None

    async def get_version(self) -> str | None:
        """Get device firmware version."""
        response = await self._request("GET", ENDPOINT_TV_INFORMATION)
        if response and "ITEMS" in response:
            for item in response["ITEMS"]:
                if item.get("CNAME") == "firmware":
                    return item.get("VALUE")
        return None

    async def get_device_info(self) -> dict[str, Any]:
        """Get comprehensive device information."""
        response = await self._request("GET", ENDPOINT_TV_INFORMATION)
        info = {}
        if response and "ITEMS" in response:
            for item in response["ITEMS"]:
                cname = item.get("CNAME")
                value = item.get("VALUE")
                if cname and value:
                    info[cname] = value
        return info


async def test_power_state(client: StandaloneVizioAPIClient) -> None:
    """Test power state query."""
    print("\n" + "=" * 60)
    print("TEST: Get Power State")
    print("=" * 60)
    state = await client.get_power_state()
    if state is True:
        print("✓ Device is ON")
    elif state is False:
        print("✓ Device is OFF")
    else:
        print("✗ Could not determine power state")
    print()


async def test_power_on(client: StandaloneVizioAPIClient) -> None:
    """Test power on."""
    print("\n" + "=" * 60)
    print("TEST: Power On")
    print("=" * 60)
    print("Sending power on command...")
    success = await client.power_on()
    if success:
        print("✓ Power on command sent successfully")
        await asyncio.sleep(3)
        state = await client.get_power_state()
        if state:
            print("✓ Device confirmed ON")
        else:
            print("⚠ Command sent but device state unclear")
    else:
        print("✗ Power on command failed")
    print()


async def test_power_off(client: StandaloneVizioAPIClient) -> None:
    """Test power off."""
    print("\n" + "=" * 60)
    print("TEST: Power Off")
    print("=" * 60)
    print("Sending power off command...")
    success = await client.power_off()
    if success:
        print("✓ Power off command sent successfully")
        await asyncio.sleep(2)
        state = await client.get_power_state()
        if state is False:
            print("✓ Device confirmed OFF")
        else:
            print("⚠ Command sent but device state unclear")
    else:
        print("✗ Power off command failed")
    print()


async def test_volume_up(client: StandaloneVizioAPIClient, num: int = 1) -> None:
    """Test volume up."""
    print("\n" + "=" * 60)
    print(f"TEST: Volume Up ({num} times)")
    print("=" * 60)
    success = await client.volume_up(num)
    if success:
        print(f"✓ Volume up command sent successfully ({num} times)")
    else:
        print("✗ Volume up command failed")
    print()


async def test_volume_down(client: StandaloneVizioAPIClient, num: int = 1) -> None:
    """Test volume down."""
    print("\n" + "=" * 60)
    print(f"TEST: Volume Down ({num} times)")
    print("=" * 60)
    success = await client.volume_down(num)
    if success:
        print(f"✓ Volume down command sent successfully ({num} times)")
    else:
        print("✗ Volume down command failed")
    print()


async def test_mute(client: StandaloneVizioAPIClient) -> None:
    """Test mute."""
    print("\n" + "=" * 60)
    print("TEST: Mute Toggle")
    print("=" * 60)
    success = await client.mute()
    if success:
        print("✓ Mute command sent successfully")
    else:
        print("✗ Mute command failed")
    print()


async def test_current_input(client: StandaloneVizioAPIClient) -> None:
    """Test get current input."""
    print("\n" + "=" * 60)
    print("TEST: Get Current Input")
    print("=" * 60)
    input_data = await client.get_current_input()
    if input_data:
        print(f"✓ Current input: {input_data['name']}")
        print(f"  HASHVAL: {input_data['id']}")
    else:
        print("✗ Could not get current input")
    print()


async def test_input_list(client: StandaloneVizioAPIClient) -> None:
    """Test get input list."""
    print("\n" + "=" * 60)
    print("TEST: Get Input List")
    print("=" * 60)
    inputs = await client.get_input_list()
    if inputs:
        print(f"✓ Found {len(inputs)} inputs:")
        for inp in inputs:
            print(f"  - {inp['name']} (HASHVAL: {inp['id']})")
    else:
        print("✗ Could not get input list")
    print()


async def test_set_input(client: StandaloneVizioAPIClient, input_name: str) -> None:
    """Test set input."""
    print("\n" + "=" * 60)
    print(f"TEST: Set Input to '{input_name}'")
    print("=" * 60)
    success = await client.set_input(input_name)
    if success:
        print(f"✓ Input changed to '{input_name}'")
        await asyncio.sleep(1)
        current = await client.get_current_input()
        if current:
            print(f"✓ Confirmed current input: {current['name']}")
    else:
        print(f"✗ Failed to set input to '{input_name}'")
    print()


async def test_device_info(client: StandaloneVizioAPIClient) -> None:
    """Test get device info."""
    print("\n" + "=" * 60)
    print("TEST: Get Device Information")
    print("=" * 60)
    info = await client.get_device_info()
    if info:
        print("✓ Device information retrieved:")
        
        # Show key information first
        if "model_name" in info:
            print(f"\n  Model Name: {info['model_name']}")
        if "firmware" in info:
            print(f"  Firmware: {info['firmware']}")
        if "serial_number" in info:
            print(f"  Serial Number: {info['serial_number']}")
        if "tv_name" in info:
            print(f"  TV Name: {info['tv_name']}")
        
        # Show all other info
        print("\n  All Information:")
        for key, value in info.items():
            if key not in ["model_name", "firmware", "serial_number", "tv_name"]:
                print(f"    {key}: {value}")
    else:
        print("✗ Could not get device information")
    print()


async def test_audio_settings(client: StandaloneVizioAPIClient) -> None:
    """Test get audio settings."""
    print("\n" + "=" * 60)
    print("TEST: Get Audio Settings")
    print("=" * 60)
    settings = await client.get_audio_settings()
    if settings:
        print("✓ Audio settings:")
        for key, value in settings.items():
            print(f"  {key}: {value}")
    else:
        print("✗ Could not get audio settings")
    print()


async def test_all(client: StandaloneVizioAPIClient) -> None:
    """Run all tests."""
    print("\n" + "=" * 60)
    print("RUNNING ALL TESTS")
    print("=" * 60)
    
    await test_power_state(client)
    await test_current_input(client)
    await test_input_list(client)
    await test_audio_settings(client)
    await test_device_info(client)
    await test_volume_up(client, 1)
    await test_mute(client)
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETE")
    print("=" * 60)
    print("\nNote: Power on/off tests skipped in 'test-all' mode")
    print("      Run 'power-on' or 'power-off' commands separately")


async def main():
    """Main function."""
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    host = sys.argv[1]
    token = sys.argv[2] if sys.argv[2] != "none" else None
    command = sys.argv[3] if len(sys.argv) > 3 else "test-all"
    
    print("=" * 60)
    print("Vizio SmartCast Direct API Test Tool")
    print("=" * 60)
    print(f"Host: {host}")
    print(f"Token: {'***' + token[-4:] if token else 'None'}")
    print(f"Command: {command}")
    print("=" * 60)
    
    client = StandaloneVizioAPIClient(host, token)
    
    try:
        if command == "power-state":
            await test_power_state(client)
        elif command == "power-on":
            await test_power_on(client)
        elif command == "power-off":
            await test_power_off(client)
        elif command == "volume-up":
            num = int(sys.argv[4]) if len(sys.argv) > 4 else 1
            await test_volume_up(client, num)
        elif command == "volume-down":
            num = int(sys.argv[4]) if len(sys.argv) > 4 else 1
            await test_volume_down(client, num)
        elif command == "mute":
            await test_mute(client)
        elif command == "current-input":
            await test_current_input(client)
        elif command == "input-list":
            await test_input_list(client)
        elif command == "set-input":
            if len(sys.argv) < 5:
                print("Error: set-input requires input name")
                print("Usage: python test_direct_api.py <host> <token> set-input <input-name>")
                sys.exit(1)
            await test_set_input(client, sys.argv[4])
        elif command == "audio-settings":
            await test_audio_settings(client)
        elif command == "device-info":
            await test_device_info(client)
        elif command == "test-all":
            await test_all(client)
        else:
            print(f"Unknown command: {command}")
            print(__doc__)
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

