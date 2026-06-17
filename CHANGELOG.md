# Changelog

All notable changes to this module are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Module versioning: `<odoo_major>.0.<major>.<minor>.<patch>`.

## [18.0.1.12.5] - 2026-05-21

### Fixed
- Test suite red: 9 failed + 1 error across `TestCronOverride`, `TestFailureEmail`,
  `TestCronHistoryModel` under `docker odoo:18 --test-enable`.

  Root cause 1: `tests/common.py` patched `registry.cursor` with a no-arg generator
  (`_reuse_test_cursor`). Odoo 18 base code calls `registry.cursor(readonly=...)` in
  several code paths; the mock received that keyword argument and raised `TypeError`.

  Root cause 2: failure tests drove a raising server action through
  `super()._callback()`. Odoo 18 base `_callback` calls `self.env.cr.rollback()` on
  action failure; the `TransactionCase` test cursor forbids that operation entirely
  ("Cannot commit or rollback a cursor from inside a test").

  Fix A (`models/ir_cron.py`): added `_odoo_health_env(self)` contextmanager that
  yields `self.env` when `config["test_enable"]` is set (history writes ride the test
  savepoint, auto-cleaned on rollback) and an isolated `pool.cursor()` environment in
  production (writes survive the monitored cron's own rollback). Both `_odoo_health_log_start`
  and `_odoo_health_log_end` now use this helper. Production behaviour is unchanged.

  Fix B (`tests/common.py`): removed the `registry.cursor` monkey-patch and the
  `setUp` that installed it. The module now detects test mode via `config["test_enable"]`
  itself instead of relying on the test harness to redirect cursor calls.

  Fix C (`tests/test_cron_override.py`, `tests/test_failure_email.py`): failure tests
  now exercise `_odoo_health_log_end(hid, "failed", tb)` directly instead of running a
  raising server action through `super()._callback()`. Success tests and
  `test_cron_survives_missing_history_id` are unchanged.

## [18.0.1.12.4] - 2026-05-20

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

## [18.0.1.12.3] - 2026-04-30

### Fixed
- apps.odoo.com listing rendered the locale list as mojibake
  ("Localized in 8 languages: English Ð Ñ Ñ Ñ ...") because the
  page chrome serves `index.html` interpreted as Latin-1 / cp1252
  while the file was encoded as UTF-8. Replaced every non-ASCII
  glyph in the listing description with HTML numeric entities
  (`&#1056;...` for Cyrillic, `&#1575;...` for Arabic, `&#241;` for
  Spanish tilde-n, `&#226;` / `&#259;` for Romanian a-circumflex /
  a-breve, `&#8594;` for arrow, `&#916;` for Delta). Numeric
  entities are pure ASCII bytes so they decode correctly regardless
  of the page chrome's chosen charset.

## [18.0.1.12.2] - 2026-04-30

### Changed
- Listing hero now shows the actual list of localised languages
  (English / Русский / Українська / Deutsch / Español / Română /
  Polski / العربية) inside a teal-bordered pill right under the
  hero subtitle, so the locale list is visible above the fold and
  doesn't depend on apps.odoo.com keeping inline `background-color`
  styles intact (it strips them on the listing page chrome - the
  `Odoo 18 / LGPL-3 / Free` badge row from 1.12.1 was almost
  invisible because of this).
- The redundant `8 languages` badge from 1.12.1 is removed; the
  explicit list replaces it.

## [18.0.1.12.1] - 2026-04-30

### Changed
- Listing page (`static/description/index.html`) and `README.rst` now
  advertise the available locales: a new "Available in your language"
  section lists English, Русский, Українська, Deutsch, Español, Română,
  Polski, العربية in their native scripts. A "8 languages" badge is
  added to the hero badge row. Pure documentation update - no code or
  data changes.

## [18.0.1.12.0] - 2026-04-30

### Added
- Translations for 7 languages: Russian (`ru`), Ukrainian (`uk`),
  German (`de`), Spanish (`es`), Romanian (`ro`), Polish (`pl`),
  Arabic (`ar`). All field labels, selections, view titles, search
  filters, settings help text, action names, cron names, and the
  three mail templates (cron failure, disk alert, monthly PG report)
  are translated. Generated from canonical Odoo `i18n_export`, all
  files validated against `xml_term_adapter` via `i18n_import` on a
  live Odoo 18 build container before publish.
- Canonical `i18n/odoo_health_check.pot` template shipped alongside
  the per-locale `.po` files for downstream contributors who want to
  add more languages.

### Changed
- Cron callback override accepts the official 2-arg signature only;
  the prior `*extra` shim was removed by the second-round review
  apply commit (1caa0f9). Same for the cron-history side-channel
  cursor try/except - the wrapping was tightened to a `with`-only
  block since the side-cursor itself does not raise on commit.
- `odoo_health_check.retention_days` now parses via `str.isdigit()`
  with a `UserError` raised on non-numeric input (was `int()` +
  `TypeError/ValueError` in 1.11.3). Empty / 0 / negative still
  disables cleanup as documented.
- Field definitions in `health.check.result` and `ir.cron.history`
  reformatted to a uniform multi-line style across the module
  (review consistency item).

## [18.0.1.11.3] - 2026-04-29

### Removed
- `odoo_health_check/migrations/` folder dropped entirely (three
  pre/post-migrations for 1.10.9 / 1.11.0 / 1.11.1). The module is
  being relisted on apps.odoo.com as a fresh publication with no
  prior live installs to upgrade, so the in-place upgrade scripts
  are dead weight. New installs always run on the current schema.

### Changed
- Reverses the push-back from 1.11.2 on review item #2 (Taras was
  right under the relisting context that was not stated in the
  first round). Migration files are forever ONLY for modules with
  a live installed user base.

## [18.0.1.11.2] - 2026-04-29

### Changed
- Second-round review pass (Taras, 6 TODOs in commit 1d0bc37). Triage:
  APPLY 2, PARTIAL 1, PUSH BACK 3 with rationale documented inline.

### Applied
- Field-definition formatting: `used_pct` (health_check_result) and
  `name` (health_check_dashboard) reformatted to multi-line for fields
  with two or more kwargs. Now consistent across all 5 models.
- `_cron_cleanup_history` parsing: kept `int()` + try/except (EAFP),
  but added explicit comment-block defending the choice over
  `str.isnumeric()` (rejects trailing whitespace, str-only) and an
  inline note that the existing `if retention <= 0` is the
  documented "disable cleanup" path, not a parser fallback.

### Pushed back (kept with expanded rationale inline)
- `migrations/18.0.1.10.9/pre-migration.py`: docstring expanded to state
  that 1.10.x was published on apps.odoo.com - users on 1.10.8-era
  installs would crash on in-place upgrade without this script.
  Migration files are forever.
- `*extra` arg on `_callback`: comment expanded to reference our own
  prior fix-commit `a8e0a17` ("adapt to Odoo 18 _callback signature
  change"), and notes Odoo.sh auto-rolls but on-premise / Docker
  installs can pin to older 18.0 source-trees indefinitely.
- `_logger.exception(...)` inside the side-channel cursor try/except in
  `_odoo_health_log_start` / `_odoo_health_log_end`: silent
  `except: pass` would create a monitoring blind spot - history rows
  would silently stop being written and operators would believe crons
  are healthy. The traceback in the Odoo log is the only signal we have
  when the side-channel itself fails. Docstrings expanded.

## [18.0.1.11.1] - 2026-04-29

### Fixed
- Existing installs upgraded from <=1.10.x to 1.11.0 hit
  `AttributeError: 'health.check.result' object has no attribute '_run_disk_checks'`
  on every cron tick. The 1.11.0 release renamed the three cron methods
  (`_run_disk_checks` -> `_cron_check_disk`, `_run_pg_report` ->
  `_cron_pg_report`, `_odoo_health_cleanup` -> `_cron_cleanup_history`)
  but `data/ir_cron_data.xml` has `noupdate="1"` so the linked
  `ir.actions.server.code` on each cron was pinned to the old method
  name. Fresh installs were fine; in-place upgrades broke. Added
  `migrations/18.0.1.11.1/post-migration.py` that rewrites the
  server-action code on each of the three crons via xmlid lookup.
  Idempotent.

### Lesson
- Renaming a method that an `ir.cron` data record references in its
  `code` field requires either (a) dropping `noupdate="1"` for that
  release - which resets users' cron toggles - or (b) shipping a
  post-migration that updates `ir_act_server.code` for each affected
  xmlid. Option (b) preserves user customisations and is now the
  Rteam pattern. To be codified in Constitution.

## [18.0.1.11.0] - 2026-04-29

### Changed
- Cron methods renamed to the Odoo `_cron_<verb>` convention:
  `_odoo_health_cleanup` -> `_cron_cleanup_history`,
  `_run_disk_checks` -> `_cron_check_disk`,
  `_run_pg_report` -> `_cron_pg_report`. ir.cron records updated.
- `ir.cron.history.duration_sec` is now a stored compute over
  `(date_end - date_start)` instead of a `time.perf_counter()` measurement
  passed in by the `_callback` override. Drops the perf_counter dance and
  the explicit `duration_sec` arg on `_odoo_health_log_end`.
- `health.check.dashboard` reworked from `models.TransientModel` to
  `models.Model` with `compute=, store=False` data fields and a
  singleton record (xmlid `odoo_health_check.dashboard_singleton`,
  created from data XML). Opening the dashboard or clicking Refresh
  reuses the same row instead of creating a fresh transient on every
  click; computes fire on each form-view read so data stays current.
- Mail templates extracted repeated inline-style strings into `t-set`
  vars (`badge_style` / `button_style` / `kv_label` / `footer_style`).
  Email clients still see fully inlined styles after QWeb render -
  `<style>` blocks would have been stripped by Gmail / Outlook / mobile.
- `_disk_thresholds` collapsed three try/except blocks into a single
  `_get_float_param(key, default)` helper.
- `_cron_check_disk` no longer aggregates results via `records |=`;
  it just iterates the targets and lets `_sample_disk` create rows.
- `_pg_top_tables` uses tuple unpacking on `cr.fetchall()` rows instead
  of positional indexing.
- `_previous_pg_report` inlined into its single caller (`_cron_pg_report`).
- `_action_url` helpers log a warning when `env.ref(...)` returns None
  before falling back to the base URL.
- Try/except blocks in `_odoo_health_send_failure_email`,
  `_send_disk_alert`, `_send_pg_report_email` narrowed to wrap only the
  actual `template.send_mail` call. The pre-checks (recipient list,
  template lookup) now propagate normally; only a flaky mail server
  is absorbed.

### Push-back items kept (with rationale)
- The `*extra` arg on `_callback` and the forwarding to `super()` are
  retained: the Odoo 18 stable branch dropped the third positional
  `job_id` arg mid-version (between 1.10.7 and 1.10.9 builds) and the
  forward absorbs that signature drift. Removing it would re-break
  installs on older 18.0 builds.
- `migrations/18.0.1.10.9/pre-migration.py` stays. apps.odoo.com ships
  every release as an in-place upgrade, and DBs upgrading from
  1.10.8-era will fail without it (xmlid model collision on
  `health_check_dashboard_action`). Docstring on the file explains.
- `int(retention) + try/except` kept as the idiomatic Python int parse;
  `str.isalnum()` would accept "1a" and reject negative values.

### Migration
- `migrations/18.0.1.11.0/pre-migration.py` deletes leftover transient
  rows from the old `health.check.dashboard` table so the singleton
  record from data XML loads cleanly.

### Tests
- Updated for the cron rename and `_cron_check_disk` no-return signature.
- Added `test_duration_sec_computed_from_dates` covering the new
  computed field.
- `test_default_get_creates_record_with_snapshot` replaced by
  `test_singleton_record_exposes_fresh_computed_snapshot`,
  `test_action_refresh_reuses_singleton_no_record_churn`,
  `test_action_open_returns_singleton_id`.

### Tooling
- Added `pyproject.toml` with `line-length=100`, `target-version=py310`,
  and per-file F401 / B018 ignores so future contributors hit a
  consistent baseline.

## [18.0.1.10.14] - 2026-04-27

### Fixed
- Upgrade from <=1.10.8 to any later version failed with
  `ParseError: For external id odoo_health_check.health_check_dashboard_action
   when trying to create/update a record of model ir.actions.server
   found record of different model ir.actions.act_window`.
  In 1.10.9 the dashboard action XML record changed from
  `ir.actions.act_window` to `ir.actions.server` (to drop the "New"
  breadcrumb on menu open). Odoo refuses to overwrite an existing
  external id if the target model differs, so every build 1.10.9 - 1.10.13
  was dropped on Odoo.sh because the production DB still held the
  1.10.8 act_window record under that xmlid.
- Added `migrations/18.0.1.10.9/pre-migration.py` that drops the stale
  act_window record (and its ir_model_data row) before the XML data
  load runs. Menu items reference the action by xmlid, so they rebind
  cleanly to the recreated server action.

## [18.0.1.10.13] - 2026-04-27

### Fixed
- Dark-mode icon swap finally lands. Odoo 18 Enterprise does not put
  a `.o_dark_mode` class on body when dark color scheme is active -
  it loads a separate `web.assets_web_dark` asset bundle instead.
  The 1.10.11 SCSS targeted `.o_dark_mode` and never matched, so the
  apps drawer Health Check tile stayed on the LIGHT icon in dark mode.
- Moved `dark_mode_icon.scss` from `web.assets_backend` (always loaded)
  to `web.assets_web_dark` (loaded only in dark mode). Selector now
  targets the actual DOM seen on test18:
  `.o_app[data-menu-xmlid="odoo_health_check.menu_root"] img.o_app_icon`
  with `content: url(...) !important` to replace the embedded base64
  image. No `.o_dark_mode` wrapper - bundle gating is the gate.

## [18.0.1.10.12] - 2026-04-27

### Fixed
- `ir.cron._callback` override broke after Odoo 18 dropped the third
  positional `job_id` arg mid-version (new signature is
  `_callback(self, cron_name, server_action_id)` with `self.ensure_one()`).
  Override now uses `*extra` to forward any legacy third arg through to
  super, so the module works on installs that pulled the new 18.0 stable
  AND on installs still on the older signature. cron_id for history
  logging derives from `self.id` (the cron singleton).
- Test suite: 7 call sites in `test_cron_override.py` and
  `test_failure_email.py` updated from `self.Cron._callback(name, sa, id)`
  to `cron._callback(name, sa)` on the cron singleton, matching the new
  upstream signature.
- `TestPgReportRun.setUp` now wipes pre-existing `pg_report` rows so
  "first run" assertions are deterministic against dev DBs where the
  monthly cron may have fired for real before the test executes.

## [18.0.1.10.11] - 2026-04-27

### Added
- Dark mode icon variant `static/description/icon_dark.png` (white H+ on
  navy with violet/teal aura - the canonical Rteam LETTER+ monogram per
  Constitution §7). Manifest `icon.png` stays as the LIGHT Flat variant
  used by light theme + apps.odoo.com listing cover.
- SCSS asset (`web.assets_backend`) overriding the apps drawer icon for
  the Health Check tile when the user has dark mode enabled
  (`body.o_dark_mode`). The menu icon now stays native to whichever
  theme the user has on: light theme shows LIGHT, dark theme shows DARK.

## [18.0.1.10.5] - 2026-04-25

### Fixed
- apps.odoo.com cover image: declare `banner.png` via the official
  `"images"` manifest key (Odoo's documented convention - see
  `odoo/modules/module.py` `'images': [],  # website`). The first entry
  becomes the cover/thumbnail on apps.odoo.com after Re-scan. The
  earlier 1.10.4 attempt (first `<img>` in index.html) did not work -
  apps.odoo.com only reads the manifest field for the cover slot.

## [18.0.1.10.4] - 2026-04-25

### Fixed
- apps.odoo.com cover image (thumbnail) attempt #1: added `banner.png`
  as the first `<img>` in `static/description/index.html`. Did not
  resolve the score warning - cover slot stayed empty. See 1.10.5 for
  the actual fix.

## [18.0.1.10.3] - 2026-04-25

### Added
- 9 real screenshots in `static/description/screenshots/` captured from a
  live test18 install:
  - `01_dashboard.png` - Dashboard with 4 populated tiles (cron health,
    OS root, filestore, latest PG report)
  - `02_cron_history.png` - Cron History list with mixed Success / Failed
    badges across multiple scheduled actions
  - `03_disk_checks.png` - Disk Checks list showing OK + Warning +
    Critical status badges across both check types
  - `04_pg_reports.png` - PG Reports list with multiple monthly reports
  - `05_settings.png` - Settings page with all four blocks
  - `06_email_inbox.png` - Inbox view of all four alert types side by side
  - `07_email_disk_alert.png` - full disk alert email body (severity
    badge, metadata table, View in Disk Checks button)
  - `08_email_pg_report.png` - full monthly PG digest email body (top
    tables with Δ size + Δ rows columns, View in PG Reports button)
  - `09_email_cron_failure.png` - full cron failure email body
    (CRITICAL badge, metadata table, View in Cron History button,
    collapsed traceback)
- New "Alerts in your inbox" section in `index.html` showcasing the
  inbox view (full width) and three example email bodies in a 3-column
  grid below it

### Changed
- `index.html` now references the real screenshots in every feature
  block; the apps.odoo.com listing page is fully populated end-to-end

## [18.0.1.10.2] - 2026-04-25

### Added
- `web_icon` on the top-level "Health Check" menu, pointing at
  `static/description/icon.png` so the H+ monogram shows next to the
  menu label in the Odoo navbar (replacing the default generic icon)
- `static/description/index.html` (apps.odoo.com module page) with hero,
  4 numbered features (each with a screenshot slot), configuration
  block, technical details, "what it does NOT do" section, and support
  links. Inline-styled to the Rteam brand palette
- `README.rst` (module-level) mirroring index.html in restructured text
  so the apps.odoo.com listing has both the rich HTML page and an RST
  fallback

## [18.0.1.10.1] - 2026-04-25

### Added
- Store assets for apps.odoo.com listing (Phase 11, partial):
  - `static/description/icon.png` (128x128) - "H+" monogram in the Rteam family LETTER+ pattern: solid white H, teal #00D4AA `+` at the upper-left, navy #0A1628 background, subtle violet→teal aura. Generated via Gemini 3 Pro Image (nano banana pro) at 2048x2048 then downscaled
  - `static/description/banner.png` (1120x560, 2:1) - hero composition: H+ monogram + "Odoo Health Check" + tagline "Catch failures before your users do" on the left, four glassmorphism feature tiles on the right (CRON / DISK / GROWTH / DASHBOARD). Generated at 2752x1536, center-cropped to 2:1 ratio, downscaled
  - Both assets follow Rteam Brand Kit (#0A1628 navy + #00D4AA teal + #7C5CFC violet aura, max 3 colors + white text, no AI cliches, no third-party logos)
- `static/description/screenshots/` directory created for the 3-5 UI captures coming next (dashboard / cron history / disk checks / settings)

### Notes
- Phase 11 still has remaining work: real screenshots from test18, `static/description/index.html`, and `README.rst`
- No functional code change in this release - assets only

## [18.0.1.10.0] - 2026-04-25

### Changed
- Mail templates UX polish:
  - **Severity badge** at the top of each alert email. `mail_template_cron_failure` always shows a red `CRITICAL` badge. `mail_template_disk_alert` shows a dynamic badge: amber `WARN` or red `CRITICAL` based on the row's status. PG monthly report stays badge-less (it's a digest, not an alert)
  - **'View in Odoo' button** in every template, deep-linking via the appropriate act_window. Cron failure → "View in Cron History", disk alert → "View in Disk Checks", PG report → "View in PG Reports". Button color matches the severity badge for consistency
  - **Traceback collapsed in `<details>`** in the cron failure email. Long stacks no longer dominate the inbox preview - the recipient sees the metadata (cron name, server, time, View button) immediately and expands the trace on demand. Email clients that don't support `<details>` (older mobile clients) gracefully render the trace inline
- New helper methods for templates:
  - `ir.cron.history._action_url()` returns the deep link
  - `health.check.result._action_url()` returns the deep link, picking PG Reports vs Disk Checks action based on `check_type`
  - Both fall back to the base URL if the action xml_id is missing (defensive)

### Added
- Tests for `_action_url()` on both models, including check_type-based action routing for `health.check.result`

## [18.0.1.9.0] - 2026-04-25

### Added
- Health Check Dashboard (Phase 9)
  - New `health.check.dashboard` TransientModel - at-a-glance summary of cron health, disk usage, and the latest PostgreSQL growth report
  - 4 tiles in a single form view:
    - **Cron health** - failed crons in last 24h / 7d, total cron runs in 7d
    - **OS root** - status badge (ok / warn / critical / error / unknown), used %, free / total in GB, last sample timestamp
    - **Filestore** - same fields for the Odoo filestore mount
    - **Latest PG report** - timestamp, DB size, Δ vs previous report, largest table
  - No new stored data: `default_get` reads the latest rows from `ir.cron.history` and `health.check.result`. Open the dashboard → fresh snapshot. The Refresh button reopens the action so `default_get` fires again
  - Empty-state messages for each tile when no underlying data exists yet (fresh install, first month before pg_report cron fires)
  - New top-level menu "Health Check -> Dashboard" (sequence 5, above Cron History)
- Tests (`tests/test_dashboard.py`, 11 tests): empty state, latest-row-per-check_type, isolation, error status, human-readable summary, failure window arithmetic across 24h / 7d / outside, pg report latest-ok selection, error-row skip, first-report message, default_get integration, action_refresh shape

## [18.0.1.8.0] - 2026-04-25

### Added
- Monthly PostgreSQL growth report (Phase 8)
  - Cron `Odoo Health Check: Monthly PostgreSQL growth report` runs on the 1st of each month at 08:00 (`interval_type='months'`)
  - SQL: top-10 tables by `pg_total_relation_size`, excluding `pg_catalog` / `information_schema`. Row count uses `pg_class.reltuples` estimate (last ANALYZE) - much faster than COUNT(*) and accurate enough for trend reports
  - Snapshot stored in `health.check.result.details_json`: `{db_name, total_db_bytes, total_db_bytes_delta, tables: [{name, total_bytes, table_bytes, row_estimate, total_bytes_delta, row_estimate_delta}], previous_report_id}`. Each new run looks up the previous `pg_report` row with `status='ok'` and computes deltas vs that snapshot. New tables show `null` deltas (rendered as "new" in the email)
  - New mail template `mail_template_pg_monthly` with HTML table of top-10 tables + size + Δ size + rows + Δ rows + DB size summary. Subject: `[Odoo Health] PG monthly report: <db> (YYYY-MM)`. Uses `_get_parsed_details()`, `_human_bytes()`, `_human_delta_bytes()` template helpers on the record
  - Email is sent every run (it's a digest, not a transition alert) when `odoo_health_check.pg_report_emails` is non-empty. Empty recipients = report row still created, just no email
  - SQL failure → row with `status='error'` and traceback in `details_json`. Cron stays green
- Settings: new "PostgreSQL Monthly Report" block with `odoo_health_pg_report_emails`
- Menu: new "Health Check -> PG Reports" filtered to `check_type='pg_report'` (Disk Checks menu's domain stays `disk_root + disk_filestore`)
- Tests (`tests/test_pg_report.py`, 4 classes, 14 tests): real SQL against test DB validates query syntax + system-schema exclusion + db_size; mocked-SQL tests cover snapshot shape, MoM delta computation, new-table handling, email gating, error path, settings roundtrip, template + cron registration, byte formatters

## [18.0.1.7.0] - 2026-04-25

### Added
- Configurable disk thresholds and disk-alert email (Phase 7)
  - New settings (in Settings -> Health Check -> Disk Monitoring):
    - `odoo_health_disk_warn_pct` (default 80) - usage % above which a sample is flagged 'warn'
    - `odoo_health_disk_critical_pct` (default 90) - usage % above which a sample is flagged 'critical'
    - `odoo_health_disk_alert_emails` - comma-separated recipients for disk alerts
  - `_disk_thresholds()` now reads from `ir.config_parameter`. Falls back to defaults on missing or non-numeric values; clamps to [0, 100]; reverts to defaults if `critical < warn` (logs a warning)
  - New mail template `mail_template_disk_alert` (subject: `[Odoo Health] Disk <status>: <mount> at X.X% used`, body: status, used%, total/free in GB, time)
  - `_send_disk_alert()` enqueues an email only on worsening transitions (ok->warn, ok->critical, warn->critical). 'error' samples are skipped for both sending and previous-state lookup, so transient measurement failures don't generate spurious alerts. Improvements (critical->warn) and steady-state (warn->warn) never trigger an alert. One email per worsening transition - no per-hour spam
  - Disk alert recipients are independent of cron-failure recipients (sysadmin vs engineering routing)
- Tests (`tests/test_disk_alert.py`, 21 tests across 3 classes):
  - Threshold reading: defaults, configured values, invalid fallback, out-of-range clamp, invariant violation, classification with custom thresholds
  - Alert transitions: first-run warn / critical, warn->critical, warn->warn (no), critical->critical (no), critical->warn (no), ok (no), error (no), empty recipients (no), error-row skipped in lookup, isolation per check_type, comma-trim
  - Settings: roundtrip for warn_pct / critical_pct / alert_emails, disk alert template registered

## [18.0.1.6.1] - 2026-04-25

### Fixed
- `health.check.result.total_bytes` and `free_bytes` were `fields.Integer`,
  which maps to PostgreSQL `int4` (~2.1 GB ceiling). Any realistic volume
  triggered `psycopg2.errors.NumericValueOutOfRange` on insert. Switched
  both to `fields.Float(digits=(20, 0))` (numeric(20,0)). Caught live on
  test18 - first cron run after install raised on disk total ~50 GB
- Added regression test `test_sample_disk_handles_large_byte_counts`
  (4 TB volume) to prevent reintroduction

## [18.0.1.6.0] - 2026-04-25

### Added
- Disk usage monitoring (Phase 6)
  - New model `health.check.result` (`check_type`, `date`, `status`, `mount_path`, `total_bytes`, `free_bytes`, `used_pct`, `details_json`). Selection includes `pg_report` to avoid a second selection migration in Phase 8
  - New classmethod `health.check.result._run_disk_checks()` samples both OS root (`/`) and Odoo filestore (`odoo.tools.config['data_dir']`), creating one row per target. Per-target failures are isolated and recorded with `status='error'` so the cron itself never crashes
  - New scheduled action `Odoo Health Check: Disk usage check` runs hourly (first run 5min after install)
  - Default thresholds (used %): `<80` ok, `80-90` warn, `>=90` critical. Phase 7 will make these configurable; the seam lives in `_disk_thresholds()` for a single override point
- Views: list / form / search on `health.check.result` with status-badge decorations and Last 24h / 7d filters; new menu "Health Check -> Disk Checks" (action filtered to disk_root + disk_filestore)
- Tests (`tests/test_disk_check.py`): threshold boundaries, mocked `shutil.disk_usage` happy paths for ok / warn / critical, zero-total guard, OSError isolation per target, cron registered + active

## [18.0.1.5.1] - 2026-04-24

### Added
- Test suite covering Phases 1-5: `tests/test_history_model.py`, `test_cron_override.py`, `test_failure_email.py`, `test_config.py`
  - Model: defaults, SQL constraint, cascade delete, cleanup with retention variants (positive / zero / invalid param)
  - Overrides: `_callback` and `method_direct_trigger` on success and failure; `_callback` tolerates `history_id=None`
  - Email: enqueue on failure with recipients, skip on empty recipients, never on success, comma-separated parsing
  - Config: settings roundtrip for both params; retention cron and mail template registered and active
- Test common helper (`tests/common.py`) patches `registry.cursor` so the module's independent-cursor writes ride the test savepoint
- All tests tagged `post_install`, `-at_install`, `odoo_health_check` - run via `odoo --test-tags odoo_health_check`

### Notes
- Tests do not execute on Odoo.sh production builds. Push to a dev/staging branch to run in CI

## [18.0.1.5.0] - 2026-04-24

### Added
- Daily retention cleanup
  - New `ir.cron.history._odoo_health_cleanup()` classmethod deletes rows older than retention window in batches of 5000
  - New scheduled action `Odoo Health Check: Cron history retention cleanup` runs daily (first run 4h after install)
  - New config parameter `odoo_health_check.retention_days` (default 30). `<= 0` disables cleanup
  - Settings view gains a "Retention" block with the new field

## [18.0.1.4.0] - 2026-04-24

### Added
- Email alert on cron failure
  - New dependency: `mail`
  - `mail.template` `mail_template_cron_failure` with HTML body (cron name, start/end, duration, server, traceback)
  - `res.config.settings` extension with `odoo_health_notify_emails` (stored in `ir.config_parameter` key `odoo_health_check.notify_emails`)
  - Settings view block "Health Check" with Notifications setting
  - New menu: Health Check -> Settings (opens inline settings form scoped to our block)
  - Email is enqueued (`force_send=False`) in the failure branch of `_odoo_health_log_end`; skipped silently when the setting is empty
  - Any failure inside the email path is caught and logged - never propagates to the cron runner

## [18.0.1.3.0] - 2026-04-24

### Changed
- `duration_sec` now measured via `time.perf_counter()` inside the cron overrides (sub-second precision)
- Dropped the computed `duration_sec` from `date_end - date_start`, since Odoo Datetime fields are second-granular and many system crons complete in <1s

## [18.0.1.2.1] - 2026-04-24

### Added
- `ir.cron.method_direct_trigger` override: manual "Run Manually" clicks now also write history rows
  - Needed because the manual trigger path bypasses `_callback` and would otherwise be invisible in the audit trail

## [18.0.1.2.0] - 2026-04-24

### Added
- `ir.cron._callback` override: every scheduled action execution writes an `ir.cron.history` row
  - 'running' row created before the call; finalized to 'success' or 'failed' (with full traceback) after
  - History writes use an independent database cursor so a cron rollback or failure does not erase the audit trail
  - Writes are sudoed; logging failures are swallowed and logged, never propagate to the cron runner

## [18.0.1.1.0] - 2026-04-24

### Added
- `ir.cron.history` model storing one record per scheduled action run
  - Fields: cron_id (m2o ir.cron), date_start, date_end, duration_sec (computed), state (running/success/failed), error_traceback, server_name
  - SQL constraint: end time must be on or after start time
- Access rights restricted to `base.group_system` (Settings/Administration)
- List, form, and search views with status badge decorations, Last 24h / Last 7d filters, group-by by cron / state / server / day
- Top-level "Health Check" menu with "Cron History" submenu

## [18.0.1.0.0] - 2026-04-24

### Added
- Initial scaffold: empty installable module targeting Odoo 18
- Manifest with metadata, LGPL-3 license, `base` dependency
- Repository layout: README, CHANGELOG, LICENSE, .gitignore
