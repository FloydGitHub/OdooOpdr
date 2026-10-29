from odoo import models, fields

class Content(models.Model):
    _name = "system_b.content"

    _content_id_unique = models.Constraint(
        "UNIQUE(content_id)",
        "Every content ID must be unique.",
    )

    content_id = fields.Integer(string="Content ID", required=True, index=True)
    name = fields.Char(string="Name",size=100, required=True)
    description = fields.Char(string="Description", size=128,)
    device_id = fields.Many2one(
        comodel_name="system_b.device",
        string="Device",
        required=True,
        ondelete="restrict",
    )
    expire_date = fields.Datetime(string="Expiration Date")
    state = fields.Selection(
        [
            ("enabled", "Enabled"),
            ("disabled", "Disabled"),
            ("deleted", "Deleted"),
        ],
        string="State",
        default="enabled",
        required=True,
    )

    def disable_experired_content(self):
        now = fields.Datetime.now()

        expired_content = self.search([
            ("expire_date", "<", now),
            ("state", "=", "enabled"),
        ])

        expired_content.write({"state":"disabled"})

