from flask import Blueprint, render_template, request, redirect, session, flash, url_for

from sqlalchemy.orm import Session
from database import SessionLocal
from models.user import User
from models.subscription import Subscription
from auth.security import hash_password, verify_password
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

        # 4️⃣ Create trial subscription
        subscription = Subscription(
            user_id=user.id,
            plan_type="trial",
            is_trial_active=True
        )
        db.add(subscription)
        db.commit()

        # 5️⃣ Session setup
        session["user_id"] = user.id
        session["user_email"] = user.email
        session["user_plan"] = "trial"

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
            return "Email and password are required", 400

        db: Session = SessionLocal()

        # 1️⃣ Fetch user
        user = db.query(User).filter(
            User.email == email.lower().strip()
        ).first()

        if not user:
            db.close()
            return "Invalid email or password", 401

        # 2️⃣ Verify password
        if not verify_password(password, user.password_hash):
            db.close()
            return "Invalid email or password", 401

        # 3️⃣ Fetch subscription
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id
        ).first()

        if not subscription:
            db.close()
            return "Subscription not found", 403

        # 4️⃣ Trial validation
        user_plan = subscription.plan_type

        if user_plan == "trial":
            if subscription.trial_end < datetime.now(timezone.utc):
                subscription.is_trial_active = False
                db.commit()
                db.close()
                return "Trial expired", 403

        # 5️⃣ Update last login
        user.last_login = datetime.now(timezone.utc)
        db.commit()

        # 6️⃣ Session setup
        """
        session.clear()
        session["user_id"] = user.id
        session["user_email"] = user.email
        session["user_plan"] = user_plan
        """
        db.close()

        return redirect("/menu")

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    """
    Clears the current user session and redirects to login page.
    """
    session.clear()  # removes user_id, user_email, user_plan, etc.
    flash("You have been logged out successfully.", "info")

    return redirect(url_for("auth.login"))  # redirect to login page
