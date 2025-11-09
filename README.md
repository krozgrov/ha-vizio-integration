# VIZIO SmartCast Plus

[![GitHub release](https://img.shields.io/github/release/krozgrov/ha-vizio-integration.svg)](https://github.com/krozgrov/ha-vizio-integration/releases)
[![GitHub stars](https://img.shields.io/github/stars/krozgrov/ha-vizio-integration.svg)](https://github.com/krozgrov/ha-vizio-integration/stargazers)
[![License](https://img.shields.io/github/license/krozgrov/ha-vizio-integration.svg)](LICENSE)

📺 Home Assistant VIZIO SmartCast integration with enhanced features and improvements.

This is a modified version of the built-in Vizio integration that is actively maintained with bug fixes and improvements.

## Features

- **Full Media Player Support**: Control your VIZIO SmartCast TV or Soundbar
- **App Management**: Launch and control SmartCast apps
- **Volume Control**: Precise volume control with configurable step size
- **Input Selection**: Switch between HDMI inputs and SmartCast apps
- **Power Management**: Turn devices on/off
- **Sound Mode Selection**: Control audio settings (when supported)
- **Zeroconf Discovery**: Automatic device discovery on your network
- **Configurable Options**: Customize volume steps and app lists

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations**
3. Click the three dots in the top right corner
4. Select **Custom repositories**
5. Add this repository URL: `https://github.com/krozgrov/ha-vizio-integration`
6. Select **Integration** as the category
7. Click **Add**
8. Search for "VIZIO SmartCast Plus" and install it
9. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [Releases](https://github.com/krozgrov/ha-vizio-integration/releases) page
2. Extract the archive
3. Copy the `vizio_smartcast` folder to your `custom_components` directory in Home Assistant
4. Restart Home Assistant

## Configuration

### Initial Setup

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **VIZIO SmartCast Plus**
4. Follow the setup wizard:
   - Enter your device's IP address or hostname
   - Select device type (TV or Speaker)
   - For TVs, you may need to pair the device (enter the PIN shown on your TV)

### Configuration Options

After installation, you can configure the integration through the integration's options:

- **Volume Step**: Set the volume increment/decrement step (1-10, default: 1)
- **App Filtering** (TVs only): Include or exclude specific apps from the source list

## Usage

### Basic Commands

The integration provides standard media player controls:

- **Turn On/Off**: Control device power
- **Volume Up/Down**: Adjust volume with configurable step size
- **Mute**: Toggle mute state
- **Select Source**: Switch between inputs and apps
- **Play/Pause**: Control media playback
- **Channel Up/Down**: Navigate channels (TVs only)

### Voice Commands

You can use voice commands with Home Assistant:

- "Turn on [VIZIO Device Name]"
- "Turn off [VIZIO Device Name]"
- "Volume up on [VIZIO Device Name]"
- "Volume down on [VIZIO Device Name]"
- "Set volume to 50 on [VIZIO Device Name]"
- "Mute [VIZIO Device Name]"
- "Change input source to [Source Name] on [VIZIO Device Name]"

### Service: `vizio_smartcast.update_setting`

Update a device setting directly.

**Service Data:**

```yaml
entity_id: media_player.vizio_tv
setting_type: audio
setting_name: volume
new_value: 50
```

**Parameters:**

- `entity_id` (required): The entity ID of the VIZIO device
- `setting_type` (required): The type of setting (e.g., "audio")
- `setting_name` (required): The name of the setting (e.g., "volume", "eq")
- `new_value` (required): The new value (integer or string)

### Automation Examples

**Turn on TV at sunset:**

```yaml
automation:
  - alias: "Turn on VIZIO TV at sunset"
    trigger:
      - platform: sun
        event: sunset
    action:
      - service: media_player.turn_on
        target:
          entity_id: media_player.vizio_tv
```

**Volume control based on time:**

```yaml
automation:
  - alias: "Reduce TV volume at night"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: media_player.volume_set
        target:
          entity_id: media_player.vizio_tv
        data:
          volume_level: 0.3
```

## Troubleshooting

### Device Not Discovered

- Ensure your VIZIO device is on the same network as Home Assistant
- Check that the device is powered on
- Try manually entering the IP address during setup

### Pairing Issues

- Make sure you're entering the correct PIN displayed on your TV
- Verify that your TV supports SmartCast (2016 or newer)
- Try restarting both Home Assistant and your TV

### Volume Control Not Working

- Some devices may not report volume information in all states
- The integration handles missing volume data gracefully
- Check that your device is powered on and connected

### Connection Lost

- Verify network connectivity
- Check firewall settings
- Ensure the device hasn't changed its IP address
- Try removing and re-adding the integration

## Requirements

- Home Assistant 2024.1.0 or later
- VIZIO SmartCast device (2016 or newer)
- Network connectivity between Home Assistant and the device

## Known Limitations

- Volume information may not be available in all device states
- Some older devices may have limited functionality
- App launching requires the device to be powered on

## Changelog

### 2025.11.9b1 (Pre-release)

- Fixed deprecation warning for OptionsFlow config_entry handling (compatible with Home Assistant 2025.12+)
- Fixed KeyError when volume information is not available in audio settings
- Improved error handling for missing device data

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Reporting Issues

If you encounter any issues, please report them on the [GitHub Issues](https://github.com/krozgrov/ha-vizio-integration/issues) page.

When reporting issues, please include:
- Home Assistant version
- Integration version
- Device model and firmware version
- Error messages from logs
- Steps to reproduce the issue

## Credits

This integration is based on the built-in Home Assistant Vizio integration, which is maintained by the Home Assistant Core team.

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Support

If you find this integration useful, please consider giving it a star ⭐ on GitHub!

---

**Note**: This is a custom integration and is not affiliated with VIZIO, Inc. VIZIO and SmartCast are trademarks of VIZIO, Inc.

