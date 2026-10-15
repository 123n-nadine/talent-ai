# Job Offer Term Template

Module: **HR** · custom DocType: 0 · child table: 0 · submittable: 0 · naming: `field:title` · title field: `-`

## Fields

| # | fieldname | label | type | options / target | reqd | hidden | read_only | list | std filter | depends_on | fetch_from | default | custom | fill % | description |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `title` | Title | Data |  |  |  |  |  |  |  |  |  |  |  |  |
| 2 | `offer_terms` | Offer Terms | Table | child -> **Job Offer Term** |  |  |  |  |  |  |  |  |  |  |  |

## Child tables

- `offer_terms` (Table) -> **Job Offer Term** — see `Job_Offer_Term.md`

## Customizations

- Custom Fields: none
- Property Setters: none
- Workflow: none (no Workflow record for this DocType)
- Client Script records: none · Server Script: none · Notification: none · Assignment Rule: none (all queried on 2026-10-12)
- `__custom_js` returned by getdoctype: 50 chars (empty wrapper only)
