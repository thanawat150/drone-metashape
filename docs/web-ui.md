# Thai local web UI

The plain HTML/CSS/JavaScript interface requires no Node.js build. It obtains an absolute Windows path from the backend native folder picker, then calls folder inspection. Inspection alone never starts processing.

The screen shows the editable plot code, server-reported image count, CRS, output directory, free space, profile, warnings, conflict policy, and deterministic stage timeline. It polls persisted state every two seconds and does not invent percentages.

In mock mode a prominent label states that Agisoft Metashape is not being called, and a development-only scenario selector is visible. Failure actions retrieve the job log, open its known diagnostics location, create a versioned retry, or copy a diagnostic prompt for Codex. The Codex action does not modify or execute code.

Run the Phase 3 mock server manually with:

```powershell
python app.py --mock-metashape
```

Then open `http://127.0.0.1:8765/`. Real mode is wired to the safe launcher but remains unverified until Phase 5.
