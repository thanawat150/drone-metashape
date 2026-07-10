# Test scope

These rules apply under `tests/` and supplement root `AGENTS.md`.

- Use `drone-metashape-local-one-click` for general test work and `metashape-runtime-validation` only for explicitly enabled real integration tests.
- Default tests must not require Metashape or a license.
- Use isolated temporary directories and preserve Thai path coverage.
- Keep mock output visibly fake.
- Test security boundaries, output conflicts, retry/cancellation, and terminal-state handling.
- Do not depend on test execution order or reduce assertions merely to pass.
- Separate unit, API, mock end-to-end, and real-Metashape integration tests.
- Exclude real integration tests from the default command unless explicitly enabled.
