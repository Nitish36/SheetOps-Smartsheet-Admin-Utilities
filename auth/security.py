"""
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


"""
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import session, redirect, flash, url_for
from database import SessionLocal
from datetime import datetime, timezone
from models.subscription import Subscription

def hash_password(password: str) -> str:
    return generate_password_hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, password)

def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return view_func(*args, **kwargs)
    return wrapper


# In auth/security.py

def check_trial_status(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_plan") == "trial":
            db = SessionLocal()
            sub = db.query(Subscription).filter(Subscription.user_id == session['user_id']).first()

            if sub and sub.trial_end:
                # --- THIS IS THE FIX ---
                # 1. Get the current time (which is AWARE of its timezone)
                current_time_utc = datetime.now(timezone.utc)

                # 2. Get the database time and MAKE IT AWARE of its timezone
                trial_end_utc = sub.trial_end.replace(tzinfo=timezone.utc)
                # -----------------------

                # 3. Now compare the two AWARE datetimes
                if current_time_utc > trial_end_utc:
                    if sub.is_trial_active:
                        sub.is_trial_active = False
                        db.commit()

                    flash("Your trial has expired. Please upgrade your plan to continue.", "warning")
                    db.close()
                    return redirect(url_for('fetch_pricing'))

            db.close()
        return f(*args, **kwargs)
    return decorated_function
