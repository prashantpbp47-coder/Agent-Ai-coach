# P19 — Priya Insurance Knowledge Base

## Basic contract

P19 provides a controlled knowledge layer for Priya. It stores approved knowledge sources and approved knowledge entries with source/version/effective-date metadata.

## Safety rules

- Only approved entries from approved sources are returned by search.
- Source metadata is retained for auditability and citations.
- P19 does not invent insurance/product facts.
- P19 does not replace the existing Priya provider layer.
- Live insurer/product content is not assumed to exist until an approved source is loaded.
- Knowledge-management mutations are ADMIN-only.
- New sources and entries are unapproved by default; an entry cannot be approved before its source is approved.

## Runtime endpoints

Public/read-only:

- `GET /api/p19/health`
- `GET /api/p19/search?q=<term>`

ADMIN-only knowledge management:

- `GET /api/p19/sources`
- `POST /api/p19/sources`
- `POST /api/p19/sources/<source_id>/approve`
- `POST /api/p19/sources/<source_id>/ingest`
- `GET /api/p19/entries`
- `POST /api/p19/entries/<entry_id>/approve`

## Retrieval behaviour

Search matches title, topic, content, tags and source title. Results include source/version/effective-date citation metadata and are ordered with the newest effective source first.

## Ingestion contract

Create a source first, keep it unapproved while review is pending, then approve the source. Ingest one or more knowledge entries against that source. Entries remain unapproved until explicitly approved. Only after both source and entry approval will Priya retrieval return the content.

## Validation

The P19 CI foundation gate validates application import/routes, Gunicorn startup, Alembic migration graph, a fresh database migration, P19 schema presence, public endpoint smoke checks and ADMIN endpoint protection. The current operational migration head is `0014_p13_operational_data`, which includes the P19 knowledge-base migration in its ancestry.
