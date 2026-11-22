# Changelog

All notable changes to this module are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Module versioning: `<odoo_major>.0.<major>.<minor>.<patch>`.

## [20.0.1.0.3] - 2026-11-22

Port to Odoo 20, on top of 19.0.1.0.3.

* `odoo-bin upgrade_code --from 19.0`: access rights are `security/ir.access.csv`.
* `ir.config_parameter.get_param` / `set_param` are gone in Odoo 20: the
  module reads its settings with `get_str` / `get_float`; a value that is
  not a number still falls back to the default threshold.
* Tests enter Odoo 20's `registry_test_mode()` context; 82 / 82 on Odoo
  20.0 community, and in GitHub Actions.
* Store page and README target Odoo 20.

## [19.0.1.0.3] - 2026-11-22

* **Run Manually recorded twice**: since Odoo 19, `method_direct_trigger`
  runs the job through `_process_job` and `_callback`, so the module's
  override of both wrote two history rows per manual run, and the outer
  one always said `success` (Odoo 19 returns the failure to the client
  instead of raising). The `method_direct_trigger` override is gone:
  `_callback` records scheduled and manual runs, one row each.
* **History retention**: `0` deleted the whole history every day and a
  negative value made the daily cleanup cron fail, while the setting says
  "0 or negative disables cleanup". Now `0` or less disables it, and a
  value that is not a whole number skips the cleanup with a warning in the
  log instead of failing the cron.
* **Tests**: 11 of 82 were red on Odoo 19. They now run in Odoo's registry
  test mode, run a cron's action without Odoo's commit / rollback (which a
  test transaction forbids), and no longer use `assertRaises` around a
  failing cron (its savepoint rollback took the history row with it).
  82 / 82 on Odoo 19.0; GitHub Actions runs them on every pull request
  (`.github/workflows/tests.yml`).

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
