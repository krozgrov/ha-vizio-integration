"""Device capability detection for Vizio SmartCast devices.

This module detects which methods work on each TV model by testing them during initialization.
Instead of falling back between pyvizio and direct API, we detect capabilities upfront and
use the appropriate method for each function.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from pyvizio import VizioAsync

from .vizio_api import VizioAPIClient

_LOGGER = logging.getLogger(__name__)


class VizioCapabilities:
    """Stores detected capabilities for a Vizio device."""

    def __init__(self) -> None:
        """Initialize capabilities - all unknown until detected."""
        # Power control
        self.power_state_pyvizio: bool | None = None
        self.power_state_direct_api: bool | None = None
        self.power_on_pyvizio: bool | None = None
        self.power_on_direct_api: bool | None = None
        self.power_off_pyvizio: bool | None = None
        self.power_off_direct_api: bool | None = None

        # Input selection
        self.input_list_pyvizio: bool | None = None
        self.input_list_direct_api: bool | None = None
        self.input_set_pyvizio: bool | None = None
        self.input_set_direct_api: bool | None = None
        self.current_input_pyvizio: bool | None = None
        self.current_input_direct_api: bool | None = None

        # Volume control
        self.volume_get_pyvizio: bool | None = None
        self.volume_get_direct_api: bool | None = None
        self.volume_set_pyvizio: bool | None = None
        self.volume_set_direct_api: bool | None = None

        # Device info
        self.device_info_pyvizio: bool | None = None
        self.device_info_direct_api: bool | None = None

    def get_best_method(self, operation: str) -> str:
        """Get the best method for an operation based on detected capabilities.
        
        Returns: 'pyvizio', 'direct_api', or 'none' if neither works.
        """
        capability_map = {
            "power_state": (self.power_state_pyvizio, self.power_state_direct_api),
            "power_on": (self.power_on_pyvizio, self.power_on_direct_api),
            "power_off": (self.power_off_pyvizio, self.power_off_direct_api),
            "input_list": (self.input_list_pyvizio, self.input_list_direct_api),
            "input_set": (self.input_set_pyvizio, self.input_set_direct_api),
            "current_input": (self.current_input_pyvizio, self.current_input_direct_api),
            "volume_get": (self.volume_get_pyvizio, self.volume_get_direct_api),
            "volume_set": (self.volume_set_pyvizio, self.volume_set_direct_api),
            "device_info": (self.device_info_pyvizio, self.device_info_direct_api),
        }

        pyvizio_works, direct_api_works = capability_map.get(operation, (None, None))

        # Prefer direct API if both work, fallback to pyvizio
        if direct_api_works:
            return "direct_api"
        if pyvizio_works:
            return "pyvizio"
        return "none"

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"VizioCapabilities("
            f"power_state={self.get_best_method('power_state')}, "
            f"power_on={self.get_best_method('power_on')}, "
            f"power_off={self.get_best_method('power_off')}, "
            f"input_set={self.get_best_method('input_set')}, "
            f"volume_set={self.get_best_method('volume_set')}"
            f")"
        )


async def detect_capabilities(
    device: VizioAsync, api_client: VizioAPIClient, host: str
) -> VizioCapabilities:
    """Detect which methods work on this TV by testing them.
    
    Args:
        device: pyvizio device instance
        api_client: Direct API client instance
        host: Device hostname/IP for logging
        
    Returns:
        VizioCapabilities object with detected capabilities
    """
    capabilities = VizioCapabilities()
    _LOGGER.info("Detecting capabilities for %s...", host)

    # Test power state
    _LOGGER.debug("Testing power state methods...")
    try:
        await device.get_power_state(log_api_exception=False)
        capabilities.power_state_pyvizio = True
        _LOGGER.debug("  ✓ pyvizio.get_power_state() works")
    except Exception as err:
        capabilities.power_state_pyvizio = False
        _LOGGER.debug("  ✗ pyvizio.get_power_state() failed: %s", err)

    try:
        await api_client.get_power_state()
        capabilities.power_state_direct_api = True
        _LOGGER.debug("  ✓ direct_api.get_power_state() works")
    except Exception as err:
        capabilities.power_state_direct_api = False
        _LOGGER.debug("  ✗ direct_api.get_power_state() failed: %s", err)

    # Test power on (only if device is off)
    try:
        current_state = await api_client.get_power_state()
        if not current_state:
            _LOGGER.debug("Testing power on methods (device is off)...")
            # Test direct API first (safer - we can verify it worked)
            try:
                success = await api_client.power_on()
                if success:
                    # Wait a moment and verify
                    await asyncio.sleep(2)
                    if await api_client.get_power_state():
                        capabilities.power_on_direct_api = True
                        _LOGGER.debug("  ✓ direct_api.power_on() works")
                        # Turn it back off for pyvizio test
                        await api_client.power_off()
                        await asyncio.sleep(1)
                    else:
                        capabilities.power_on_direct_api = False
                        _LOGGER.debug("  ✗ direct_api.power_on() failed (no state change)")
                else:
                    capabilities.power_on_direct_api = False
                    _LOGGER.debug("  ✗ direct_api.power_on() returned False")
            except Exception as err:
                capabilities.power_on_direct_api = False
                _LOGGER.debug("  ✗ direct_api.power_on() failed: %s", err)

            # Test pyvizio
            try:
                await device.pow_on(log_api_exception=False)
                await asyncio.sleep(2)
                if await api_client.get_power_state():
                    capabilities.power_on_pyvizio = True
                    _LOGGER.debug("  ✓ pyvizio.pow_on() works")
                else:
                    capabilities.power_on_pyvizio = False
                    _LOGGER.debug("  ✗ pyvizio.pow_on() failed (no state change)")
            except Exception as err:
                capabilities.power_on_pyvizio = False
                _LOGGER.debug("  ✗ pyvizio.pow_on() failed: %s", err)
        else:
            _LOGGER.debug("Skipping power on test (device is already on)")
    except Exception as err:
        _LOGGER.debug("Could not test power on: %s", err)

    # Test power off (only if device is on)
    try:
        current_state = await api_client.get_power_state()
        if current_state:
            _LOGGER.debug("Testing power off methods (device is on)...")
            # Test direct API first
            try:
                success = await api_client.power_off()
                if success:
                    await asyncio.sleep(1)
                    if not await api_client.get_power_state():
                        capabilities.power_off_direct_api = True
                        _LOGGER.debug("  ✓ direct_api.power_off() works")
                        # Turn it back on for pyvizio test
                        await api_client.power_on()
                        await asyncio.sleep(2)
                    else:
                        capabilities.power_off_direct_api = False
                        _LOGGER.debug("  ✗ direct_api.power_off() failed (no state change)")
                else:
                    capabilities.power_off_direct_api = False
                    _LOGGER.debug("  ✗ direct_api.power_off() returned False")
            except Exception as err:
                capabilities.power_off_direct_api = False
                _LOGGER.debug("  ✗ direct_api.power_off() failed: %s", err)

            # Test pyvizio
            try:
                await device.pow_off(log_api_exception=False)
                await asyncio.sleep(1)
                if not await api_client.get_power_state():
                    capabilities.power_off_pyvizio = True
                    _LOGGER.debug("  ✓ pyvizio.pow_off() works")
                else:
                    capabilities.power_off_pyvizio = False
                    _LOGGER.debug("  ✗ pyvizio.pow_off() failed (no state change)")
            except Exception as err:
                capabilities.power_off_pyvizio = False
                _LOGGER.debug("  ✗ pyvizio.pow_off() failed: %s", err)
        else:
            _LOGGER.debug("Skipping power off test (device is already off)")
    except Exception as err:
        _LOGGER.debug("Could not test power off: %s", err)

    # Test input list
    _LOGGER.debug("Testing input list methods...")
    try:
        inputs = await device.get_inputs_list(log_api_exception=False)
        if inputs and len(inputs) > 0:
            capabilities.input_list_pyvizio = True
            _LOGGER.debug("  ✓ pyvizio.get_inputs_list() works (%d inputs)", len(inputs))
        else:
            capabilities.input_list_pyvizio = False
            _LOGGER.debug("  ✗ pyvizio.get_inputs_list() returned empty")
    except Exception as err:
        capabilities.input_list_pyvizio = False
        _LOGGER.debug("  ✗ pyvizio.get_inputs_list() failed: %s", err)

    try:
        inputs = await api_client.get_input_list()
        if inputs and len(inputs) > 0:
            capabilities.input_list_direct_api = True
            _LOGGER.debug("  ✓ direct_api.get_input_list() works (%d inputs)", len(inputs))
        else:
            capabilities.input_list_direct_api = False
            _LOGGER.debug("  ✗ direct_api.get_input_list() returned empty")
    except Exception as err:
        capabilities.input_list_direct_api = False
        _LOGGER.debug("  ✗ direct_api.get_input_list() failed: %s", err)

    # Test current input
    _LOGGER.debug("Testing current input methods...")
    try:
        current = await device.get_current_input(log_api_exception=False)
        if current is not None:
            capabilities.current_input_pyvizio = True
            _LOGGER.debug("  ✓ pyvizio.get_current_input() works: %s", current)
        else:
            capabilities.current_input_pyvizio = False
            _LOGGER.debug("  ✗ pyvizio.get_current_input() returned None")
    except Exception as err:
        capabilities.current_input_pyvizio = False
        _LOGGER.debug("  ✗ pyvizio.get_current_input() failed: %s", err)

    try:
        current = await api_client.get_current_input()
        if current is not None:
            capabilities.current_input_direct_api = True
            _LOGGER.debug("  ✓ direct_api.get_current_input() works: %s", current)
        else:
            capabilities.current_input_direct_api = False
            _LOGGER.debug("  ✗ direct_api.get_current_input() returned None")
    except Exception as err:
        capabilities.current_input_direct_api = False
        _LOGGER.debug("  ✗ direct_api.get_current_input() failed: %s", err)

    # Test input set (only if we have inputs and device is on)
    try:
        current_state = await api_client.get_power_state()
        if current_state:
            inputs = await api_client.get_input_list()
            if inputs and len(inputs) > 1:
                # Get current input
                current_input = await api_client.get_current_input()
                if current_input:
                    current_name = current_input.get("name", "")
                    # Find a different input to switch to
                    target_input = None
                    for inp in inputs:
                        if inp.get("name") != current_name:
                            target_input = inp.get("name")
                            break

                    if target_input:
                        _LOGGER.debug(
                            "Testing input set methods (switching from %s to %s)...",
                            current_name,
                            target_input,
                        )
                        # Test direct API
                        try:
                            success = await api_client.set_input(target_input)
                            if success:
                                await asyncio.sleep(1)
                                # Verify it changed
                                new_input = await api_client.get_current_input()
                                if new_input and new_input.get("name") == target_input:
                                    capabilities.input_set_direct_api = True
                                    _LOGGER.debug("  ✓ direct_api.set_input() works")
                                    # Switch back
                                    await api_client.set_input(current_name)
                                    await asyncio.sleep(1)
                                else:
                                    capabilities.input_set_direct_api = False
                                    _LOGGER.debug(
                                        "  ✗ direct_api.set_input() failed (no change)"
                                    )
                            else:
                                capabilities.input_set_direct_api = False
                                _LOGGER.debug("  ✗ direct_api.set_input() returned False")
                        except Exception as err:
                            capabilities.input_set_direct_api = False
                            _LOGGER.debug("  ✗ direct_api.set_input() failed: %s", err)

                        # Test pyvizio
                        try:
                            await device.set_input(target_input, log_api_exception=False)
                            await asyncio.sleep(1)
                            new_input = await api_client.get_current_input()
                            if new_input and new_input.get("name") == target_input:
                                capabilities.input_set_pyvizio = True
                                _LOGGER.debug("  ✓ pyvizio.set_input() works")
                                # Switch back
                                await device.set_input(current_name, log_api_exception=False)
                                await asyncio.sleep(1)
                            else:
                                capabilities.input_set_pyvizio = False
                                _LOGGER.debug("  ✗ pyvizio.set_input() failed (no change)")
                        except Exception as err:
                            capabilities.input_set_pyvizio = False
                            _LOGGER.debug("  ✗ pyvizio.set_input() failed: %s", err)
    except Exception as err:
        _LOGGER.debug("Could not test input set: %s", err)

    # Test volume get
    _LOGGER.debug("Testing volume get methods...")
    try:
        settings = await device.get_all_settings(log_api_exception=False)
        if settings and "volume" in settings:
            capabilities.volume_get_pyvizio = True
            _LOGGER.debug("  ✓ pyvizio.get_all_settings() works for volume")
        else:
            capabilities.volume_get_pyvizio = False
            _LOGGER.debug("  ✗ pyvizio.get_all_settings() missing volume")
    except Exception as err:
        capabilities.volume_get_pyvizio = False
        _LOGGER.debug("  ✗ pyvizio.get_all_settings() failed: %s", err)

    try:
        settings = await api_client.get_audio_settings()
        if settings and "volume" in settings:
            capabilities.volume_get_direct_api = True
            _LOGGER.debug("  ✓ direct_api.get_audio_settings() works for volume")
        else:
            capabilities.volume_get_direct_api = False
            _LOGGER.debug("  ✗ direct_api.get_audio_settings() missing volume")
    except Exception as err:
        capabilities.volume_get_direct_api = False
        _LOGGER.debug("  ✗ direct_api.get_audio_settings() failed: %s", err)

    # Test device info
    _LOGGER.debug("Testing device info methods...")
    try:
        model = await device.get_model_name(log_api_exception=False)
        if model:
            capabilities.device_info_pyvizio = True
            _LOGGER.debug("  ✓ pyvizio.get_model_name() works: %s", model)
        else:
            capabilities.device_info_pyvizio = False
            _LOGGER.debug("  ✗ pyvizio.get_model_name() returned None")
    except Exception as err:
        capabilities.device_info_pyvizio = False
        _LOGGER.debug("  ✗ pyvizio.get_model_name() failed: %s", err)

    try:
        model = await api_client.get_model_name()
        if model:
            capabilities.device_info_direct_api = True
            _LOGGER.debug("  ✓ direct_api.get_model_name() works: %s", model)
        else:
            capabilities.device_info_direct_api = False
            _LOGGER.debug("  ✗ direct_api.get_model_name() returned None")
    except Exception as err:
        capabilities.device_info_direct_api = False
        _LOGGER.debug("  ✗ direct_api.get_model_name() failed: %s", err)

    _LOGGER.info("Capability detection complete for %s: %s", host, capabilities)
    return capabilities

