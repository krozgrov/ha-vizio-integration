# Architecture & Design Decisions

## API Client Approach

### Direct API vs External Library

**Decision**: Use a lightweight API client class (`VizioAPIClient`) embedded within the integration rather than an external library.

**Rationale**:
1. **Home Assistant Best Practices**: While Home Assistant recommends using external libraries, having a well-structured API client class within the integration is also acceptable and common practice.
2. **Control**: Direct control over API calls, error handling, and logging without external dependencies.
3. **Maintainability**: No dependency on potentially unmaintained external libraries (like `pyvizio`).
4. **Separation of Concerns**: Clean separation between API client logic and entity logic.
5. **No External Dependencies**: Uses only Home Assistant core dependencies (`aiohttp_client`).

### Architecture Pattern

```
┌─────────────────────────────────────┐
│   Home Assistant Integration        │
│                                     │
│  ┌──────────────────────────────┐  │
│  │   Config Flow                │  │
│  │   (Uses pyvizio for setup)   │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │   Media Player Entity         │  │
│  │   (Uses VizioAPIClient)       │  │
│  └──────────────────────────────┘  │
│           │                         │
│           ▼                         │
│  ┌──────────────────────────────┐  │
│  │   VizioAPIClient             │  │
│  │   (Direct API calls)          │  │
│  └──────────────────────────────┘  │
│           │                         │
│           ▼                         │
│  ┌──────────────────────────────┐  │
│  │   Vizio SmartCast API         │  │
│  │   (HTTPS on port 7345)        │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

## Logging Strategy

### Log Levels

Following Home Assistant best practices:

- **DEBUG**: Detailed request/response information for troubleshooting
  - API request details (method, endpoint, host, port)
  - Request payloads (JSON data)
  - Response status codes and headers
  - Full response bodies
  - Power state values and parsing
  - Exception stack traces (`exc_info=True`)

- **INFO**: Important state changes
  - Connection restored
  - Successful operations (if needed)

- **WARNING**: Errors and failures that may need attention
  - API request failures
  - Non-200 HTTP status codes
  - JSON parsing errors
  - Timeout errors
  - Connection lost
  - Failed commands

- **ERROR**: Critical errors that prevent functionality
  - Currently not used (warnings are sufficient)

### Security Considerations

- **Auth Tokens**: Never logged in full
  - Masked in logs: `{token[:4]}...{token[-4:]}` or `***`
  - Only presence indicated: `"auth=present"` or `"auth=none"`

- **Sensitive Data**: No passwords, PINs, or full tokens logged

### Debug Logging Enablement

Users can enable debug logging via `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.vizio_smartcast: debug
    custom_components.vizio_smartcast.vizio_api: debug
```

Or via Home Assistant UI:
1. Settings → Devices & Services
2. Select the integration
3. Three dots menu → Enable debug logging

## Error Handling

### API Request Errors

1. **Timeout Errors**: Logged with timeout value and host details
2. **HTTP Errors**: Logged with status code and response body (first 500 chars)
3. **JSON Parse Errors**: Logged with error details and full response text
4. **Connection Errors**: Logged with exception type and full stack trace

### Power State Handling

- **None Response**: 
  - If device was OFF: Expected behavior, no error
  - If device was ON: Connection lost, mark unavailable
  
- **Invalid Response Format**: Logged as warning with full response

### Retry Logic

- Power on: 3 attempts with delays (5s initial, 4s retry)
- Power off: 3 attempts with 1s delay
- State verification after each attempt

## Code Organization

### Module Structure

```
custom_components/vizio_smartcast/
├── __init__.py          # Integration setup
├── config_flow.py       # Configuration & pairing (uses pyvizio)
├── media_player.py      # Entity implementation (uses VizioAPIClient)
├── vizio_api.py         # Direct API client (no external deps)
├── coordinator.py        # App list coordinator
├── const.py             # Constants
└── services.yaml        # Service definitions
```

### Separation of Concerns

1. **VizioAPIClient** (`vizio_api.py`):
   - Pure API communication
   - No Home Assistant entity logic
   - Reusable API methods
   - Comprehensive logging

2. **VizioDevice** (`media_player.py`):
   - Home Assistant entity logic
   - State management
   - Uses VizioAPIClient for API calls
   - Handles Home Assistant callbacks

3. **Config Flow** (`config_flow.py`):
   - Setup and pairing
   - Uses pyvizio for pairing (one-time operation)
   - Creates config entries

## Benefits of This Approach

1. **Reliability**: Direct control over API calls
2. **Debuggability**: Comprehensive logging at all levels
3. **Maintainability**: Clear separation of concerns
4. **Flexibility**: Easy to adapt to API changes
5. **No External Dependencies**: Only Home Assistant core
6. **Security**: Proper token masking in logs
7. **User-Friendly**: Easy to enable debug logging for troubleshooting

## Future Considerations

### If pyvizio Becomes Unavailable

If `pyvizio` becomes completely unavailable or broken, we can:
1. Implement pairing/auth in `VizioAPIClient` (already documented in API_REFERENCE.md)
2. Implement device discovery in `VizioAPIClient`
3. Remove `pyvizio` dependency entirely

The architecture supports this migration path without major refactoring.

### External Library Option

If we wanted to create an external library:
1. Extract `VizioAPIClient` to separate package
2. Publish to PyPI
3. Add to `requirements.txt`
4. Import in integration

However, this adds complexity without significant benefit for a custom integration.

## Alignment with Home Assistant Standards

✅ **Code Quality**: Follows Home Assistant style guidelines  
✅ **Error Handling**: Comprehensive try/except blocks  
✅ **Logging**: Appropriate log levels, no sensitive data  
✅ **Documentation**: Docstrings and comments  
✅ **Type Hints**: Full type annotations  
✅ **Async/Await**: Proper async patterns  
✅ **Separation**: API client separate from entity logic  
✅ **Security**: Token masking, no secrets in logs  

This architecture aligns with Home Assistant's integration quality standards and best practices.

