{
    "name": "System B (Signage Sync)",
    "version": "20.0.1.0.0",
    "category": "Operations",
    "author": "Floyd",
    "summary": "Imports device and content CSV files into the database",
    "depends": ["base"],
    "data": [
        "security/ir.access.csv",
        "data/cron.xml",
        "views/res_config_settings_views.xml",
        "views/device_views.xml",
        "views/content_views.xml",
        "views/menu.xml",
    ],
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}
