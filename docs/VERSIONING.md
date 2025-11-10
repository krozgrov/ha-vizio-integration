# Versioning Scheme

This integration follows a date-based versioning scheme aligned with the release date.

## Version Format

### Production Releases
**Format**: `YYYY.MM.DD`

- `YYYY` = Year (4 digits)
- `MM` = Month (2 digits, 01-12)
- `DD` = Day (2 digits, 01-31)

**Examples**:
- `2025.11.9` - Release on November 9, 2025
- `2025.11.10` - Release on November 10, 2025
- `2025.12.1` - Release on December 1, 2025

### Testing/Beta Releases
**Format**: `YYYY.MM.DDb#`

- `YYYY.MM.DD` = Base release date
- `b#` = Beta number (b1, b2, b3, etc.)

**Examples**:
- `2025.11.9b1` - First beta for November 9 release
- `2025.11.9b2` - Second beta for November 9 release
- `2025.11.10b1` - First beta for November 10 release

## Release Workflow

### For Testing (Beta Releases)
1. Create a feature branch: `bug/description` or `feature/description`
2. Make changes and commit
3. Update `manifest.json` version to: `YYYY.MM.DDb#` (e.g., `2025.11.9b3`)
4. Create tag: `git tag -a 2025.11.9b3 -m "Pre-release message"`
5. Push branch and tag
6. Create GitHub release (mark as pre-release)

### For Production Releases
1. Merge feature branch to `main`
2. Update `manifest.json` version to: `YYYY.MM.DD` (e.g., `2025.11.10`)
3. Create tag: `git tag -a 2025.11.10 -m "Release message"`
4. Push to main and tag
5. Create GitHub release (not pre-release)

## Version Increment Rules

- **New day = New production release**: If releasing on a different day, increment the day
- **Same day, testing = Beta**: If testing on the same day, use beta version (b1, b2, etc.)
- **Multiple releases per day**: Use beta versions for testing, then final production release

## Examples

### Scenario 1: Testing on same day
- Start: `2025.11.9` (production)
- Testing: `2025.11.9b1`, `2025.11.9b2` (betas)
- Final: `2025.11.9` (or new day if released later)

### Scenario 2: New day release
- Previous: `2025.11.9` (production)
- New release: `2025.11.10` (production on next day)

### Scenario 3: Testing then production
- Testing: `2025.11.9b1`, `2025.11.9b2` (betas)
- Production: `2025.11.10` (released next day)

## Notes

- Always update `manifest.json` version before creating a tag
- Tags should match the version in `manifest.json`
- Beta releases should be marked as pre-releases on GitHub
- Production releases should not be marked as pre-releases

