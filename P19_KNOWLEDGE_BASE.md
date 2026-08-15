# P19 — Priya Insurance Knowledge Base

## Basic contract

P19 provides a controlled knowledge layer for Priya. It stores approved knowledge sources and approved knowledge entries with source/version/effective-date metadata.

## Safety rules

- Only approved entries are returned by search.
- Source metadata is retained for auditability.
- P19 does not invent insurance/product facts.
- P19 does not replace the existing Priya provider layer.
- Live insurer/product content is not assumed to exist until an approved source is loaded.

## Initial endpoints

- `GET /api/p19/health`
- `GET /api/p19/search?q=<term>`

## Later incremental work

- document ingestion
- source approval workflow
- retrieval ranking
- source citations in Priya answers
- effective-date conflict handling
- insurer/product-specific knowledge
- admin knowledge management UI
- P19 runtime smoke tests
