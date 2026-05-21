# Changelog

All notable changes to this module are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Module versioning: `<odoo_major>.0.<major>.<minor>.<patch>`.

## [19.0.1.0.2] - 2026-05-21

* **res.config.settings action**: `ir.actions.act_window.target` value
  `inline` was removed in Odoo 19, which made the module fail to install
  (`ValueError: Wrong value for ir.actions.act_window.target: 'inline'`).
  Switched the Health Check settings shortcut action to `target="current"`.
  The 19.0 branch now installs cleanly on Odoo 19 (verified on `odoo:19`
  docker `--test-enable` + XML-RPC install smoke).

## [19.0.1.0.1] - 2026-05-20

Backport of the version-agnostic fixes from the 14.0 review (OHC-14).

* **health.check.dashboard**: dropped redundant `readonly=True` on the
  computed (`store=False`) fields; computed non-stored fields are
  read-only by default. Kept on the stored `name` field.
* **ir.cron._odoo_health_log_end**: write the history row in its own
  cursor (lock released on commit) and enqueue the failure email in a
  separate cursor afterwards, so the slow template render / mail.mail
  creation no longer runs while holding the history row lock. Both
  cursors stay isolated from the monitored cron's transaction so the
  history write and the alert survive its rollback.

## [19.0.1.0.0] - 2026-04-30

Initial public release for Odoo 19. Feature parity with the v18 listing
release `18.0.1.12.3` plus the changes required for Odoo 19's ORM:

* `_sql_constraints` (deprecated in 19, logs a WARNING) replaced with
  the new `models.Constraint` API. Same `CHECK (date_end IS NULL OR
  date_end >= date_start)` invariant on `ir.cron.history.date_order`.
* Manifest, README, and listing description updated for Odoo 19.

Features brought forward from the v18 listing:

* At-a-glance dashboard (cron failures 24h/7d, disk root and filestore
  current usage, latest PG monthly report)
* Cron execution history with duration and error traceback, written
  through an independent cursor so cron rollbacks do not erase audit
  rows. Email alert on every failure.
* Hourly disk monitoring on OS root and the Odoo filestore mount,
  worsening-transition alert emails (no per-tick spam).
* Monthly PostgreSQL growth report (1st of each month at 08:00) with
  top-10 tables, byte/row deltas, total DB size delta vs prior report.
* Localised UI and emails in 8 languages: English, Russian, Ukrainian,
  German, Spanish, Romanian, Polish, Arabic.
