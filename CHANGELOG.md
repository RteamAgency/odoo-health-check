# Changelog

All notable changes to this module are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Module versioning: `<odoo_major>.0.<major>.<minor>.<patch>`.

## [15.0.1.0.1] - 2026-05-07

* Fix: `numbercall=-1` added on every cron record. v14-v17 ir.cron has
  `numbercall = fields.Integer(default=1, ...)`, so a freshly-installed
  cron with no explicit numbercall fires once and the scheduler's
  UPDATE clause sets `active=False`. v18 dropped the field entirely.

## [15.0.1.0.0] - 2026-05-07

Initial public release for Odoo 15. Branched from the v16 listing release
`16.0.1.0.0`. v15 and v16 share the settings-view layout, the `<tree>`
list-view tag, the 3-arg `_callback(cron_name, server_action_id, job_id)`
signature, and the QWeb (`{{ }}` / `t-out` / `t-if`) mail-template
syntax - so no code changes were required beyond the version stamp.

* Reset module version to 15.0.1.0.0 (first publication on the v15
  apps.odoo.com listing per Constitution §6).
* Listing description, README, and listing chrome (badge, monospace
  pill) updated to mention Odoo 15.

Features brought forward from the v16 listing:

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
