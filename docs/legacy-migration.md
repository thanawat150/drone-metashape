# Legacy migration status

| Legacy script | Profile/route | Preserved | Deliberate change | Retirement recommendation |
|---|---|---|---|---|
| `align_surat_37_stc.py` | Preview alignment basis | downscale 2, 30k/4k, reference preselection | reusable source/output and continued preview DEM/ortho | Keep until Preview is validated with real 37-STC copy |
| `process_surat_metashape.py` | Standard basis | downscale 1, 40k/4k, mild depth maps, depth-map DEM, optional report path | explicit CRS/profile/state/validation and safe conflicts | Keep until Standard real output is accepted |
| `process_surat_metashape_cpu.py` | Future explicit CPU-only option | CPU enabled/GPU disabled observation and downscale 2 variant documented | no hidden machine-wide hardware choice in current profile | Keep; hardware decision unresolved |
| `process_phangnga_28_vsd.py` | High Quality alignment basis | 80k/10k and guided matching are represented | no `doc.clear`, no hard-coded Downloads, proposed depth-map DEM instead of silent tie-point production substitution | Keep until 28-VSD behavior/profile mapping is reviewed |

No legacy script is safe to retire at Phase 4 because no complete job has run through the new real adapter. Removal requires separate approval after Phase 5 and user acceptance.
