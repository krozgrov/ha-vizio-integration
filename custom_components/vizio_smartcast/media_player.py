"""Vizio SmartCast Device support."""

from __future__ import annotations

from datetime import timedelta
import logging
import asyncio

from pyvizio import AppConfig, VizioAsync
from pyvizio.api.apps import find_app_name
from pyvizio.const import APP_HOME, INPUT_APPS, NO_APP_RUNNING, UNKNOWN_APP

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_DEVICE_CLASS,
    CONF_EXCLUDE,
    CONF_HOST,
    CONF_INCLUDE,
    CONF_NAME,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_ADDITIONAL_CONFIGS,
    CONF_APPS,
    CONF_VOLUME_STEP,
    DEFAULT_TIMEOUT,
    DEFAULT_VOLUME_STEP,
    DEVICE_ID,
    DOMAIN,
    SERVICE_UPDATE_SETTING,
    SUPPORTED_COMMANDS,
    UPDATE_SETTING_SCHEMA,
    VIZIO_AUDIO_SETTINGS,
    VIZIO_DEVICE_CLASSES,
    VIZIO_MUTE,
    VIZIO_MUTE_ON,
    VIZIO_SOUND_MODE,
    VIZIO_VOLUME,
)
from .coordinator import VizioAppsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)
PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up a Vizio media player entry."""
    host = config_entry.data[CONF_HOST]
    token = config_entry.data.get(CONF_ACCESS_TOKEN)
    name = config_entry.data[CONF_NAME]
    device_class = config_entry.data[CONF_DEVICE_CLASS]

    # If config entry options not set up, set them up,
    # otherwise assign values managed in options
    volume_step = config_entry.options.get(
        CONF_VOLUME_STEP, config_entry.data.get(CONF_VOLUME_STEP, DEFAULT_VOLUME_STEP)
    )

    params = {}
    if not config_entry.options:
        params["options"] = {CONF_VOLUME_STEP: volume_step}

        include_or_exclude_key = next(
            (
                key
                for key in config_entry.data.get(CONF_APPS, {})
                if key in (CONF_INCLUDE, CONF_EXCLUDE)
            ),
            None,
        )
        if include_or_exclude_key:
            params["options"][CONF_APPS] = {
                include_or_exclude_key: config_entry.data[CONF_APPS][
                    include_or_exclude_key
                ].copy()
            }

    if not config_entry.data.get(CONF_VOLUME_STEP):
        new_data = config_entry.data.copy()
        new_data.update({CONF_VOLUME_STEP: volume_step})
        params["data"] = new_data

    if params:
        hass.config_entries.async_update_entry(
            config_entry,
            **params,  # type: ignore[arg-type]
        )

    device = VizioAsync(
        DEVICE_ID,
        host,
        name,
        auth_token=token,
        device_type=VIZIO_DEVICE_CLASSES[device_class],
        session=async_get_clientsession(hass, False),
        timeout=DEFAULT_TIMEOUT,
    )

    apps_coordinator = hass.data[DOMAIN].get(CONF_APPS)

    entity = VizioDevice(config_entry, device, name, device_class, apps_coordinator)

    async_add_entities([entity], update_before_add=True)
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_UPDATE_SETTING, UPDATE_SETTING_SCHEMA, "async_update_setting"
    )


class VizioDevice(MediaPlayerEntity):
    """Media Player implementation which performs REST requests to device."""

    _attr_has_entity_name = True
    _attr_name = None
    _received_device_info = False

    def __init__(
        self,
        config_entry: ConfigEntry,
        device: VizioAsync,
        name: str,
        device_class: MediaPlayerDeviceClass,
        apps_coordinator: VizioAppsDataUpdateCoordinator | None,
    ) -> None:
        """Initialize Vizio device."""
        self._config_entry = config_entry
        self._apps_coordinator = apps_coordinator

        self._volume_step = config_entry.options[CONF_VOLUME_STEP]
        self._current_input: str | None = None
        self._current_app_config: AppConfig | None = None
        self._available_inputs: list[str] = []
        self._available_apps: list[str] = []
        self._all_apps = apps_coordinator.data if apps_coordinator else None
        self._conf_apps = config_entry.options.get(CONF_APPS, {})
        self._additional_app_configs = config_entry.data.get(CONF_APPS, {}).get(
            CONF_ADDITIONAL_CONFIGS, []
        )
        self._device = device
        try:
            self._max_volume = float(device.get_max_volume())
        except (ValueError, TypeError, AttributeError) as err:
            _LOGGER.warning(
                "Failed to get max volume for %s, using default of 100: %s", name, err
            )
            self._max_volume = 100.0
        self._attr_assumed_state = True

        # Entity class attributes that will change with each update (we only include
        # the ones that are initialized differently from the defaults)
        self._attr_sound_mode_list = []
        self._attr_supported_features = SUPPORTED_COMMANDS[device_class]

        # Entity class attributes that will not change
        unique_id = config_entry.unique_id
        assert unique_id
        self._attr_unique_id = unique_id
        self._attr_device_class = device_class
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            manufacturer="VIZIO",
            name=name,
        )

    def _apps_list(self, apps: list[str]) -> list[str]:
        """Return process apps list based on configured filters."""
        if self._conf_apps.get(CONF_INCLUDE):
            return [app for app in apps if app in self._conf_apps[CONF_INCLUDE]]

        if self._conf_apps.get(CONF_EXCLUDE):
            return [app for app in apps if app not in self._conf_apps[CONF_EXCLUDE]]

        return apps

    async def async_update(self) -> None:
        """Retrieve latest state of the device."""
        try:
            is_on = await self._device.get_power_state(log_api_exception=False)
        except Exception as err:
            _LOGGER.debug(
                "Error getting power state for %s: %s",
                self._config_entry.data[CONF_HOST],
                err,
            )
            if self._attr_available:
                _LOGGER.warning(
                    "Lost connection to %s", self._config_entry.data[CONF_HOST]
                )
                self._attr_available = False
            return

        # Handle None response - could mean device is off or unreachable
        if is_on is None:
            # If we just turned the device off, it's expected to not respond
            if self._attr_state == MediaPlayerState.OFF:
                # Device is off, this is expected - keep it as OFF, not unavailable
                return
            # Otherwise, mark as unavailable (connection lost)
            if self._attr_available:
                _LOGGER.warning(
                    "Lost connection to %s", self._config_entry.data[CONF_HOST]
                )
                self._attr_available = False
            return

        if not self._attr_available:
            _LOGGER.warning(
                "Restored connection to %s", self._config_entry.data[CONF_HOST]
            )
            self._attr_available = True

        if not self._received_device_info:
            device_reg = dr.async_get(self.hass)
            if not self._config_entry.unique_id:
                _LOGGER.warning(
                    "Config entry %s has no unique_id, skipping device info update",
                    self._config_entry.entry_id,
                )
            else:
                device = device_reg.async_get_device(
                    identifiers={(DOMAIN, self._config_entry.unique_id)}
                )
                if device:
                    try:
                        model = await self._device.get_model_name(log_api_exception=False)
                        version = await self._device.get_version(log_api_exception=False)
                        device_reg.async_update_device(
                            device.id,
                            model=model,
                            sw_version=version,
                        )
                        self._received_device_info = True
                    except Exception as err:
                        _LOGGER.debug(
                            "Error updating device info for %s: %s",
                            self._config_entry.data[CONF_HOST],
                            err,
                        )

        if not is_on:
            self._attr_state = MediaPlayerState.OFF
            self._attr_volume_level = None
            self._attr_is_volume_muted = None
            self._current_input = None
            self._attr_app_name = None
            self._current_app_config = None
            self._attr_sound_mode = None
            return

        self._attr_state = MediaPlayerState.ON

        if audio_settings := await self._device.get_all_settings(
            VIZIO_AUDIO_SETTINGS, log_api_exception=False
        ):
            if VIZIO_VOLUME in audio_settings:
                self._attr_volume_level = (
                    float(audio_settings[VIZIO_VOLUME]) / self._max_volume
                )
            else:
                self._attr_volume_level = None
            if VIZIO_MUTE in audio_settings:
                self._attr_is_volume_muted = (
                    audio_settings[VIZIO_MUTE].lower() == VIZIO_MUTE_ON
                )
            else:
                self._attr_is_volume_muted = None

            if VIZIO_SOUND_MODE in audio_settings:
                self._attr_supported_features |= (
                    MediaPlayerEntityFeature.SELECT_SOUND_MODE
                )
                self._attr_sound_mode = audio_settings[VIZIO_SOUND_MODE]
                if not self._attr_sound_mode_list:
                    self._attr_sound_mode_list = await self._device.get_setting_options(
                        VIZIO_AUDIO_SETTINGS,
                        VIZIO_SOUND_MODE,
                        log_api_exception=False,
                    )
            else:
                # Explicitly remove MediaPlayerEntityFeature.SELECT_SOUND_MODE from supported features
                self._attr_supported_features &= (
                    ~MediaPlayerEntityFeature.SELECT_SOUND_MODE
                )

        if input_ := await self._device.get_current_input(log_api_exception=False):
            self._current_input = input_

        # If no inputs returned, end update
        if not (inputs := await self._device.get_inputs_list(log_api_exception=False)):
            return

        self._available_inputs = [input_.name for input_ in inputs]

        # Return before setting app variables if INPUT_APPS isn't in available inputs
        if self._attr_device_class == MediaPlayerDeviceClass.SPEAKER or not any(
            app for app in INPUT_APPS if app in self._available_inputs
        ):
            return

        # Create list of available known apps from known app list after
        # filtering by CONF_INCLUDE/CONF_EXCLUDE
        self._available_apps = self._apps_list(
            [app["name"] for app in self._all_apps or ()]
        )

        self._current_app_config = await self._device.get_current_app_config(
            log_api_exception=False
        )

        self._attr_app_name = find_app_name(
            self._current_app_config,
            [APP_HOME, *(self._all_apps or ()), *self._additional_app_configs],
        )

        if self._attr_app_name == NO_APP_RUNNING:
            self._attr_app_name = None

    def _get_additional_app_names(self) -> list[str]:
        """Return list of additional apps that were included in configuration.yaml."""
        return [
            additional_app["name"] for additional_app in self._additional_app_configs
        ]

    @staticmethod
    async def _async_send_update_options_signal(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> None:
        """Send update event when Vizio config entry is updated."""
        # Move this method to component level if another entity ever gets added for a
        # single config entry.
        # See here: https://github.com/home-assistant/core/pull/30653#discussion_r366426121
        async_dispatcher_send(hass, config_entry.entry_id, config_entry)

    async def _async_update_options(self, config_entry: ConfigEntry) -> None:
        """Update options if the update signal comes from this entity."""
        self._volume_step = config_entry.options[CONF_VOLUME_STEP]
        # Update so that CONF_ADDITIONAL_CONFIGS gets retained for imports
        self._conf_apps.update(config_entry.options.get(CONF_APPS, {}))

    async def async_update_setting(
        self, setting_type: str, setting_name: str, new_value: int | str
    ) -> None:
        """Update a setting when update_setting service is called."""
        await self._device.set_setting(
            setting_type,
            setting_name,
            new_value,
            log_api_exception=False,
        )

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""
        # Register callback for when config entry is updated.
        self.async_on_remove(
            self._config_entry.add_update_listener(
                self._async_send_update_options_signal
            )
        )

        # Register callback for update event
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, self._config_entry.entry_id, self._async_update_options
            )
        )

        if not self._apps_coordinator:
            return

        # Register callback for app list updates if device is a TV
        @callback
        def apps_list_update() -> None:
            """Update list of all apps."""
            if not self._apps_coordinator:
                return
            self._all_apps = self._apps_coordinator.data
            self.async_write_ha_state()

        self.async_on_remove(
            self._apps_coordinator.async_add_listener(apps_list_update)
        )

    @property
    def source(self) -> str | None:
        """Return current input of the device."""
        # If we have an app name and we're on a SmartCast input, show the app name
        if self._attr_app_name is not None and self._current_input in INPUT_APPS:
            return self._attr_app_name
        
        # If we're on a SmartCast input but no app is running, show a more descriptive name
        if self._current_input in INPUT_APPS and self._attr_app_name is None:
            return f"{self._current_input} (No App)"
        
        # Otherwise, return the current input (HDMI 1, HDMI 2, etc.)
        return self._current_input

    @property
    def source_list(self) -> list[str]:
        """Return list of available inputs of the device."""
        # If Smartcast app is in input list, and the app list has been retrieved,
        # show the combination with, otherwise just return inputs
        if self._available_apps:
            return [
                *(
                    _input
                    for _input in self._available_inputs
                    if _input not in INPUT_APPS
                ),
                *self._available_apps,
                *(
                    app
                    for app in self._get_additional_app_names()
                    if app not in self._available_apps
                ),
            ]

        return self._available_inputs

    @property
    def app_id(self) -> dict[str, str] | None:
        """Return the ID of the current app if it is unknown by pyvizio."""
        if self._current_app_config and self.source == UNKNOWN_APP:
            return {
                "APP_ID": self._current_app_config.APP_ID,
                "NAME_SPACE": self._current_app_config.NAME_SPACE,
                "MESSAGE": self._current_app_config.MESSAGE,
            }

        return None

    async def async_select_sound_mode(self, sound_mode: str) -> None:
        """Select sound mode."""
        if sound_mode in (self._attr_sound_mode_list or ()):
            await self._device.set_setting(
                VIZIO_AUDIO_SETTINGS,
                VIZIO_SOUND_MODE,
                sound_mode,
                log_api_exception=False,
            )

    async def async_turn_on(self) -> None:
        """Turn the device on."""
        host = self._config_entry.data[CONF_HOST]
        max_attempts = 2
        initial_delay = 5.0  # Wait 5s after first command - allows time for TV to wake
        retry_delay = 3.0  # Wait 3s between retry attempts
        
        _LOGGER.info("Attempting to turn on %s", host)
        
        for attempt in range(max_attempts):
            try:
                _LOGGER.debug(
                    "Power on attempt %d/%d for %s",
                    attempt + 1,
                    max_attempts,
                    host,
                )
                
                # Send power on command
                await self._device.pow_on(log_api_exception=False)
                
                # Wait before checking - don't poll frequently as it can overwhelm the TV
                delay = initial_delay if attempt == 0 else retry_delay
                await asyncio.sleep(delay)
                
                # Check state once after waiting
                try:
                    power_state = await self._device.get_power_state(log_api_exception=False)
                    if power_state:
                        # Device is confirmed on
                        self._attr_state = MediaPlayerState.ON
                        self._attr_available = True
                        _LOGGER.info(
                            "Successfully turned on %s (attempt %d/%d, checked after %.1fs)",
                            host,
                            attempt + 1,
                            max_attempts,
                            delay,
                        )
                        # Force an update to get the actual state from the device
                        await self.async_update()
                        return
                    else:
                        _LOGGER.debug(
                            "Power on verification failed for %s (attempt %d/%d), device still off after %.1fs",
                            host,
                            attempt + 1,
                            max_attempts,
                            delay,
                        )
                        if attempt < max_attempts - 1:
                            # Continue to next attempt
                            continue
                        else:
                            # Last attempt failed
                            _LOGGER.warning(
                                "Power on command sent to %s %d times but device did not turn on within %.1fs",
                                host,
                                max_attempts,
                                delay,
                            )
                            # Update state optimistically anyway
                            self._attr_state = MediaPlayerState.ON
                            self._attr_available = True
                            await self.async_update()
                            return
                except Exception as verify_err:
                    # Error checking power state, but command was sent
                    _LOGGER.debug(
                        "Could not verify power state for %s (attempt %d/%d): %s",
                        host,
                        attempt + 1,
                        max_attempts,
                        verify_err,
                    )
                    if attempt < max_attempts - 1:
                        # Continue to next attempt
                        continue
                    else:
                        # Last attempt, update state optimistically
                        _LOGGER.warning(
                            "Could not verify power state for %s after %d attempts, updating optimistically",
                            host,
                            max_attempts,
                        )
                        self._attr_state = MediaPlayerState.ON
                        self._attr_available = True
                        await self.async_update()
                        return
                        
            except Exception as err:
                _LOGGER.warning(
                    "Error turning on %s (attempt %d/%d): %s",
                    host,
                    attempt + 1,
                    max_attempts,
                    err,
                )
                if attempt < max_attempts - 1:
                    # Wait before retry
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    # Last attempt failed
                    _LOGGER.error(
                        "Failed to turn on %s after %d attempts: %s",
                        host,
                        max_attempts,
                        err,
                    )
                    # Still try to update state even if command failed
                    self._attr_state = MediaPlayerState.ON
                    self._attr_available = True
                    await self.async_update()
                    return

    async def async_turn_off(self) -> None:
        """Turn the device off."""
        host = self._config_entry.data[CONF_HOST]
        max_attempts = 3
        
        _LOGGER.info("Attempting to turn off %s", host)
        
        for attempt in range(max_attempts):
            try:
                _LOGGER.debug(
                    "Power off attempt %d/%d for %s",
                    attempt + 1,
                    max_attempts,
                    host,
                )
                
                await self._device.pow_off(log_api_exception=False)
                
                # Wait a moment for device to respond
                await asyncio.sleep(1.0)
                
                # Verify the device turned off
                try:
                    power_state = await self._device.get_power_state(log_api_exception=False)
                    if not power_state:
                        # Device is confirmed off
                        self._attr_state = MediaPlayerState.OFF
                        # When device is off, clear volume and other state
                        self._attr_volume_level = None
                        self._attr_is_volume_muted = None
                        self._current_input = None
                        self._attr_app_name = None
                        self._current_app_config = None
                        self._attr_sound_mode = None
                        self._attr_available = True
                        _LOGGER.info(
                            "Successfully turned off %s (attempt %d/%d)",
                            host,
                            attempt + 1,
                            max_attempts,
                        )
                        # Try to update, but don't mark unavailable if it fails (device is off)
                        try:
                            await self.async_update()
                        except Exception:
                            # Device is off, can't query state - this is expected
                            pass
                        return
                    else:
                        _LOGGER.debug(
                            "Power off verification failed for %s (attempt %d/%d), device still on",
                            host,
                            attempt + 1,
                            max_attempts,
                        )
                        if attempt < max_attempts - 1:
                            continue
                        else:
                            # Some TVs don't respond to power off via API
                            _LOGGER.warning(
                                "Power off command sent to %s %d times but device may not support remote power off",
                                host,
                                max_attempts,
                            )
                            # Update state optimistically anyway
                            self._attr_state = MediaPlayerState.OFF
                            self._attr_volume_level = None
                            self._attr_is_volume_muted = None
                            self._current_input = None
                            self._attr_app_name = None
                            self._current_app_config = None
                            self._attr_sound_mode = None
                            self._attr_available = True
                            try:
                                await self.async_update()
                            except Exception:
                                pass
                            return
                except Exception as verify_err:
                    # Error checking power state, but command was sent
                    _LOGGER.debug(
                        "Could not verify power state for %s (attempt %d/%d): %s",
                        host,
                        attempt + 1,
                        max_attempts,
                        verify_err,
                    )
                    if attempt < max_attempts - 1:
                        continue
                    else:
                        # Update state optimistically
                        self._attr_state = MediaPlayerState.OFF
                        self._attr_volume_level = None
                        self._attr_is_volume_muted = None
                        self._current_input = None
                        self._attr_app_name = None
                        self._current_app_config = None
                        self._attr_sound_mode = None
                        self._attr_available = True
                        try:
                            await self.async_update()
                        except Exception:
                            pass
                        return
                        
            except Exception as err:
                _LOGGER.warning(
                    "Error turning off %s (attempt %d/%d): %s",
                    host,
                    attempt + 1,
                    max_attempts,
                    err,
                )
                if attempt < max_attempts - 1:
                    await asyncio.sleep(1.0)
                    continue
                else:
                    _LOGGER.error(
                        "Failed to turn off %s after %d attempts: %s",
                        host,
                        max_attempts,
                        err,
                    )
                    # Still update state even if command failed
                    self._attr_state = MediaPlayerState.OFF
                    self._attr_volume_level = None
                    self._attr_is_volume_muted = None
                    self._current_input = None
                    self._attr_app_name = None
                    self._current_app_config = None
                    self._attr_sound_mode = None
                    self._attr_available = True
                    try:
                        await self.async_update()
                    except Exception:
                        pass
                    return

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute the volume."""
        if mute:
            await self._device.mute_on(log_api_exception=False)
            self._attr_is_volume_muted = True
        else:
            await self._device.mute_off(log_api_exception=False)
            self._attr_is_volume_muted = False

    async def async_media_previous_track(self) -> None:
        """Send previous channel command."""
        await self._device.ch_down(log_api_exception=False)

    async def async_media_next_track(self) -> None:
        """Send next channel command."""
        await self._device.ch_up(log_api_exception=False)

    async def async_select_source(self, source: str) -> None:
        """Select input source."""
        try:
            if source in self._available_inputs:
                try:
                    await self._device.set_input(source, log_api_exception=False)
                except TypeError as err:
                    # Handle case where pyvizio fails due to None input ID
                    # This can happen when the current input doesn't have a valid ID
                    if "NoneType" in str(err) or "int() argument" in str(err):
                        _LOGGER.warning(
                            "Input selection failed due to invalid current input state on %s. "
                            "Refreshing inputs and retrying...",
                            self._config_entry.data[CONF_HOST],
                        )
                        # Refresh inputs and try again
                        try:
                            await self.async_update()
                            await self._device.set_input(source, log_api_exception=False)
                        except Exception as retry_err:
                            _LOGGER.error(
                                "Error selecting source %s on %s after refresh: %s",
                                source,
                                self._config_entry.data[CONF_HOST],
                                retry_err,
                            )
                    else:
                        raise
            elif source in self._get_additional_app_names():
                app_config = next(
                    (app["config"] for app in self._additional_app_configs if app["name"] == source),
                    None,
                )
                if app_config:
                    await self._device.launch_app_config(
                        **app_config,
                        log_api_exception=False,
                    )
                else:
                    _LOGGER.warning("App config not found for source: %s", source)
            elif source in self._available_apps:
                await self._device.launch_app(
                    source, self._all_apps, log_api_exception=False
                )
            else:
                _LOGGER.warning("Source not found: %s", source)
        except Exception as err:
            _LOGGER.error(
                "Error selecting source %s on %s: %s",
                source,
                self._config_entry.data[CONF_HOST],
                err,
            )

    async def async_volume_up(self) -> None:
        """Increase volume of the device."""
        try:
            await self._device.vol_up(num=self._volume_step, log_api_exception=False)
            # Update local state if we have a current volume level
            if self._attr_volume_level is not None:
                self._attr_volume_level = min(
                    1.0, self._attr_volume_level + self._volume_step / self._max_volume
                )
            # Force an update to get the actual volume from the device
            await self.async_update()
        except Exception as err:
            _LOGGER.error(
                "Error increasing volume on %s: %s",
                self._config_entry.data[CONF_HOST],
                err,
            )

    async def async_volume_down(self) -> None:
        """Decrease volume of the device."""
        try:
            await self._device.vol_down(num=self._volume_step, log_api_exception=False)
            # Update local state if we have a current volume level
            if self._attr_volume_level is not None:
                self._attr_volume_level = max(
                    0.0, self._attr_volume_level - self._volume_step / self._max_volume
                )
            # Force an update to get the actual volume from the device
            await self.async_update()
        except Exception as err:
            _LOGGER.error(
                "Error decreasing volume on %s: %s",
                self._config_entry.data[CONF_HOST],
                err,
            )

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level."""
        try:
            # Always use set_setting to set volume directly (faster and more accurate)
            volume_value = int(volume * self._max_volume)
            await self._device.set_setting(
                VIZIO_AUDIO_SETTINGS,
                VIZIO_VOLUME,
                volume_value,
                log_api_exception=False,
            )
            self._attr_volume_level = volume
            # Force an update to get the actual volume from the device
            await self.async_update()
        except Exception as err:
            _LOGGER.error(
                "Error setting volume level on %s: %s",
                self._config_entry.data[CONF_HOST],
                err,
            )

    async def async_media_play(self) -> None:
        """Play whatever media is currently active."""
        await self._device.play(log_api_exception=False)

    async def async_media_pause(self) -> None:
        """Pause whatever media is currently active."""
        await self._device.pause(log_api_exception=False)