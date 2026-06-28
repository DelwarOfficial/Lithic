# Merge Notes

- Wrapped Graphify through subprocess CLI calls. No Graphify source was copied into `src/`.
- Wrapped Headroom through its public `headroom.compress` API when importable. Fallback compression is original code in this repo.
- Adapted Caveman behavior as policy rules in `ResponsePolicy` and `caveman_policy.md`. No hooks, installer code, or command templates were copied.
- Copied license texts only into `LICENSES/`.
- Added attribution in `THIRD_PARTY_NOTICES.md`.
## Merge Notes

- `lithic_cli.graph.graphify_adapter` is a subprocess-first wrapper around Graphify CLI behavior rather than a source merge.
- `lithic_cli.compression.headroom_adapter` uses Headroom when importable and falls back to deterministic compression when it is not.
- `lithic_cli.policy.response_policy` is an original Lithic implementation informed by Caveman-style brevity, with safety overrides for risky actions.
- Provider wrappers are optional and isolated under `lithic_cli.providers`.
- Old `unified_agent` shim imports were removed from active codepaths and tests so the runtime package is natively `lithic_cli.*`.
