from flask import Blueprint, render_template, request, redirect, session, flash, url_for

from sqlalchemy.orm import Session
from database import SessionLocal
from models.user import User
from models.subscription import Subscription
from auth.security import hash_password, verify_password, check_trial_status
from datetime import datetime, timezone

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # 1️⃣ Validate input FIRST
        if not email or not password:
            return "Email and password are required", 400

        email = email.lower().strip()

        db: Session = SessionLocal()

        # 2️⃣ Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            db.close()
            return "User already exists", 400

        # 3️⃣ Create user
        user = User(
            email=email,
            password_hash=hash_password(password)
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        selected_plan = session.get("user_plan", "trial")
        # 4️⃣ Create trial subscription
        subscription = Subscription(
            user_id=user.id,
            plan_type=selected_plan,
            is_trial_active=True
        )
        db.add(subscription)
        db.commit()

        # 5️⃣ Session setup
        session["user_id"] = user.id
        session["user_email"] = user.email
        session["user_plan"] = selected_plan
        flash("Account created successfully! Welcome to SheetOps.", "success")
        db.close()

        # 6️⃣ Redirect into app
        return redirect("/menu")

    return render_template("register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            flash("Email and password are required", "danger")

        db: Session = SessionLocal()

        # 1️⃣ Fetch user
        user = db.query(User).filter(
            User.email == email.lower().strip()
        ).first()

        if not user or not verify_password(password, user.password_hash):
            db.close()
            flash("Invalid email or password", "danger")
            return redirect(url_for("auth.login"))


        # 3️⃣ Fetch subscription
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id
        ).first()

        user.last_login = datetime.now(timezone.utc)
        db.commit()

        # Session setup
        session.clear()
        session["user_id"] = user.id
        session["user_email"] = user.email
        session["user_plan"] = subscription.plan_type if subscription else 'trial'

        db.close()

        flash("Logged in successfully!", "info")
        return redirect("/menu")  # <-- Now it redirects to /menu

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    """
    Clears the current user session and redirects to login page.
    """
    session.clear()  # removes user_id, user_email, user_plan, etc.
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("auth.login"))  # redirect to login page