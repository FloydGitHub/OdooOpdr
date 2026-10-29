from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    csv_folder_path = fields.Char(
        string="CSV Import Folder",
        config_parameter="system_b.csv_folder_path",
        default="",
    )

    csv_delimiter = fields.Char(
        string="CSV Delimiter",
        config_parameter="system_b.csv_delimiter",
        default=",",
        required=True,
    )
