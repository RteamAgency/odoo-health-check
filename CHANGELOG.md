# Changelog

All notable changes to this module are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Module versioning: `<odoo_major>.0.<major>.<minor>.<patch>`.

## [14.0.1.0.0] - 2026-05-07

Initial public release for Odoo 14. Branched from the v15 listing release
`15.0.1.0.0` plus the changes required for Odoo 14's mail engine and
ir.cron defaults.

* **Mail templates rewritten from QWeb to Jinja2.** v14 mail rendering
  uses a Jinja2 SandboxedEnvironment configured with
  `block_start_string="<%"`, `variable_start_string="${"`,
  `line_statement_prefix="%"` (Mako-flavoured Jinja2). v15 switched to
  QWeb (`{{ }}`, `t-out`, `t-if`, `t-foreach`, `t-set`). Conversions:
  `{{ expr }}` -> `${expr}`, `t-out="expr"` -> `${expr}` inline,
  `t-set="x" t-value="y"` -> `% set x = y` line statement,
  `t-attf-style="{{ s }}"` -> `style="${s}"`, `t-att-href="x"` ->
  `href="${x}"`, `t-if`/`t-else`/`t-elif` -> `% if`/`% else`/`% elif`,
  `t-foreach`/`t-as` -> `% for x in y`. `is None` -> `is none`
  (Jinja2 lower-case singletons).
* **`<field name="numbercall">-1</field>` added on every cron record.**
  v14-v17 ir.cron has `numbercall = fields.Integer(default=1, ...)`,
  so a freshly-installed cron with no explicit numbercall fires once
  and the scheduler's UPDATE clause sets `active=False`. The
  apps.odoo.com release of v17.0.1.0.0 has the same latent bug;
  see Constitution §6 follow-up. v18 dropped the field entirely.
* Reset module version to 14.0.1.0.0 (first publication on the v14
  apps.odoo.com listing per Constitution §6).
* Listing description, README, and listing chrome (badge, monospace
  pill) updated to mention Odoo 14.

Features brought forward from the v15 listing:

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
