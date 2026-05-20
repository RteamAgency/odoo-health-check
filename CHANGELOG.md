# Changelog

All notable changes to this module are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Module versioning: `<odoo_major>.0.<major>.<minor>.<patch>`.

## [16.0.1.0.2] - 2026-05-20

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
  args; Odoo 16's signature requires the third (`job_id`). Fixed all
  four call sites.

## [16.0.1.0.1] - 2026-05-07

* Fix: `numbercall=-1` added on every cron record. v14-v17 ir.cron has
  `numbercall = fields.Integer(default=1, ...)`, so a freshly-installed
  cron with no explicit numbercall fires once and the scheduler's
  UPDATE clause sets `active=False`. v18 dropped the field entirely.

## [16.0.1.0.0] - 2026-05-07

Initial public release for Odoo 16. Feature parity with the v17 listing
release `17.0.1.0.0` plus the changes required for Odoo 16's ORM and
view stack:

* Settings view rewritten from the v17 `<app>/<block>/<setting>` shortcut
  tags to the v14-v16 div-based pattern (`<div class="app_settings_block">`
  / `<div class="o_settings_container">` / `<div class="o_setting_box">`).
  Xpath target switched from `//form` to `//div[hasclass('settings')]`.
* `<page invisible="...">` replaced with `attrs="{'invisible': [...]}"`
  domain-style on the two notebook pages (cron history Error Traceback
  page, disk Details page) - the new short-form `invisible="..."` attr
  on view nodes is v17+.
* Removed the `web.assets_web_dark` manifest entry and the
  `static/src/scss/dark_mode_icon.scss` asset - dark mode bundle and
  body-class gating only exist on Odoo 18 Enterprise.
* `_callback` override and 3-arg test fixtures are unchanged from v17;
  v14-v17 all share the same `(cron_name, server_action_id, job_id)`
  signature.
* Reset module version to 16.0.1.0.0 (first publication on the v16
  apps.odoo.com listing per Constitution §6).
* Listing description, README, and listing chrome (badge, monospace
  pill) updated to mention Odoo 16.

Features brought forward from the v17 listing:

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
