from flask import Flask, request, render_template, send_file
import requests
import pandas as pd
from io import BytesIO
import urllib3
urllib3.disable_warnings()

app = Flask(__name__, template_folder='template')

GROUPS_URL = "https://api.smartsheet.com/2.0/groups"
USERS_URL = "https://api.smartsheet.com/2.0/users"

# Route to get group data
@app.route("/", methods=["GET", "POST"])
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

    return render_template("index.html")

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



if __name__ == "__main__":
    app.run(debug=True)
