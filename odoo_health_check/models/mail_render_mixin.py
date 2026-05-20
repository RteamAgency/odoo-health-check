from odoo import api, models

from .health_check_result import _human_bytes, _human_delta_bytes


class MailRenderMixin(models.AbstractModel):
    _inherit = "mail.render.mixin"

    @api.model
    def _render_jinja_eval_context(self):
        """Bridge the module's helpers into the Jinja render context.

        Odoo 14 renders mail.template bodies through a Jinja
        SandboxedEnvironment whose is_safe_attribute() rejects every
        attribute that starts with "_" (see
        addons/mail/models/mail_render_mixin.py). Calling
        object._action_url() / object._get_parsed_details() / the byte
        formatters directly from the template raises SecurityError at
        send time, so the private helpers are exposed here as public
        globals named hc_*. The methods themselves stay private on the
        model (no public-wrapper-for-mechanism anti-pattern).

        v15+ renders these same templates with QWeb, which has no such
        restriction and calls object._helper() directly. This override
        is therefore v14-only.
        """
        ctx = super()._render_jinja_eval_context()
        ctx.update({
            "hc_human_bytes": _human_bytes,
            "hc_human_delta_bytes": _human_delta_bytes,
            "hc_signed_int": lambda n: f"+{n}" if n > 0 else f"{n}",
            "hc_action_url": lambda obj: obj._action_url(),
            "hc_parsed_details": lambda obj: obj._get_parsed_details(),
        })
        return ctx
