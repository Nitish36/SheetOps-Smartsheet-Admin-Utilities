from flask import Flask, request, render_template, send_file
import requests
import pandas as pd
from io import BytesIO
import urllib3
urllib3.disable_warnings()

app = Flask(__name__, template_folder='template')

SMRTSHEET_GROUPS_URL = "https://api.smartsheet.com/2.0/groups"

@app.route("/", methods=["GET", "POST"])
def index():
    error = None

    if request.method == "POST":
        action = request.form.get("action")
        api_key = request.form.get("api_key")

        if not api_key:
            return render_template("index.html", error="API key is required")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        response = requests.get(SMRTSHEET_GROUPS_URL, headers=headers, verify=False)

        if response.status_code != 200:
            return render_template("index.html", error="Invalid API key or API error")

        data = response.json().get("data", [])
        df = pd.DataFrame(data)

        # -------- CSV --------
        if action == "csv":
            output = BytesIO()
            df.to_csv(output, index=False)
            output.seek(0)

            return send_file(
                output,
                mimetype="text/csv",
                as_attachment=True,
                download_name="smartsheet_groups.csv"
            )

    # GET request OR after CSV download
    return render_template("index.html")



if __name__ == "__main__":
    app.run(debug=True)
