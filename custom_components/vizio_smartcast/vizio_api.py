"""Direct Vizio SmartCast API client.

This module provides direct API calls to Vizio SmartCast devices,
bypassing pyvizio for operations that are failing or unreliable.

This is a lightweight API client library embedded within the integration,
following Home Assistant best practices for device communication:
- Clean separation of API logic from entity logic
- Comprehensive error handling and logging
- Direct control over API calls and responses
- No external dependencies beyond Home Assistant core

Based on: https://github.com/exiva/Vizio_SmartCast_API

Logging:
- Debug level: Detailed request/response information for troubleshooting
- Warning level: Errors and failures that may need attention
- Info level: Important state changes (if needed)
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    ENDPOINT_AUDIO_SETTING,
    ENDPOINT_CHANGE_INPUT,
    ENDPOINT_CURRENT_INPUT,
    ENDPOINT_GET_AUDIO_SETTING,
    ENDPOINT_INPUT_LIST,
    ENDPOINT_KEY_COMMAND,
    ENDPOINT_POWER_MODE,
    ENDPOINT_TV_INFORMATION,
    KEY_CODESET_POWER,
    KEY_CODESET_VOLUME,
    KEY_CODE_MUTE,
    KEY_CODE_POWER_OFF,
    KEY_CODE_POWER_ON,
    KEY_CODE_VOLUME_DOWN,
    KEY_CODE_VOLUME_UP,
)

_LOGGER = logging.getLogger(__name__)


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
        # Check if host contains a colon (IPv6 addresses also use colons, but not in this context)
        if ":" in host and not host.startswith("["):
            # Host already includes port (format: "host:port")
            parts = host.rsplit(":", 1)  # Use rsplit to handle IPv6 addresses correctly
            self.host = parts[0]
            try:
                self.port = int(parts[1])
            except (ValueError, IndexError):
                # Invalid port format, use default
                self.host = host
                self.port = port
        else:
            self.host = host
            self.port = port
        
        self.base_url = f"https://{self.host}:{self.port}"
        _LOGGER.debug("Direct API client initialized: host=%s, port=%d, base_url=%s", self.host, self.port, self.base_url)

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Make an API request.
        
        Args:
            method: HTTP method (GET, PUT, POST, etc.)
            endpoint: API endpoint path
            data: Optional JSON data for request body
            
        Returns:
            Parsed JSON response dict, or None if request failed
        """
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        # Mask auth token in logs for security
        auth_header = None
        if self.auth_token:
            headers["AUTH"] = self.auth_token
            auth_header = f"{self.auth_token[:4]}...{self.auth_token[-4:]}" if len(self.auth_token) > 8 else "***"
        
        # Log request details at debug level
        _LOGGER.debug(
            "API request: %s %s (host=%s, port=%d, auth=%s, timeout=%ds)",
            method,
            endpoint,
            self.host,
            self.port,
            "present" if auth_header else "none",
            self.timeout,
        )
        if data:
            _LOGGER.debug("Request data: %s", data)

        try:
            async with self.session.request(
                method,
                url,
                json=data,
                headers=headers,
                ssl=False,  # Vizio uses self-signed certs
                timeout=self.timeout,
            ) as response:
                # Log response status
                _LOGGER.debug(
                    "API response: %s %s - Status: %d, Headers: %s",
                    method,
                    endpoint,
                    response.status,
                    dict(response.headers),
                )
                
                if response.status == 200:
                    try:
                        # Try to parse as JSON first
                        json_data = await response.json()
                        _LOGGER.debug(
                            "API response JSON: %s %s - %s",
                            method,
                            endpoint,
                            json_data,
                        )
                        return json_data
                    except Exception as json_err:
                        # If JSON parsing fails, get text for logging
                        response_text = await response.text()
                        _LOGGER.warning(
                            "API response is not JSON for %s %s: %s, Response (first 500 chars): %s",
                            method,
                            endpoint,
                            json_err,
                            response_text[:500],
                        )
                        _LOGGER.debug(
                            "Full non-JSON response: %s",
                            response_text,
                        )
                        return None
                else:
                    # Non-200 status, get text for logging
                    response_text = await response.text()
                    _LOGGER.warning(
                        "API request failed: %s %s - Status: %d, Response (first 500 chars): %s",
                        method,
                        endpoint,
                        response.status,
                        response_text[:500],
                    )
                    _LOGGER.debug(
                        "Full error response: %s",
                        response_text,
                    )
                    return None
        except asyncio.TimeoutError:
            _LOGGER.warning(
                "API request timeout: %s %s (timeout=%ds, host=%s:%d)",
                method,
                endpoint,
                self.timeout,
                self.host,
                self.port,
            )
            return None
        except Exception as err:
            _LOGGER.warning(
                "API request error: %s %s - %s (type: %s)",
                method,
                endpoint,
                err,
                type(err).__name__,
            )
            _LOGGER.debug(
                "Full exception details for %s %s:",
                method,
                endpoint,
                exc_info=True,
            )
            return None

    async def get_power_state(self) -> bool | None:
        """Get current power state.
        
        Returns:
            True if device is on
            False if device is off
            None if unable to determine (connection error, etc.)
        """
        _LOGGER.debug("Getting power state from %s:%d", self.host, self.port)
        try:
            response = await self._request("GET", ENDPOINT_POWER_MODE)
            if response and "ITEMS" in response:
                for item in response["ITEMS"]:
                    if item.get("CNAME") == "power_mode":
                        # Power mode: 0 = off, 1 = on
                        value = item.get("VALUE")
                        _LOGGER.debug(
                            "Power state response: CNAME=%s, VALUE=%s, HASHVAL=%s",
                            item.get("CNAME"),
                            value,
                            item.get("HASHVAL"),
                        )
                        if value is not None:
                            is_on = value == 1
                            _LOGGER.debug("Power state determined: %s (value=%s)", "ON" if is_on else "OFF", value)
                            return is_on
                        # If VALUE is None but item exists, device might be off
                        _LOGGER.debug("Power state VALUE is None, assuming OFF")
                        return False
            # If we got a response but no ITEMS, might be a different format
            if response:
                _LOGGER.warning(
                    "Unexpected response format for power state: %s (expected ITEMS array)",
                    response,
                )
            else:
                _LOGGER.debug("No response received for power state query")
            return None
        except Exception as err:
            _LOGGER.warning(
                "Error getting power state via direct API: %s (type: %s)",
                err,
                type(err).__name__,
            )
            _LOGGER.debug(
                "Power state exception details:",
                exc_info=True,
            )
            return None

    async def power_on(self) -> bool:
        """Send power on command.
        
        Returns:
            True if command was sent successfully, False otherwise
        """
        _LOGGER.debug("Sending power on command to %s:%d", self.host, self.port)
        result = await self._send_key_command(KEY_CODESET_POWER, KEY_CODE_POWER_ON)
        _LOGGER.debug("Power on command result: %s", "success" if result else "failed")
        return result

    async def power_off(self) -> bool:
        """Send power off command.
        
        Returns:
            True if command was sent successfully, False otherwise
        """
        _LOGGER.debug("Sending power off command to %s:%d", self.host, self.port)
        result = await self._send_key_command(KEY_CODESET_POWER, KEY_CODE_POWER_OFF)
        _LOGGER.debug("Power off command result: %s", "success" if result else "failed")
        return result

    async def _send_key_command(self, codeset: int, code: int) -> bool:
        """Send a key command.
        
        Args:
            codeset: Key command codeset (e.g., 11 for power, 5 for audio)
            code: Key command code (e.g., 1 for on, 0 for off)
            
        Returns:
            True if command was successful, False otherwise
        """
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
            "Sending key command: CODESET=%d, CODE=%d to %s%s",
            codeset,
            code,
            self.base_url,
            ENDPOINT_KEY_COMMAND,
        )
        response = await self._request("PUT", ENDPOINT_KEY_COMMAND, data)
        if response:
            status = response.get("STATUS", {})
            result = status.get("RESULT", "").upper() if status.get("RESULT") else ""
            detail = status.get("DETAIL", "Unknown")
            uri = response.get("URI", "Unknown")
            time = response.get("TIME", "Unknown")
            
            _LOGGER.debug(
                "Key command response: CODESET=%d, CODE=%d, RESULT=%s, DETAIL=%s, URI=%s, TIME=%s",
                codeset,
                code,
                result,
                detail,
                uri,
                time,
            )
            _LOGGER.debug("Full key command response: %s", response)
            
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
                    "Key command failed: CODESET=%d, CODE=%d, RESULT=%s, DETAIL=%s",
                    codeset,
                    code,
                    result,
                    detail,
                )
                _LOGGER.debug("Failed key command full response: %s", response)
                return False
        else:
            _LOGGER.warning(
                "Key command request failed: CODESET=%d, CODE=%d (no response from API, host=%s:%d)",
                codeset,
                code,
                self.host,
                self.port,
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
        - VALUE: ITEMS[x].NAME from name_input endpoint (or lowercase CNAME)
        - HASHVAL: Current HashValue from ITEMS[0].HASHVAL of current_input GET response
        
        Some TV models don't provide HASHVAL in ITEMS[0], making input selection impossible.
        """
        # Step 1: Get current_input to extract HASHVAL from ITEMS[0]
        # Per API docs and user feedback: HASHVAL should be in ITEMS[0].HASHVAL
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
            _LOGGER.warning(
                "Could not extract current input HASHVAL from ITEMS[0].HASHVAL. "
                "This TV model may not support programmatic input selection. "
                "The current_input endpoint must return ITEMS[0].HASHVAL for input selection to work."
            )
            return False
        
        # Step 2: Get input list to find target input NAME
        input_list = await self.get_input_list()
        if not input_list:
            _LOGGER.warning("Could not retrieve input list for input selection")
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
            _LOGGER.warning("Input '%s' not found in available inputs", input_name)
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
        
        _LOGGER.debug(
            "Setting input: VALUE=%s, HASHVAL=%d (from ITEMS[0] of current_input)",
            target_value,
            current_hashval,
        )
        
        response = await self._request("PUT", ENDPOINT_CHANGE_INPUT, data)
        
        if response:
            status = response.get("STATUS", {})
            result = status.get("RESULT")
            if result == "SUCCESS":
                _LOGGER.debug("Successfully changed input to %s", input_name)
                return True
            else:
                _LOGGER.debug(
                    "Input change failed: %s - %s",
                    result,
                    status.get("DETAIL", "Unknown error"),
                )
        
        return False

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

    async def volume_up(self, num: int = 1) -> bool:
        """Increase volume."""
        for _ in range(num):
            if not await self._send_key_command(KEY_CODESET_VOLUME, KEY_CODE_VOLUME_UP):
                return False
        return True

    async def volume_down(self, num: int = 1) -> bool:
        """Decrease volume."""
        for _ in range(num):
            if not await self._send_key_command(KEY_CODESET_VOLUME, KEY_CODE_VOLUME_DOWN):
                return False
        return True

    async def mute(self, mute_on: bool = True) -> bool:
        """Toggle mute."""
        return await self._send_key_command(KEY_CODESET_VOLUME, KEY_CODE_MUTE)

    async def get_volume_level(self) -> int | None:
        """Get current volume level."""
        # This would require parsing the audio settings response
        # For now, return None - we'll use pyvizio's method as fallback
        return None

