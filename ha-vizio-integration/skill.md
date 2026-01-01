# Skill Plan: HA alignment improvements

Goal
- Improve HA best-practice alignment and UX without introducing regressions.

Constraints
- Prefer low-risk changes first.
- Keep changes small and reversible.

Prioritized plan (least impactful -> most impactful)

1) Device compatibility audit and capability matrix
Goal
- Identify which Vizio models and firmware versions are failing and what
  capabilities are missing or misreported.
Execution outline
1. Collect model, firmware, and network details from affected TVs.
2. Use existing test scripts to capture device info and capabilities.
3. Build a lightweight matrix mapping models to supported features and gaps.
Risks
- Incomplete data could misclassify capability gaps.
- Differences across firmware versions may require per-model handling.
Tests and validation
- Manual pairing and device info retrieval on each affected model.
- Verify existing power and input tests still pass.

2) pzvizio gap analysis and upstream strategy
Goal
- Determine whether missing functionality should be added to pzvizio or handled
  locally as a fallback.
Execution outline
1. Map integration needs to pzvizio endpoints and capability flags.
2. Identify missing endpoints, commands, or response parsing.
3. Decide whether to contribute upstream patches or add guarded fallbacks.
Risks
- Updating the dependency could introduce behavior changes for known models.
- Local fallbacks risk divergence from upstream API behavior.
Tests and validation
- Run existing tests against the updated library or fallback code paths.
- Validate against at least one known-good and one affected model.

3) Integration capability detection and entity gating
Goal
- Ensure entities and services only expose features that the TV supports.
Execution outline
1. Add capability-driven checks before entity creation and service execution.
2. Ensure entity unique_id stability for unchanged entities.
3. Add clear logging for unsupported features without spamming.
Risks
- Entity add/remove could impact dashboards or automations.
- Incorrect gating may hide functionality on supported models.
Tests and validation
- Confirm entity registry stability for existing devices.
- Manual verification of entity availability per model.

4) Diagnostics and supportability improvements
Goal
- Capture capability snapshots to simplify support without exposing secrets.
Execution outline
1. Add diagnostics output for capabilities and device metadata.
2. Redact tokens, IPs, and any user-specific data.
3. Document how to collect diagnostics in README or troubleshooting docs.
Risks
- Diagnostics could expose sensitive data if redaction is incomplete.
Tests and validation
- Validate diagnostics output redaction and schema shape.
