# Legacy Compatibility Layer

`legacy/` contains obsolete Studio compatibility behavior that is intentionally not part of canonical `cicada-studio==0.0.1`.

Rules:

- Every legacy entry must be marked `@obsolete`.
- Legacy code is documentation or migration reference only.
- CORE paths (`cicada/`, `core/*.py`, `vendor/cicada-dsl-parser/cicada/`) must never import from `legacy/`.
- If a behavior is needed again, implement it upstream in `cicada-studio` or through an adapter outside CORE.
