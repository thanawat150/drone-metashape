# Pipeline scope

These rules apply under `metashape_pipeline/` and supplement root `AGENTS.md`.

- Use `drone-metashape-local-one-click` for general pipeline implementation and `metashape-runtime-validation` for installed-version/API/CLI compatibility work.
- Treat normal Python and Metashape embedded Python as separate runtimes; never assume matching Python versions.
- Keep `Metashape` imports isolated from normal test collection.
- Do not hard-code plot paths or use arbitrary `eval`. Map profile values through explicit allowlists.
- Launch subprocesses with argument arrays and `shell=False`.
- Preserve atomic state writes and persist stage/error evidence immediately.
- Fatal stage failures must stop all later stages. Never silently lower quality or switch profiles/sources.
- Require an explicit policy before overwriting output.
- Pair real-adapter changes with mock regression tests and real-validation notes.
- Keep mock outputs visibly distinguishable from production output.
- Leave `work/` legacy scripts untouched unless the task explicitly approves migration edits.
