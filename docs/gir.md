# GIR 1.0

GIR is GraphSight Intermediate Representation.

Required top-level fields:

- `gir_version`
- `document`
- `pages`
- `nodes`
- `edges`
- `groups`
- `labels`
- `connectors`
- `evidence`
- `conflicts`
- `uncertainties`
- `metadata`

Every important prediction should link to `evidence_ids`. Coordinates are in original image pixels unless a future page transform declares otherwise.

