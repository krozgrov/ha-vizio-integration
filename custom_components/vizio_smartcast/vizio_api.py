"""Direct Vizio SmartCast API client.

This module provides direct API calls to Vizio SmartCast devices,
bypassing pyvizio for operations that are failing or unreliable.
Based on: https://github.com/exiva/Vizio_SmartCast_API
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

# API endpoints
ENDPOINT_KEY_COMMAND = "/key_command/"
ENDPOINT_POWER_MODE = "/state/device/power_mode"
ENDPOINT_CURRENT_INPUT = "/state/device/current_input"
ENDPOINT_INPUT_LIST = "/menu_native/dynamic/tv_settings/devices/name_input"
ENDPOINT_CHANGE_INPUT = "/menu_native/dynamic/tv_settings/devices/current_input"
ENDPOINT_AUDIO_SETTING = "/menu_native/dynamic/tv_settings/audio/{setting_name}"
ENDPOINT_GET_AUDIO_SETTING = "/menu_native/dynamic/tv_settings/audio"


class VizioAPIClient:
    """Direct API client for Vizio SmartCast devices."""

    def __init__(
        self,
        host: str,
        auth_token: str | None,
        session,
        port: int = 7345,
        timeout: int = 8,
    ) -> None:
        """Initialize the API client."""
        self.auth_token = auth_token
        self.session = session
        self.timeout = timeout
        
        # Handle host that might already include port (e.g., "192.168.1.226:7345")
        if ":" in host:
            # Host already includes port
            self.host = host.split(":")[0]
            self.port = int(host.split(":")[1])
        else:
            self.host = host
            self.port = port
        
        self.base_url = f"https://{self.host}:{self.port}"

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

        try:
            async with self.session.request(
                method,
                url,
                json=data,
                headers=headers,
                ssl=False,  # Vizio uses self-signed certs
                timeout=self.timeout,
            ) as response:
                if response.status == 200:
                    try:
                        # Try to parse as JSON first
                        json_data = await response.json()
                        return json_data
                    except Exception as json_err:
                        # If JSON parsing fails, get text for logging
                        response_text = await response.text()
                        _LOGGER.warning(
                            "API response is not JSON for %s %s: %s, Response: %s",
                            method,
                            endpoint,
                            json_err,
                            response_text[:200],
                        )
                        return None
                else:
                    # Non-200 status, get text for logging
                    response_text = await response.text()
                    _LOGGER.warning(
                        "API request failed: %s %s - Status: %s, Response: %s",
                        method,
                        endpoint,
                        response.status,
                        response_text[:500],
                    )
                    return None
        except asyncio.TimeoutError:
            _LOGGER.warning("API request timeout: %s %s", method, endpoint)
            return None
        except Exception as err:
            _LOGGER.warning("API request error: %s %s - %s", method, endpoint, err)
            return None

    async def get_power_state(self) -> bool | None:
        """Get current power state.
        
        Returns:
            True if device is on
            False if device is off
            None if unable to determine (connection error, etc.)
        """
        try:
            response = await self._request("GET", ENDPOINT_POWER_MODE)
            if response and "ITEMS" in response:
                for item in response["ITEMS"]:
                    if item.get("CNAME") == "power_mode":
                        # Power mode: 0 = off, 1 = on
                        value = item.get("VALUE")
                        if value is not None:
                            return value == 1
                        # If VALUE is None but item exists, device might be off
                        return False
            # If we got a response but no ITEMS, might be a different format
            if response:
                _LOGGER.debug("Unexpected response format for power state: %s", response)
            return None
        except Exception as err:
            _LOGGER.debug("Error getting power state via direct API: %s", err)
            return None

    async def power_on(self) -> bool:
        """Send power on command."""
        # Use key command for power on (CODESET 11, CODE 1)
        return await self._send_key_command(11, 1)

    async def power_off(self) -> bool:
        """Send power off command."""
        # Use key command for power off (CODESET 11, CODE 0)
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
        _LOGGER.debug(
            "Sending key command: CODESET=%d, CODE=%d to %s",
            codeset,
            code,
            self.base_url + ENDPOINT_KEY_COMMAND,
        )
        response = await self._request("PUT", ENDPOINT_KEY_COMMAND, data)
        if response:
            status = response.get("STATUS", {})
            result = status.get("RESULT", "").upper() if status.get("RESULT") else ""
            detail = status.get("DETAIL", "Unknown")
            _LOGGER.debug(
                "Key command response: CODESET=%d, CODE=%d, RESULT=%s, DETAIL=%s, Full response: %s",
                codeset,
                code,
                result,
                detail,
                response,
            )
            # Accept SUCCESS (case-insensitive) as success
            if result == "SUCCESS":
                _LOGGER.debug(
                    "Key command succeeded: CODESET=%d, CODE=%d",
                    codeset,
                    code,
                )
                return True
            else:
                _LOGGER.warning(
                    "Key command failed: CODESET=%d, CODE=%d, RESULT=%s, DETAIL=%s, Full response: %s",
                    codeset,
                    code,
                    result,
                    detail,
                    response,
                )
                return False
        else:
            _LOGGER.warning(
                "Key command request failed: CODESET=%d, CODE=%d (no response from API)",
                codeset,
                code,
            )
        return False

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
                if item.get("TYPE") == "T_VALUE_V1":
                    # Extract input name and HASHVAL
                    value = item.get("VALUE", "")
                    hashval = item.get("HASHVAL")
                    if value and hashval is not None:
                        inputs.append({
                            "name": value,
                            "id": hashval,
                        })
        return inputs

    async def set_input(self, input_name: str) -> bool:
        """Set input by name."""
        # First, get the current input to get its HASHVAL (required by API)
        current_input = await self.get_current_input()
        if not current_input or current_input.get("id") is None:
            _LOGGER.warning("Cannot get current input HASHVAL for input selection")
            return False
        
        current_input_hashval = current_input["id"]
        
        # Get the list of available inputs to find the target input's HASHVAL
        input_list = await self.get_input_list()
        target_input = None
        for inp in input_list:
            if inp["name"].upper() == input_name.upper():
                target_input = inp
                break
        
        if not target_input:
            _LOGGER.warning("Input '%s' not found in available inputs", input_name)
            return False
        
        target_input_hashval = target_input["id"]
        
        # Change input using the API
        # According to API docs: PUT to current_input with REQUEST: MODIFY, VALUE: input_name, HASHVAL: target_hashval
        # Input names should be lowercase
        data = {
            "REQUEST": "MODIFY",
            "VALUE": input_name.lower(),
            "HASHVAL": target_input_hashval,
        }
        
        response = await self._request("PUT", ENDPOINT_CHANGE_INPUT, data)
        
        if response:
            status = response.get("STATUS", {})
            result = status.get("RESULT")
            if result == "SUCCESS":
                _LOGGER.debug("Successfully changed input to %s", input_name)
                return True
            else:
                _LOGGER.debug(
                    "Input change failed: %s",
                    status.get("DETAIL", "Unknown error"),
                )
        
        return False

    async def volume_up(self, num: int = 1) -> bool:
        """Increase volume."""
        # CODESET 5, CODE 2 = Volume Up
        for _ in range(num):
            if not await self._send_key_command(5, 2):
                return False
        return True

    async def volume_down(self, num: int = 1) -> bool:
        """Decrease volume."""
        # CODESET 5, CODE 3 = Volume Down
        for _ in range(num):
            if not await self._send_key_command(5, 3):
                return False
        return True

    async def mute(self, mute_on: bool = True) -> bool:
        """Toggle mute."""
        # CODESET 5, CODE 4 = Mute
        return await self._send_key_command(5, 4)

    async def get_volume_level(self) -> int | None:
        """Get current volume level."""
        # This would require parsing the audio settings response
        # For now, return None - we'll use pyvizio's method as fallback
        return None

