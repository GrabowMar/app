"""Reconcile schema drift: the original 0001_initial was edited after being applied,
so the live DB is missing the ``expires_at`` and ``generation_job_id`` columns that
``reports.Report`` (and the migration state) already declare.

This is a database-only migration: model state already reflects the desired schema,
so we use ``RunSQL`` (no state operations) and gate every statement on the column
not already existing, making the migration safe to re-apply on a freshly built DB.
"""

from __future__ import annotations

from django.db import migrations


class _RunSQLIfPostgreSQL(migrations.RunSQL):
    """RunSQL variant that is a no-op on non-PostgreSQL backends.

    The reconciliation SQL uses PL/pgSQL DO blocks which are only valid on
    PostgreSQL.  Running against SQLite (e.g. during tests) must be skipped.
    """

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor == "postgresql":
            super().database_forwards(app_label, schema_editor, from_state, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor == "postgresql":
            super().database_backwards(app_label, schema_editor, from_state, to_state)

ADD_EXPIRES_AT = """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'reports_report' AND column_name = 'expires_at'
    ) THEN
        ALTER TABLE reports_report
            ADD COLUMN expires_at timestamp with time zone NULL;
    END IF;
END$$;
"""

ADD_GENERATION_JOB = """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'reports_report' AND column_name = 'generation_job_id'
    ) THEN
        ALTER TABLE reports_report
            ADD COLUMN generation_job_id uuid NULL
            REFERENCES generation_generationjob(id)
            DEFERRABLE INITIALLY DEFERRED;
        CREATE INDEX reports_report_generation_job_id_idx
            ON reports_report (generation_job_id);
    END IF;
END$$;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0001_initial"),
        ("generation", "0001_initial"),
    ]

    operations = [
        _RunSQLIfPostgreSQL(ADD_EXPIRES_AT, reverse_sql=migrations.RunSQL.noop),
        _RunSQLIfPostgreSQL(ADD_GENERATION_JOB, reverse_sql=migrations.RunSQL.noop),
    ]
