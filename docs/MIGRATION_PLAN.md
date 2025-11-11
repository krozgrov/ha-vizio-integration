# Vizio SmartCast Integration Migration Plan

## Overview

This document outlines the plan to migrate the Vizio SmartCast Home Assistant integration from relying on the `pyvizio` library to using direct API calls based on the [Vizio SmartCast API documentation](https://github.com/exiva/Vizio_SmartCast_API).

## Current State Analysis

### Current `pyvizio` Dependencies

The integration currently uses `pyvizio` for:

#### Setup Operations (Keep using pyvizio) ✅
1. **Pairing & Authentication** (Config Flow Only)
   - `start_pair()` - Initiate pairing process
   - `pair()` - Complete pairing with PIN
   - `validate_ha_config()` - Validate device configuration

2. **Device Discovery & Identification** (Config Flow Only)
   - `async_guess_device_type()` - Detect TV vs Speaker
   - `get_unique_id()` - Get device unique identifier

#### Runtime Operations (Migrate to Direct API) 🔄
3. **Power Control** - ✅ **MIGRATED** (using direct API)
   - `get_power_state()` - Check if device is on/off
   - `pow_on()` - Turn device on
   - `pow_off()` - Turn device off

4. **Volume Control** - 🔄 **PARTIAL** (basic commands migrated, level retrieval pending)
   - `vol_up()` / `vol_down()` - Adjust volume ✅
   - `mute_on()` / `mute_off()` - Mute/unmute ✅
   - `get_max_volume()` - Get maximum volume level ⏳
   - `get_all_settings()` - Get audio settings (volume, mute, EQ) ⏳

5. **Input Management** - ✅ **MIGRATED** (using direct API)
   - `get_current_input()` - Get active input
   - `get_inputs_list()` - List available inputs
   - `set_input()` - Change input

6. **App Management** - ⏳ **PENDING**
   - `get_current_app_config()` - Get current running app
   - `launch_app()` - Launch app by name
   - `launch_app_config()` - Launch app with custom config

7. **Settings Management** - ⏳ **PENDING**
   - `set_setting()` - Update device settings
   - `get_setting_options()` - Get available setting values

8. **App List Retrieval** - ⏳ **PENDING**
   - `gen_apps_list_from_url()` - Fetch app list from external server
   - Constants: `APPS`, `APP_HOME`, `INPUT_APPS`, etc.

### Already Implemented Direct API

The `vizio_api.py` module already implements:
- ✅ Power state (`get_power_state`, `power_on`, `power_off`)
- ✅ Input management (`get_current_input`, `get_input_list`, `set_input`)
- ✅ Basic volume commands (`volume_up`, `volume_down`, `mute`)
- ⚠️ Volume level retrieval (returns `None` - needs implementation)

## Migration Strategy

### Hybrid Approach: Keep pyvizio for Setup, Migrate Runtime Operations

**Decision**: Keep `pyvizio` for pairing/auth and device discovery in config flow, migrate all runtime operations to direct API.

**Rationale**:
- Pairing is critical and only used during one-time setup
- Device discovery is also setup-only
- Reduces risk by keeping proven pairing logic
- Can migrate pairing later if needed
- Focuses migration effort on frequently-used operations

### Phase 1: Complete Direct API Client (Runtime Operations)
**Goal**: Build a complete, robust direct API client for all runtime operations

#### 1.1 Pairing & Authentication
**Status**: ⏸️ **DEFERRED** - Keep using `pyvizio` for now
- Pairing is only used during setup (one-time operation)
- Current `pyvizio` implementation works reliably
- Can migrate later if `pyvizio` becomes problematic
- Low priority since it's not used during normal operation

**Future Implementation** (if needed):
- [ ] Implement `start_pairing()` - `PUT /pairing/start`
- [ ] Implement `complete_pairing()` - `PUT /pairing/pair`
- [ ] Implement `cancel_pairing()` - `PUT /pairing/cancel`
- [ ] Implement `validate_config()` - Test connection with token

#### 1.2 Device Discovery & Identification
**Status**: ⏸️ **DEFERRED** - Keep using `pyvizio` for now
- `async_guess_device_type()` - Used in config flow
- `get_unique_id()` - Used in config flow
- `validate_ha_config()` - Used in config flow
- These are setup-only operations, low priority for migration

**Future Implementation** (if needed):
- [ ] Implement `get_unique_id()` - Query device info endpoint
- [ ] Implement `guess_device_type()` - Determine TV vs Speaker from device info
- [ ] Add device info endpoint: `GET /state/device/info` or similar

#### 1.3 Volume Control (Complete)
- [ ] Implement `get_volume_level()` - Parse audio settings
- [ ] Implement `get_max_volume()` - Get max volume from device
- [ ] Implement `get_audio_settings()` - `GET /menu_native/dynamic/tv_settings/audio`
- [ ] Implement `set_audio_setting()` - `PUT /menu_native/dynamic/tv_settings/audio/{setting_name}`
- [ ] Enhance `mute()` to support mute on/off (currently just toggles)

**API Reference**:
- Audio settings: `GET /menu_native/dynamic/tv_settings/audio`
- Set audio setting: `PUT /menu_native/dynamic/tv_settings/audio/{setting_name}` with `{"REQUEST": "MODIFY", "VALUE": value, "HASHVAL": hashval}`

#### 1.4 Settings Management
- [ ] Implement `get_setting()` - Generic setting retrieval
- [ ] Implement `set_setting()` - Generic setting update
- [ ] Implement `get_setting_options()` - Get available values for a setting
- [ ] Support different setting types (audio, video, etc.)

**API Reference**:
- Settings follow pattern: `/menu_native/dynamic/tv_settings/{setting_type}/{setting_name}`
- Use `REQUEST: MODIFY`, `VALUE`, and `HASHVAL` for updates

#### 1.5 App Management
- [ ] Implement `get_current_app()` - Get currently running app
- [ ] Implement `launch_app()` - Launch app by app_id
- [ ] Implement `launch_app_by_name()` - Launch app by name (lookup app_id first)
- [ ] Parse app config from `get_current_input()` when on SmartCast input

**API Reference**:
- Launch app: `PUT /app/launch` with `{"APP_ID": "...", "NAME_SPACE": "...", "MESSAGE": "..."}`
- Current app: Check `current_input` - if SmartCast input, query app info

#### 1.6 Constants & Utilities
- [ ] Extract constants from `pyvizio` or define new ones
- [ ] Implement `find_app_name()` utility
- [ ] Implement app list parsing from external URL
- [ ] Define `INPUT_APPS`, `APP_HOME`, etc.

**API Reference**:
- App list: `http://hometest.buddytv.netdna-cdn.com/appservice/vizio_apps_prod.json`
- App availability: `http://hometest.buddytv.netdna-cdn.com/appservice/app_availability_prod.json`

### Phase 2: Migrate Config Flow
**Status**: ⏸️ **DEFERRED** - Keep using `pyvizio` for setup operations

**Decision**: Keep `pyvizio` for config flow operations:
- ✅ Keep `VizioAsync.get_unique_id()` - Works reliably
- ✅ Keep `async_guess_device_type()` - Works reliably  
- ✅ Keep `VizioAsync.validate_ha_config()` - Works reliably
- ✅ Keep `dev.start_pair()` and `dev.pair()` - Critical setup operation

**Rationale**:
- These operations are only used during one-time setup
- Current implementation is proven and reliable
- Low risk to keep them as-is
- Can migrate later if `pyvizio` becomes unavailable or problematic

**Future Migration** (if needed):
- [ ] Replace `VizioAsync.get_unique_id()` with direct API call
- [ ] Replace `async_guess_device_type()` with direct API call
- [ ] Replace `VizioAsync.validate_ha_config()` with direct API validation
- [ ] Replace `dev.start_pair()` and `dev.pair()` with direct API calls
- [ ] Update error handling for pairing flow
- [ ] Test pairing flow end-to-end

### Phase 3: Migrate Media Player Entity
**Goal**: Replace `pyvizio` usage in media player entity

- [ ] Replace `VizioAsync` initialization with `VizioAPIClient`
- [ ] Migrate `async_update()` to use direct API:
  - [ ] Power state (already done)
  - [ ] Audio settings (volume, mute, sound mode)
  - [ ] Current input
  - [ ] Input list
  - [ ] Current app
- [ ] Migrate `async_turn_on()` / `async_turn_off()` (already done, verify)
- [ ] Migrate `async_volume_up()` / `async_volume_down()` / `async_set_volume_level()`
- [ ] Migrate `async_mute_volume()`
- [ ] Migrate `async_select_source()` (partially done, complete)
- [ ] Migrate `async_select_sound_mode()`
- [ ] Migrate `async_update_setting()`
- [ ] Migrate app launching (`async_select_source()` for apps)
- [ ] Update device info retrieval (`get_model_name()`, `get_version()`)

### Phase 4: Migrate Coordinator
**Goal**: Replace app list retrieval

- [ ] Replace `gen_apps_list_from_url()` with direct HTTP call
- [ ] Replace `APPS` constant import
- [ ] Update app list parsing logic

### Phase 5: Minimize pyvizio Dependency
**Goal**: Keep `pyvizio` only for setup operations, remove from runtime

- [ ] Keep `pyvizio` in `requirements.txt` (still needed for config flow)
- [ ] Keep `pyvizio` in `manifest.json` (still needed for config flow)
- [ ] Remove `pyvizio` imports from `media_player.py` (runtime operations)
- [ ] Remove `pyvizio` imports from `coordinator.py` (runtime operations)
- [ ] Keep `pyvizio` imports only in `config_flow.py` (setup operations)
- [ ] Update documentation to reflect hybrid approach
- [ ] Test all functionality
- [ ] Create migration guide for users

**Note**: `pyvizio` will remain as a dependency but only used during setup/configuration, not during normal operation.

### Phase 6: Testing & Validation
**Goal**: Ensure reliability across different Vizio models

- [ ] Test on multiple Vizio models (TVs and Speakers)
- [ ] Test pairing flow
- [ ] Test power on/off
- [ ] Test volume control
- [ ] Test input switching
- [ ] Test app launching
- [ ] Test settings updates
- [ ] Test error handling and edge cases
- [ ] Performance testing (response times, retries)

## Implementation Details

### API Client Structure

```python
class VizioAPIClient:
    """Complete direct API client for Vizio SmartCast devices."""
    
    # Pairing
    async def start_pairing(device_name: str, device_id: str) -> PairingData
    async def complete_pairing(device_id: str, challenge_type: int, pin: str, token: int) -> str  # Returns auth_token
    async def cancel_pairing(device_id: str, challenge_type: int, token: int) -> bool
    
    # Device Info
    async def get_device_info() -> dict
    async def get_unique_id() -> str | None
    async def get_model_name() -> str | None
    async def get_version() -> str | None
    async def guess_device_type() -> str  # "tv" or "speaker"
    
    # Power
    async def get_power_state() -> bool | None  # ✅ Done
    async def power_on() -> bool  # ✅ Done
    async def power_off() -> bool  # ✅ Done
    
    # Volume & Audio
    async def get_volume_level() -> int | None  # ⚠️ Needs implementation
    async def get_max_volume() -> int
    async def set_volume_level(level: int) -> bool
    async def volume_up(num: int = 1) -> bool  # ✅ Done
    async def volume_down(num: int = 1) -> bool  # ✅ Done
    async def mute(mute_on: bool = True) -> bool  # ✅ Done (needs enhancement)
    async def get_audio_settings() -> dict
    async def set_audio_setting(setting_name: str, value: Any) -> bool
    async def get_sound_mode_options() -> list[str]
    
    # Inputs
    async def get_current_input() -> dict | None  # ✅ Done
    async def get_input_list() -> list[dict]  # ✅ Done
    async def set_input(input_name: str) -> bool  # ✅ Done
    
    # Apps
    async def get_current_app() -> dict | None
    async def launch_app(app_id: str, name_space: str, message: str) -> bool
    async def launch_app_by_name(app_name: str, app_list: list) -> bool
    
    # Settings (Generic)
    async def get_setting(setting_type: str, setting_name: str) -> Any
    async def set_setting(setting_type: str, setting_name: str, value: Any) -> bool
    async def get_setting_options(setting_type: str, setting_name: str) -> list
```

### Constants to Define

```python
# Device Types
DEVICE_CLASS_TV = "tv"
DEVICE_CLASS_SPEAKER = "speaker"

# Input Types
INPUT_APPS = ["CAST", "SmartCast"]  # SmartCast inputs
APP_HOME = {"name": "Home", "APP_ID": "0", ...}

# App States
NO_APP_RUNNING = "NO_APP_RUNNING"
UNKNOWN_APP = "UNKNOWN_APP"

# Audio Settings
VIZIO_VOLUME = "volume"
VIZIO_MUTE = "mute"
VIZIO_SOUND_MODE = "eq"

# API Endpoints
ENDPOINT_PAIRING_START = "/pairing/start"
ENDPOINT_PAIRING_PAIR = "/pairing/pair"
ENDPOINT_PAIRING_CANCEL = "/pairing/cancel"
ENDPOINT_DEVICE_INFO = "/state/device/info"  # May need to verify
ENDPOINT_POWER_MODE = "/state/device/power_mode"
ENDPOINT_CURRENT_INPUT = "/state/device/current_input"
ENDPOINT_INPUT_LIST = "/menu_native/dynamic/tv_settings/devices/name_input"
ENDPOINT_CHANGE_INPUT = "/menu_native/dynamic/tv_settings/devices/current_input"
ENDPOINT_AUDIO_SETTINGS = "/menu_native/dynamic/tv_settings/audio"
ENDPOINT_APP_LAUNCH = "/app/launch"
```

### Error Handling Strategy

1. **Connection Errors**: Retry with exponential backoff
2. **Authentication Errors**: Trigger reauth flow
3. **API Errors**: Parse `STATUS.RESULT` and `STATUS.DETAIL` from responses
4. **Timeout Errors**: Implement configurable timeouts
5. **SSL Errors**: Continue using `ssl=False` for self-signed certs

### Backward Compatibility

- Maintain same Home Assistant entity interface
- Keep same config entry structure
- Preserve user settings and options
- No breaking changes to user-facing features

## Benefits of Hybrid Migration Approach

1. **Reduced Risk**: Keep proven pairing logic, migrate only runtime operations
2. **Faster Migration**: Focus on frequently-used operations first
3. **Reliability**: Direct control over runtime API calls and error handling
4. **Model Support**: Better support for different Vizio models in runtime operations
5. **Performance**: Optimized API calls without library overhead for runtime
6. **Maintainability**: Full control over runtime codebase
7. **Debugging**: Easier to debug runtime issues with direct API calls
8. **Future-Proofing**: Can adapt runtime API changes quickly
9. **Stability**: Keep setup flow stable while improving runtime operations
10. **Gradual Migration**: Can migrate pairing later if needed without breaking setup

## Risks & Mitigation

1. **API Changes**: Vizio may change API endpoints
   - *Mitigation*: Monitor API responses, add version detection
   
2. **Model Differences**: Different models may behave differently
   - *Mitigation*: Extensive testing, model-specific handling if needed
   
3. **Pairing Complexity**: Pairing flow is critical for setup
   - *Mitigation*: Thorough testing, clear error messages, fallback options
   
4. **Breaking Changes**: Migration might break existing installations
   - *Mitigation*: Phased rollout, maintain backward compatibility during transition

## Timeline Estimate (Updated for Hybrid Approach)

- **Phase 1**: 1-2 weeks (Complete runtime API client - pairing/debugging deferred)
- **Phase 2**: ⏸️ **DEFERRED** (Keep pyvizio for config flow)
- **Phase 3**: 2 weeks (Media player migration - remove pyvizio from runtime)
- **Phase 4**: 3-5 days (Coordinator migration)
- **Phase 5**: 2-3 days (Cleanup - keep pyvizio only for config flow)
- **Phase 6**: 1-2 weeks (Testing)

**Total**: ~4-6 weeks for runtime migration (setup operations deferred)

**Future Work** (if needed):
- Pairing/auth migration: 1-2 weeks (if pyvizio becomes problematic)
- Device discovery migration: 3-5 days (if pyvizio becomes problematic)

## Next Steps

1. ✅ Review current implementation
2. ✅ Create migration plan (this document)
3. ✅ Decide on hybrid approach (keep pyvizio for setup)
4. ⏭️ Start Phase 1: Complete Direct API Client (runtime operations)
5. ⏭️ Complete volume and audio settings (get_volume_level, get_max_volume, etc.)
6. ⏭️ Implement app management (get_current_app, launch_app)
7. ⏭️ Implement settings management (get_setting, set_setting)
8. ⏭️ Migrate media player entity (remove pyvizio from runtime)
9. ⏭️ Migrate coordinator (app list retrieval)
10. ⏭️ Minimize pyvizio dependency (keep only for config flow)
11. ⏭️ Comprehensive testing
12. ⏭️ **Future**: Migrate pairing/auth if pyvizio becomes problematic

## References

- [Vizio SmartCast API Documentation](https://github.com/exiva/Vizio_SmartCast_API)
- [Current pyvizio Library](https://github.com/raman325/pyvizio)
- [Home Assistant Custom Integration Documentation](https://developers.home-assistant.io/docs/creating_integration_manifest/)

