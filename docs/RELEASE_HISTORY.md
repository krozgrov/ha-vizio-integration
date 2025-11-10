# Release History

This document tracks the release history and alignment with the versioning workflow.

## Current Production Release

**2025.11.12** - November 12, 2025
- Optimized power on functionality based on testing
- Simplified power on logic (single attempt with 0.5s delay)
- Added comprehensive power on test script
- Tested and verified with actual Vizio TV devices

## Previous Releases

**2025.11.11** - November 11, 2025
- Power on retry improvements
- Added retry mechanism for power on command

**2025.11.10** - November 10, 2025
- Power and volume control fixes
- Fixed power on/off functionality
- Fixed volume setting to use direct set_setting API

**2025.11.9** - November 9, 2025
- Initial production release
- Base integration functionality

## Pre-releases

**2025.11.9b2** - November 9, 2025 (Pre-release)
- Testing release

**2025.11.9b1** - November 9, 2025 (Pre-release)
- Initial testing release

## Workflow Alignment Note

Versions 2025.11.10, 2025.11.11, and 2025.11.12 were created directly on `main` before the feature branch workflow was established. Going forward, all new changes will follow the proper workflow:

1. **Feature branch** → Development
2. **Pre-release** (YYYY.MM.DDb#) → Testing on feature branch
3. **Production release** (YYYY.MM.DD) → Merge to main

## Next Steps

For future releases:
- Create feature branch for changes
- Create pre-release (e.g., `2025.11.13b1`) on feature branch
- Test pre-release in Home Assistant
- Merge to main with production version (e.g., `2025.11.13`)

