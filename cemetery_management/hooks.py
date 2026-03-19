app_name = "cemetery_management"
app_title = "Cemetery Management"
app_publisher = "PS Church"
app_description = "Cemetery plot and burial record management for Frappe/ERPNext"
app_email = "soulxone@gmail.com"
app_license = "AGPLv3"
required_apps = ["frappe", "erpnext", "church_mrm"]

# App Icon
app_icon = "/assets/cemetery_management/images/cemetery.svg"
app_color = "#4A7C59"
app_icon_color = "#FFFFFF"

after_install = "cemetery_management.install.after_install"

# Include CSS and JS in all pages
app_include_css = "/assets/cemetery_management/css/cemetery.css"
app_include_js = "/assets/cemetery_management/js/cemetery.js"

# Extend Church Member DocType
doc_events = {
    "Church Member": {
        "validate": "cemetery_management.overrides.church_member.on_validate",
    }
}

# Fixtures - Custom Fields added to existing DocTypes
fixtures = [
    {
        "dt": "Custom Field",
        "filters": [["module", "=", "Cemetery Management"]]
    },
    {
        "dt": "Property Setter",
        "filters": [["module", "=", "Cemetery Management"]]
    },
    {
        "dt": "Number Card",
        "filters": [["module", "=", "Cemetery Management"]]
    },
]

# Scheduled Tasks
scheduler_events = {}

# Website routes
website_route_rules = [
    {"from_route": "/cemetery-search", "to_route": "cemetery_search"},
]

# Website context
website_context = {}
