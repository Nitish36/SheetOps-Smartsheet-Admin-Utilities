from flask import Flask, request, render_template, send_file, session, redirect, flash, url_for
from sqlalchemy import func
import requests
import pandas as pd
from io import BytesIO
import urllib3
import secrets
import os
from datetime import datetime,date, timezone
from database import SessionLocal
from models.user import User
from models.subscription import Subscription
from auth.security import login_required, check_trial_status
from scripts.workspace import get_workspace
from scripts.sheets import get_sheets
from scripts.dashboard import get_dashboard
from scripts.report import get_reports
from scripts.groups import get_group_members,get_all_groups,build_group_dataframe
from scripts.users import get_users
from scripts.webhook import get_webhooks
from scripts.contacts import get_pro_contact
from trial_scripts.sheets import get_trial_sheets
from trial_scripts.report import get_trial_reports
from trial_scripts.dashboard import get_trial_dashboard
from trial_scripts.webhook import get_trial_webhooks
from trial_scripts.workspace import get_trial_workspace
from trial_scripts.users import get_trial_users
from trial_scripts.groups import build_trial_group_dataframe,get_all_trial_groups
from trial_scripts.contacts import get_trial_contact
from auth.auth_routes import auth_bp
from models.usage import UsageLog

urllib3.disable_warnings()

def secret_key():
    token = secrets.token_hex(10)
    return token

app = Flask(__name__, template_folder='template')
app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", "sheetops-default-key")

app.register_blueprint(auth_bp)

GROUPS_URL = "https://api.smartsheet.com/2.0/groups"
USERS_URL = "https://api.smartsheet.com/2.0/users"
SHEETS_URL = "https://api.smartsheet.com/2.0/sheets"
REPORTS_URL = "https://api.smartsheet.com/2.0/reports"
WORKSPACE_URL = "https://api.smartsheet.com/2.0/workspaces"
WEBHOOK_URL = "https://api.smartsheet.com/2.0/webhooks"
DASHBOARD_URL = "https://api.smartsheet.com/2.0/sights"
BASE_URL = "https://api.smartsheet.com/2.0/contacts"

def init_progress():
    session["progress"] = []

def update_progress(message):
    progress = session.get("progress", [])
    progress.append(message)
    session["progress"] = progress

@app.route("/progress")
def get_progress():
    return {
        "messages": session.get("progress", [])
    }


@app.route("/generate-password")
def generate_password():
    return {"password": secrets.token_hex(8)}


@app.route("/", methods=["GET","POST"])
def fetch_home():
    error = None
    return render_template("index.html")

@app.route("/menu", methods=["GET","POST"])
@login_required
@check_trial_status
def fetch_menu():
    error = None
    return render_template("menu.html")

# Route to get group data
@app.route("/groups", methods=["GET", "POST"])
@login_required
@check_trial_status
def fetch_groups():
    if request.method == "POST":
        api_key = request.form.get("api_key")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }


        # Validate API key
        response = requests.get(GROUPS_URL, headers=headers, verify=False)
        if response.status_code != 200:
            return "Invalid API key or API error", 400

        user_plan = session.get("user_plan", "trial")

        # ✅ SINGLE dataframe variable
        g_df = pd.DataFrame()
        init_progress()
        update_progress("Starting Groups extraction")
        if user_plan == "trial":
            groups = get_all_trial_groups(GROUPS_URL, headers)
            g_df = build_trial_group_dataframe(groups)
            g_df = g_df.head(50)

        elif user_plan == "pro":
            groups = get_all_groups(GROUPS_URL, headers)
            rows, skipped = get_group_members(GROUPS_URL, headers, groups)
            g_df = build_group_dataframe(rows)

        elif user_plan == "enterprise":
            groups = get_all_groups(GROUPS_URL, headers)
            rows, skipped = get_group_members(GROUPS_URL, headers, groups)
            g_df = build_group_dataframe(rows)
            # later you can enrich enterprise data here

        # Create CSV
        output = BytesIO()
        g_df.to_csv(output, index=False)
        output.seek(0)

        return send_file(
            output,
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"smartsheet_groups_{user_plan}.csv"
        )

    return render_template("group.html")

# Route to get user data
@app.route("/users", methods = ["GET","POST"])
@login_required
@check_trial_status
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

        user_plan = session.get("user_plan", "trial")
        df = []
        if user_plan == "trial":
            data = get_trial_users(USERS_URL, headers)
            df = pd.DataFrame(data)
            df = df.head(50)

        elif user_plan == "pro":
            data = get_users(USERS_URL, headers)
            df = pd.DataFrame(data)

        elif user_plan == "enterprise":
            pass  # full data (no limit)

        # Create CSV
        update_progress("Preparing CSV file")
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        update_progress("CSV ready for download")
        update_progress("Download started")
        return send_file(
            output,
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"smartsheet_users_{user_plan}.csv"
        )

    return render_template("users.html")

@app.route("/sheets", methods=["GET", "POST"])
@login_required
@check_trial_status
def fetch_sheets():
    if request.method == "POST":
        api_key = request.form.get("api_key")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Validate key
        response = requests.get(SHEETS_URL, headers=headers, verify=False)
        if response.status_code != 200:
            return "Invalid API key or API error", 400

        # Fetch ALL sheets (same function)

        # 👇 PLAN-BASED LIMITING
        user_plan = session.get("user_plan", "trial")
        df = []
        if user_plan == "trial":
            data = get_trial_sheets(SHEETS_URL,headers)
            df = pd.DataFrame(data)
            df = df.head(50)

        elif user_plan == "pro":
            data = get_sheets(SHEETS_URL, headers)
            df = pd.DataFrame(data)

        elif user_plan == "enterprise":
            pass  # full data (no limit)

        # Create CSV
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return send_file(
            output,
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"smartsheet_sheets_{user_plan}.csv"
        )

    return render_template("sheets.html")


@app.route("/reports", methods=["GET","POST"])
@login_required
@check_trial_status
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

        user_plan = session.get("user_plan", "trial")
        df = []
        if user_plan == "trial":
            data = get_trial_reports(REPORTS_URL, headers)
            df = pd.DataFrame(data)
            df = df.head(50)

        elif user_plan == "pro":
            data = get_reports(REPORTS_URL, headers)
            df = pd.DataFrame(data)

        elif user_plan == "enterprise":
            pass  # full data (no limit)

        # Create CSV
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return send_file(
            output,
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"smartsheet_report_{user_plan}.csv"
        )

    return render_template("reports.html")

@app.route("/webhooks", methods=["GET","POST"])
@login_required
@check_trial_status
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

        user_plan = session.get("user_plan", "trial")
        df = []
        if user_plan == "trial":
            data = get_trial_webhooks(WEBHOOK_URL, headers)
            df = pd.DataFrame(data)
            df = df.head(50)

        elif user_plan == "pro":
            data = get_webhooks(WEBHOOK_URL, headers)
            df = pd.DataFrame(data)

        elif user_plan == "enterprise":
            pass  # full data (no limit)

        # Create CSV
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return send_file(
            output,
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"smartsheet_webhook_{user_plan}.csv"
        )

    return render_template("webhook.html")

@app.route("/dashboards", methods=["GET","POST"])
@login_required
@check_trial_status
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

        user_plan = session.get("user_plan", "trial")
        df = []
        if user_plan == "trial":
            data = get_trial_dashboard(DASHBOARD_URL, headers)
            df = pd.DataFrame(data)
            df = df.head(50)

        elif user_plan == "pro":
            data = get_dashboard(DASHBOARD_URL, headers)
            df = pd.DataFrame(data)

        elif user_plan == "enterprise":
            pass  # full data (no limit)

        # Create CSV
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return send_file(
            output,
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"smartsheet_dashboard_{user_plan}.csv"
        )

    return render_template("dashboard.html")


@app.route("/contacts", methods=["GET", "POST"])
@login_required
@check_trial_status
def fetch_contacts():
    if request.method == "POST":
        api_key = request.form.get("api_key")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Determine the URL
        # BASE_URL in your main.py should be "https://api.smartsheet.com/2.0/contacts"
        CONTACTS_URL = f"{BASE_URL}/contacts" if not BASE_URL.endswith("/contacts") else BASE_URL

        user_plan = session.get("user_plan", "trial")

        # 1. Fetch Data based on plan
        if user_plan == "pro" or user_plan == "enterprise":
            data = get_pro_contact(CONTACTS_URL, headers)
        else:
            # Your existing trial function with the 50 limit
            data = get_trial_contact(CONTACTS_URL, headers)

        if not data:
            return "No contacts found or API error.", 400

        # 2. Create CSV
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)

        return send_file(
            output,
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"smartsheet_contacts_{user_plan}.csv"
        )

    return render_template("contact.html")

@app.route("/workspaces", methods=["GET","POST"])
@login_required
@check_trial_status
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

        user_plan = session.get("user_plan", "trial")
        df = []
        if user_plan == "trial":
            data = get_trial_workspace(WORKSPACE_URL, headers)
            df = pd.DataFrame(data)
            df = df.head(50)

        elif user_plan == "pro":
            data = get_workspace(WORKSPACE_URL, headers)
            df = pd.DataFrame(data)

        elif user_plan == "enterprise":
            pass  # full data (no limit)

        # Create CSV
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return send_file(
            output,
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"smartsheet_workspace_{user_plan}.csv"
        )

    return render_template("workspace.html")

@app.route("/about", methods=["GET","POST"])
def fetch_about():
    return render_template("about.html")

@app.route("/pricing", methods=["GET","POST"])
def fetch_pricing():
    return render_template("pricing.html")

@app.route("/select-plan", methods=["POST"])
def select_plan():
    selected_plan = request.form.get("plan", "trial")

    # store plan in session
    session["user_plan"] = selected_plan

    return redirect("/register")

# Admin's view
@app.route("/admin/users")
@login_required
def admin_user_list():
    admin_email = "admin@sheetops.com"
    if session.get("user_email") != admin_email:
        flash("Access Denied", "danger")
        return redirect("/menu")

    db = SessionLocal()

    # 1. Fetch data for the table
    results = db.query(User, Subscription).join(
        Subscription, User.id == Subscription.user_id
    ).all()

    # 2. Get data for the Line Graph (Counts per Date)
    # This groups users by date and counts them
    graph_query = db.query(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('count')
    ).group_by(func.date(User.created_at)).order_by(func.date(User.created_at)).all()

    # Prepare labels (dates) and values (counts) for Chart.js
    chart_labels = [str(row.date) for row in graph_query]
    chart_values = [row.count for row in graph_query]

    total_users = len(results)
    db.close()

    return render_template("admin_users.html",
                           results=results,
                           total_users=total_users,
                           chart_labels=chart_labels,
                           chart_values=chart_values)


# --- ADMIN UPDATE PLAN ---
@app.route("/admin/update-plan/<int:user_id>", methods=["POST"])
@login_required
def admin_update_plan(user_id):
    if session.get("user_email") != "your-email@example.com":
        return "Unauthorized", 403

    new_plan = request.form.get("new_plan")
    db = SessionLocal()

    sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    if sub:
        sub.plan_type = new_plan
        db.commit()
        flash(f"User {user_id} updated to {new_plan}", "info")

    db.close()
    return redirect("/admin/users")


# --- ADMIN DELETE USER ---
@app.route("/admin/delete-user/<int:user_id>", methods=["POST"])
@login_required
def admin_delete_user(user_id):
    if session.get("user_email") != "your-email@example.com":
        return "Unauthorized", 403

    db = SessionLocal()
    # 1. Delete subscription first (foreign key requirement)
    db.query(Subscription).filter(Subscription.user_id == user_id).delete()
    # 2. Delete user
    db.query(User).filter(User.id == user_id).delete()

    db.commit()
    db.close()

    flash("User deleted successfully", "danger")
    return redirect("/admin/users")


@app.route("/admin/export-users")
@login_required
def admin_export_users():
    # 1. Security Check
    admin_email = "nitish.pkv@gmail.com"
    if session.get("user_email") != admin_email:
        return "Unauthorized", 403

    db = SessionLocal()

    # 2. Get the data (Join User and Subscription)
    results = db.query(User, Subscription).join(
        Subscription, User.id == Subscription.user_id
    ).all()

    db.close()

    # 3. Format data for CSV
    data = []
    for user, sub in results:
        data.append({
            "User ID": user.id,
            "Email": user.email,
            "Plan Type": sub.plan_type.upper(),
            "Last Login": user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never',
            "Created At": user.created_at.strftime('%Y-%m-%d') if user.created_at else 'N/A'
        })

    # 4. Create CSV using Pandas
    df = pd.DataFrame(data)
    output = BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)

    return send_file(
        output,
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"SheetOps_User_Report_{datetime.now().strftime('%Y%m%d')}.csv"
    )

@app.route("/usage")
@login_required
def user_dashboard():
    user_id = session.get("user_id")
    db = SessionLocal()

    # --- 1. METRIC WIDGETS (KPIs) ---

    # Total API calls this month
    today = date.today()
    start_of_month = date(today.year, today.month, 1)

    total_usage_month = db.query(func.count(UsageLog.id)).filter(
        UsageLog.user_id == user_id,
        func.date(UsageLog.timestamp) >= start_of_month
    ).scalar() or 0

    # Total API calls of all time
    total_usage_all_time = db.query(func.count(UsageLog.id)).filter(
        UsageLog.user_id == user_id
    ).scalar() or 0

    # --- 2. SUBSCRIPTION STATUS ---

    days_left = None
    subscription = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    if subscription and subscription.plan_type == 'trial' and subscription.trial_end:
        # Make the database time "aware" to prevent timezone errors
        trial_end_aware = subscription.trial_end.replace(tzinfo=timezone.utc)
        time_remaining = trial_end_aware - datetime.now(timezone.utc)
        # We use max(0, ...) to avoid showing negative days
        days_left = max(0, time_remaining.days)

    # 3. Data for the Area Chart (Usage count per day)
    graph_data = db.query(
        func.date(UsageLog.timestamp).label('date'),
        func.count(UsageLog.id).label('count')
    ).filter(UsageLog.user_id == user_id).group_by(func.date(UsageLog.timestamp)).all()

    labels = [str(row.date) for row in graph_data]
    values = [row.count for row in graph_data]

    # 2. Data for the table (Recent API Events)
    recent_events = db.query(UsageLog).filter(UsageLog.user_id == user_id).order_by(UsageLog.timestamp.desc()).limit(10).all()

    db.close()
    return render_template("usage.html",
                           labels=labels,
                           values=values,
                           events=recent_events,
                           total_usage_month=total_usage_month,
                           total_usage_all_time=total_usage_all_time,
                           current_plan=session.get('user_plan', 'Trial'),
                           days_left=days_left)


# In Main.py

@app.route("/upgrade-plan", methods=["POST"])
@login_required
def upgrade_plan():
    new_plan = request.form.get("plan")
    user_id = session.get("user_id")

    # Ensure plan is a valid option
    if new_plan not in ['pro', 'enterprise']:
        flash("Invalid plan selected.", "danger")
        return redirect(url_for('fetch_pricing'))

    db = SessionLocal()
    sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()

    if sub:
        # Update their plan
        sub.plan_type = new_plan
        sub.is_trial_active = False  # Ensure trial is marked as off
        db.commit()

        # IMPORTANT: Update the session to reflect the new plan
        session['user_plan'] = new_plan

        flash(f"Successfully upgraded to the {new_plan.title()} plan! Welcome.", "success")
        db.close()
        return redirect("/menu")

    db.close()
    flash("Could not find your subscription. Please contact support.", "danger")
    return redirect(url_for('fetch_pricing'))

if __name__ == "__main__":
    app.run(debug=True)