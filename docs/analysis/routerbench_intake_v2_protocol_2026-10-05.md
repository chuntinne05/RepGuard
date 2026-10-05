# Intake v2: archive layout amendment

The first intake downloaded and SHA256-verified the complete archive, but its
README-based `bench/` matcher recognized zero files. The 700 JSON member names
actually start with `bench-release/`; 51 contain MMLU and remain excluded.
No JSON payload was parsed in v1, no outcome inspected or used to choose this fix.

V2 preserves the original metadata-only extraction and all exclusions. It accepts
`bench-release/<dataset>/<partition...>/<model>/<file>.json`; datasets without a
partition directory are explicitly labeled `unspecified`, never inferred as test.
Reuse the exact verified archive from v1 run `8844b39df2d3d6b37eface11` on the same
Volume. New run/source identity, app name, protocol and receipt; preserve v1 artifacts.
Fail if the whole archive yields zero supported records. Original exclusions,
private storage, checkpointing, no outcome-based selection and bounds all remain.

See [original protocol](routerbench_intake_protocol_2026-10-05.md).
