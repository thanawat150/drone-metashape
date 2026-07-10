# Web UI scope

These rules apply under `web/` and supplement root `AGENTS.md`.

- Use `drone-metashape-local-one-click` for UI implementation.
- Keep plain HTML, CSS, and JavaScript unless an approved task changes the stack.
- Do not introduce a Node.js runtime dependency for normal use.
- Keep labels Thai-first, desktop-friendly, keyboard-usable, and associated with accessible form controls.
- Use only the localhost API. Do not infer absolute filesystem paths from browser APIs.
- Never expose secrets or fabricate progress percentages.
- Treat persisted backend state as the source of truth.
- Show mock mode prominently and label unsupported behavior instead of presenting it as working.
- Require confirmation for destructive actions and show readable, actionable errors.
