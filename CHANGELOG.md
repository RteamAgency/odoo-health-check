# Changelog

All notable changes to this module are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Module versioning: `<odoo_major>.0.<major>.<minor>.<patch>`.

## [17.0.1.0.3] - 2026-05-21

* **Test suite green** (was 13 problem tests of 82). The cron history/alert tests
  drove failing/long crons through base `ir.cron._callback`, which rolls back the
  cursor on failure - illegal on the test cursor (savepoint corruption). Rewrote
  those tests to exercise the logging helpers directly, and made the module
  test-aware: `_odoo_health_env` uses an isolated cursor in production (history +
  alert survive the monitored cron's rollback) and the test cursor under
  `--test-enable`. Removed the broken `registry.cursor` monkeypatch from the test base.
* **Scheduled-cron failure detection fixed (Odoo 14-17)**: on these majors base
  `_callback` SWALLOWS a failing scheduled action (it calls
  `_handle_callback_exception` and does not re-raise), so the previous
  try/except-around-super recorded every run as "success". Failures are now
  recorded by overriding `_handle_callback_exception`. Manual "Run" already worked
  (it runs the action directly and re-raises).
* **ir.cron.history retention cleanup**: a non-numeric `retention_days` raised
  `UserError` and a non-positive value still purged rows. A GC cron must not break
  on bad config: invalid values are now skipped and `<= 0` disables cleanup.


## [17.0.1.0.2] - 2026-05-20

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
* **tests**: `test_failure_email` called `_callback` with two positional
  args; Odoo 17's signature requires the third (`job_id`). Fixed all
  four call sites.

## [17.0.1.0.1] - 2026-05-07

* Fix: `numbercall=-1` added on every cron record. v14-v17 ir.cron has
  `numbercall = fields.Integer(default=1, ...)`, so a freshly-installed
  cron with no explicit numbercall fires once and the scheduler's
  UPDATE clause sets `active=False`. v18 dropped the field entirely.
  Existing v17.0.1.0.0 installs are NOT auto-fixed by upgrade because
  `data/ir_cron_data.xml` has `noupdate="1"`; affected operators must
  toggle each Odoo Health Check cron's `Number of Calls` to `-1`
  manually (Settings -> Technical -> Scheduled Actions).

## [17.0.1.0.0] - 2026-04-30

Initial public release for Odoo 17. Feature parity with the v18 listing
release `18.0.1.12.3` plus the changes required for Odoo 17's ORM:

* `_callback(self, cron_name, server_action_id, job_id)` override
  matches the Odoo 17 base signature (v18 dropped the `job_id`
  parameter mid-major; v17 keeps it). The override picks up the cron
  id from `job_id` since `self` is the empty model when called from
  `_process_job`.
* Test fixtures updated to pass the third `job_id` arg to
  `cron._callback(...)`.
* Reset module version to 17.0.1.0.0 (first publication on the v17
  apps.odoo.com listing per Constitution §6).
* Listing description, README, and badge updated to mention Odoo 17.
* README/listing GitHub URLs corrected from the legacy alex-odoo
  org to RteamAgency (the repo lived at alex-odoo before the org
  transfer).
* CHANGELOG reset to a single 17.0.1.0.0 "Initial public release"
  entry (no prior live installs on v17 listing, no upgrade history
  to preserve).

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
