from flask import Flask, request, render_template, send_file
import requests
import pandas as pd
from io import BytesIO
import urllib3
import secrets
urllib3.disable_warnings()

def secret_key():
    token = secrets.token_hex(10)
    return token

app = Flask(__name__, template_folder='template')
app.config['SECRET_KEY'] = secret_key()

GROUPS_URL = "https://api.smartsheet.com/2.0/groups"
USERS_URL = "https://api.smartsheet.com/2.0/users"
SHEETS_URL = "https://api.smartsheet.com/2.0/sheets"
REPORTS_URL = "https://api.smartsheet.com/2.0/reports"
WORKSPACE_URL = "https://api.smartsheet.com/2.0/workspaces"
WEBHOOK_URL = "https://api.smartsheet.com/2.0/webhooks"
DASHBOARD_URL = "https://api.smartsheet.com/2.0/sights"

@app.route("/", methods=["GET","POST"])
def fetch_home():
    error = None
    return render_template("index.html")

# Route to get group data
@app.route("/groups", methods=["GET", "POST"])
def fetch_groups():
    error = None

    if request.method == "POST":
        api_key = request.form.get("api_key")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        response = requests.get(GROUPS_URL, headers=headers, verify=False)

        if response.status_code != 200:
            return "Invalid API key or API error", 400

        data = response.json().get("data", [])

        # Convert to DataFrame
        df = pd.DataFrame(data)

        # Create CSV in memory
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return send_file(
            output,
            mimetype="text/csv",
            as_attachment=True,
            download_name="smartsheet_groups.csv"
        )

    return render_template("group.html")

# Route to get user data
@app.route("/users", methods = ["GET","POST"])
def fetch_users():
    error = None

    if request.method == "POST":
        api_key = request.form.get("api_key")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        response = requests.get(USERS_URL, headers=headers, verify=False)

        if response.status_code != 200:
            return "Invalid API key or API error", 400

        data = response.json().get("data", [])
        df = pd.DataFrame(data)

        # Create CSV in memory
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return send_file(
            output,
            mimetype="text/csv",
            as_attachment=True,
            download_name="smartsheet_users.csv"
        )

    return render_template("users.html")

@app.route("/sheets", methods=["GET","POST"])
def fetch_sheets():
    error = None
    if request.method == "POST":
        api_key = request.form.get("api_key")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        response = requests.get(SHEETS_URL, headers=headers, verify=False)

        if response.status_code != 200:
            return "Invalid API key or API error", 400

        data = response.json().get("data", [])
        df = pd.DataFrame(data)

        # Create CSV in memory
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return send_file(
            output,
            mimetype="text/csv",
            as_attachment=True,
            download_name="smartsheet_sheets.csv"
        )

    return render_template("sheets.html")

@app.route("/reports", methods=["GET","POST"])
def fetch_reports():
    error = None
    if request.method == "POST":
        api_key = request.form.get("api_key")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        response = requests.get(REPORTS_URL, headers=headers, verify=False)

        if response.status_code != 200:
            return "Invalid API key or API error", 400

        data = response.json().get("data", [])
        df = pd.DataFrame(data)

        # Create CSV in memory
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return send_file(
            output,
            mimetype="text/csv",
            as_attachment=True,
            download_name="smartsheet_report.csv"
        )

    return render_template("reports.html")

@app.route("/webhooks", methods=["GET","POST"])
def fetch_webhooks():
    error = None
    if request.method == "POST":
        api_key = request.form.get("api_key")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        response = requests.get(WEBHOOK_URL, headers=headers, verify=False)

        if response.status_code != 200:
            return "Invalid API key or API error", 400

        data = response.json().get("data", [])
        df = pd.DataFrame(data)

        # Create CSV in memory
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return send_file(
            output,
            mimetype="text/csv",
            as_attachment=True,
            download_name="smartsheet_webhook.csv"
        )

    return render_template("webhook.html")

@app.route("/dashboards", methods=["GET","POST"])
def fetch_dashboards():
    error = None
    if request.method == "POST":
        api_key = request.form.get("api_key")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        response = requests.get(DASHBOARD_URL, headers=headers, verify=False)

        if response.status_code != 200:
            return "Invalid API key or API error", 400

        data = response.json().get("data", [])
        df = pd.DataFrame(data)

        # Create CSV in memory
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return send_file(
            output,
            mimetype="text/csv",
            as_attachment=True,
            download_name="smartsheet_dashboard.csv"
        )

    return render_template("dashboard.html")

@app.route("/workspaces", methods=["GET","POST"])
def fetch_workspace():
    error = None
    if request.method == "POST":
        api_key = request.form.get("api_key")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        response = requests.get(WORKSPACE_URL, headers=headers, verify=False)

        if response.status_code != 200:
            return "Invalid API key or API error", 400

        data = response.json().get("data", [])
        df = pd.DataFrame(data)

        # Create CSV in memory
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return send_file(
            output,
            mimetype="text/csv",
            as_attachment=True,
            download_name="smartsheet_workspace.csv"
        )

    return render_template("workspace.html")

@app.route("/about", methods=["GET","POST"])
def fetch_about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=True)
