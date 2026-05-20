# Changelog

All notable changes to this module are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Module versioning: `<odoo_major>.0.<major>.<minor>.<patch>`.

## [14.0.1.0.1] - 2026-05-20

Fixes for three Odoo 14 mail-rendering bugs in the v14 backport (none
caught by the v15->v14 conversion; all only surface on a live Odoo 14
Jinja2 render, not at XML parse time), plus a code review pass.

* **`% set` line statements no longer dropped on install.** Odoo 14's
  `type="html"` data loader serialises child elements only
  (`"".join(etree.tostring(n) for n in node)` in
  `odoo/tools/convert.py`), discarding `field.text`. The `% set` style
  vars sat before the root `<div>` as `field.text` and vanished at
  install, so every `${badge_style}` / `${accent}` rendered as
  `Undefined`. Moved the `% set` block inside the root `<div>` (whose
  style is literal, so render order stays correct).
* **Private model helpers bridged into the Jinja context.** Odoo 14
  renders mail bodies through a `SandboxedEnvironment` whose
  `is_safe_attribute()` rejects any `_`-prefixed attribute, so
  `object._action_url()` / `object._get_parsed_details()` / the byte
  formatters raised `SecurityError` at send time. New
  `models/mail_render_mixin.py` overrides `_render_jinja_eval_context`
  to expose them as `hc_*` globals; the methods stay private. v15+ uses
  QWeb (no sandbox restriction) and does not need this.
* **`&gt;` removed from a Jinja line statement.** `% elif ... &gt; 0:`
  was re-escaped to `&gt;` by the html serialiser and broke Python
  expression parsing (`TemplateSyntaxError`). Replaced with the
  `hc_signed_int` helper.
* **`health.check.dashboard`**: dropped redundant `readonly=True` on the
  computed (`store=False`) fields; computed non-stored fields are
  read-only by default. Kept on the stored `name` field.
* **`ir.cron._odoo_health_log_end`**: write the history row in its own
  cursor (lock released on commit) and enqueue the failure email in a
  separate cursor afterwards, so the slow template render / mail.mail
  creation no longer runs while holding the history row lock. Both
  cursors stay isolated from the monitored cron's transaction so the
  history write and the alert survive its rollback.
* **Tests**: `test_failure_email` called `_callback` with two positional
  args; Odoo 14's signature requires the third (`job_id`). Fixed all
  four call sites.

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
