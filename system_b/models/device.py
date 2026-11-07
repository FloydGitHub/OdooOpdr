from odoo import models, fields

class Device(models.Model):
    _name = "system_b.device"
    _description = "Signage Device"

    _device_id_unique = models.Constraint(
        "UNIQUE(device_id)",
        "Every device ID must be unique.",
    )

    _code_unique = models.Constraint(
        "UNIQUE(code)",
        "Every device code must be unique.",
    )


    device_id = fields.Integer(string="Device ID", required=True, index=True)
    name = fields.Char(string="Name",size=32, required=True)
    description = fields.Char(string="Description", size=128,)
    code = fields.Char(string="Code", size=30, required=True)
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

    def disable_expired_devices(self):
        now = fields.Datetime.now()

        expired_devices = self.search([
            ("expire_date", "<", now),
            ("state", "=", "enabled"),
            ("expire_date", "!=", False),
        ])

        expired_devices.write({"state":"disabled"})