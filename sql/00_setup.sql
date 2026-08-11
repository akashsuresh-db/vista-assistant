-- This file uses {catalog} and {schema} placeholders.
-- run_sql.py substitutes from CFG before executing.

-- Phase 1: UC objects for the Vista Assistant demo.
-- Catalog and schema are configured in config.yaml; we create the schema if needed.

CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}
  COMMENT 'Meridian Bank Finance & Accounting Shared Services - Vista Assistant demo (structured marts + document volume)';

-- Volume holding the unstructured corpus the Knowledge Assistant indexes:
-- accounting policies, month-end close SOPs, audit memos, board/MD&A decks.
CREATE VOLUME IF NOT EXISTS {catalog}.{schema}.vista_documents
  COMMENT 'Finance policy PDFs, close SOPs, audit memos and management-reporting decks';
