"""
sql_queries.py
==============
All Supabase database query helpers for the Employee Intrusion Detection System.
Import this module in app.py instead of writing inline queries.
"""

from database import supabase
from datetime import datetime
import uuid


# ─────────────────────────────────────────────
#  Profile Queries
# ─────────────────────────────────────────────

def get_employee_by_username(username: str):
    """Return a single profile dict or None."""
    res = supabase.table("employees").select("*").eq("username", username).execute()
    return res.data[0] if res.data else None


def get_employee_by_email(email: str):
    """Return a single profile dict matched by email, or None."""
    res = supabase.table("employees").select("*").eq("email", email).execute()
    return res.data[0] if res.data else None


def get_user_by_email_or_username(identifier: str):
    """
    Look up a user (employee or admin) by either username, email, or employee number.
    Tries username first, then email, then employee_number.
    Returns a single profile dict or None.
    """
    # Try username match first
    res = supabase.table("employees").select("*").eq("username", identifier).execute()
    if res.data:
        return res.data[0]
    
    # Try email match
    res = supabase.table("employees").select("*").eq("email", identifier).execute()
    if res.data:
        return res.data[0]
    
    # Try employee_number match
    res = supabase.table("employees").select("*").eq("employee_number", identifier).execute()
    return res.data[0] if res.data else None


def get_employee_by_id(user_id: str):
    """Return a single profile dict or None."""
    res = supabase.table("employees").select("*").eq("id", user_id).execute()
    return res.data[0] if res.data else None


def get_all_employees():
    """Return list of all employee profile dicts."""
    res = supabase.table("employees").select("*").eq("role", "Employee").execute()
    return res.data or []


def employee_username_exists(username: str) -> bool:
    res = supabase.table("employees").select("id").eq("username", username).execute()
    return bool(res.data)


def employee_number_exists(employee_number: str) -> bool:
    res = supabase.table("employees").select("id").eq("employee_number", employee_number).execute()
    return bool(res.data)


def update_failed_attempts(user_id: str, attempts: int):
    supabase.table("employees").update({"failed_attempts": attempts}).eq("id", user_id).execute()


def reset_failed_attempts(user_id: str, ip_address: str = None):
    """
    Reset failed attempts to 0 and update last login.
    Uses a gradual fallback if optional columns are missing.
    """
    now = datetime.utcnow().isoformat()
    # 1. Try updating all fields
    try:
        supabase.table("employees").update({
            "failed_attempts": 0,
            "last_login": now,
            "last_ip_address": ip_address
        }).eq("id", user_id).execute()
        return
    except Exception:
        pass

    # 2. Try updating without ip_address
    try:
        supabase.table("employees").update({
            "failed_attempts": 0,
            "last_login": now
        }).eq("id", user_id).execute()
        return
    except Exception:
        pass

    # 3. Last resort: only reset failed_attempts
    try:
        supabase.table("employees").update({
            "failed_attempts": 0
        }).eq("id", user_id).execute()
    except Exception as e:
        print(f"[DB ERROR] Critical failure in reset_failed_attempts: {e}")


def lock_employee(user_id: str):
    supabase.table("employees").update({"status": "Locked"}).eq("id", user_id).execute()


def unlock_employee(user_id: str):
    supabase.table("employees").update({
        "status": "Active",
        "failed_attempts": 0,
    }).eq("id", user_id).execute()


def get_employee_username_by_id(user_id: str):
    """Return just the username string, or None."""
    res = supabase.table("employees").select("username").eq("id", user_id).execute()
    return res.data[0]["username"] if res.data else None


def create_employee(name, email, employee_number, username, password_hash, role="Employee"):
    """
    Create a new employee profile.
    Note: In a real Supabase setup, you'd usually create an auth user first.
    For this 'unified login' demo, we store the hash in the profile.
    """
    # Generate a random UUID for the profile if not using Supabase Auth
    # Alternatively, you could use gen_random_uuid() in SQL
    user_id = str(uuid.uuid4())
    data = {
        "id": user_id,
        "name": name,
        "email": email,
        "employee_number": employee_number,
        "username": username,
        "password": password_hash,
        "role": role,
        "status": "Active",
        "failed_attempts": 0,
        "created_at": datetime.utcnow().isoformat()
    }
    supabase.table("employees").insert(data).execute()


def update_employee_password(user_id: str, hashed_password: str):
    """
    Update an employee's password.
    """
    supabase.table("employees").update({"password": hashed_password}).eq("id", user_id).execute()


def update_employee_emergency_email(user_id: str, email: str):
    """
    Update an employee's emergency/recovery email.
    """
    supabase.table("employees").update({"emergency_email": email}).eq("id", user_id).execute()


def delete_employee(user_id: str):
    supabase.table("employees").delete().eq("id", user_id).execute()


def get_employee_by_email_only(email: str):
    """Return a single employee dict matched by email only, or None."""
    res = supabase.table("employees").select("*").eq("email", email).execute()
    return res.data[0] if res.data else None


# ─────────────────────────────────────────────
#  Password Reset Token Queries
# ─────────────────────────────────────────────

def create_password_reset_token(user_id: str, token: str, expires_at: str):
    """Store a one-time password reset token."""
    # Delete any existing tokens for this user first
    try:
        supabase.table("password_reset_tokens").delete().eq("user_id", user_id).execute()
    except Exception:
        pass
    data = {
        "user_id": user_id,
        "token": token,
        "expires_at": expires_at,
    }
    supabase.table("password_reset_tokens").insert(data).execute()


def get_password_reset_token(token: str):
    """Return the token record if it exists and has not expired, or None."""
    try:
        res = (supabase.table("password_reset_tokens")
               .select("*")
               .eq("token", token)
               .execute())
        return res.data[0] if res.data else None
    except Exception:
        return None


def delete_password_reset_token(token: str):
    """Delete a token after use or expiry."""
    try:
        supabase.table("password_reset_tokens").delete().eq("token", token).execute()
    except Exception:
        pass


# ─────────────────────────────────────────────
#  Admin Queries
# ─────────────────────────────────────────────

def get_admin_by_username(username: str):
    """Return a single admin profile dict or None."""
    res = supabase.table("employees").select("*").eq("username", username).eq("role", "Admin").execute()
    return res.data[0] if res.data else None


def admin_exists() -> bool:
    res = supabase.table("employees").select("id").eq("role", "Admin").limit(1).execute()
    return bool(res.data)


def create_admin(username, password_hash):
    """Create initial system admin."""
    user_id = str(uuid.uuid4())
    data = {
        "id": user_id,
        "username": username,
        "email": f"{username}@system.local",
        "password": password_hash,
        "role": "Admin",
        "status": "Active",
        "created_at": datetime.utcnow().isoformat()
    }
    supabase.table("employees").insert(data).execute()


# ─────────────────────────────────────────────
#  Intrusion Log Queries
# ─────────────────────────────────────────────

def log_intrusion(username: str, reason: str, ip_address: str = None, device_info: str = None):
    data = {"username": username, "reason": reason}
    if ip_address:
        data["ip_address"] = ip_address
    if device_info:
        data["device_info"] = device_info
    
    try:
        supabase.table("intrusion_logs").insert(data).execute()
    except Exception:
        fallback_data = {"username": username, "reason": reason}
        supabase.table("intrusion_logs").insert(fallback_data).execute()

def get_recent_intrusion_logs(limit: int = 50):
    try:
        res = supabase.table("intrusion_logs").select("*").order("timestamp", desc=True).limit(limit).execute()
        return res.data or []
    except Exception:
        return []

def log_audit_action(admin_username: str, action: str, target: str, ip_address: str = None):
    data = {
        "admin_username": admin_username,
        "action": action,
        "target": target,
        "ip_address": ip_address
    }
    try:
        supabase.table("audit_logs").insert(data).execute()
    except Exception:
        fallback_data = {
            "admin_username": admin_username,
            "action": action,
            "target": target
        }
        supabase.table("audit_logs").insert(fallback_data).execute()

def get_recent_audit_logs(limit: int = 50):
    try:
        res = supabase.table("audit_logs").select("*").order("timestamp", desc=True).limit(limit).execute()
        return res.data or []
    except Exception:
        return []


# ─────────────────────────────────────────────
#  System Settings Queries
# ─────────────────────────────────────────────

def get_setting(key: str, default: str = "") -> str:
    """Get a configuration value from the system_settings table."""
    try:
        res = supabase.table("system_settings").select("value").eq("key", key).execute()
        if res.data:
            return res.data[0]["value"]
    except Exception:
        pass
    return default


def update_setting(key: str, value: str):
    """Update or insert a setting in the database."""
    # Check if exists
    res = supabase.table("system_settings").select("id").eq("key", key).execute()
    if res.data:
        supabase.table("system_settings").update({"value": value}).eq("key", key).execute()
    else:
        supabase.table("system_settings").insert({"key": key, "value": value}).execute()


def get_system_settings() -> dict:
    """Return an object of system settings in a single fast query."""
    defaults = {
        "admin_email": "ivybarchebo916@gmail.com",
        "sender_email": "ivybarchebo916@gmail.com",
        "sender_password": "zyufnycxoymgthit",
    }
    try:
        res = supabase.table("system_settings").select("key, value").execute()
        if res.data:
            for row in res.data:
                k = row.get("key")
                v = row.get("value")
                if k and v is not None:
                    defaults[k] = v
    except Exception as e:
        print(f"[WARN] Failed to fetch system_settings in batch: {e}")
    return defaults


def update_system_settings(admin_email: str, sender_email: str, sender_password: str = None):
    """Update multiple system settings at once."""
    if admin_email: update_setting("admin_email", admin_email)
    if sender_email: update_setting("sender_email", sender_email)
    if sender_password is not None: update_setting("sender_password", sender_password)


# --- New Tasks Functions ---
from database import supabase
from datetime import datetime, timezone

def get_employee_tasks(user_id):
    """Fetch all tasks for a given employee, ordered by incomplete first then creation date."""
    try:
        res = supabase.table("employee_tasks").select("*").eq("user_id", user_id).order("is_completed").order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        print(f"Error fetching tasks: {e}")
        return []

def add_employee_task(user_id, title, priority="Medium"):
    try:
        data = {
            "user_id": user_id,
            "title": title,
            "priority": priority,
            "is_completed": False
        }
        res = supabase.table("employee_tasks").insert(data).execute()
        return res.data
    except Exception as e:
        print(f"Error adding task: {e}")
        return None

def update_task_status(task_id, user_id, is_completed):
    try:
        res = supabase.table("employee_tasks").update({"is_completed": is_completed}).eq("id", task_id).eq("user_id", user_id).execute()

        return res.data
    except Exception as e:
        print(f"Error updating task: {e}")
        return None

def delete_employee_task(task_id, user_id):
    try:
        res = supabase.table("employee_tasks").delete().eq("id", task_id).eq("user_id", user_id).execute()
        return res.data
    except Exception as e:
        print(f"Error deleting task: {e}")
        return None

# ─────────────────────────────────────────────
#  Internal Messaging Functions
# ─────────────────────────────────────────────

def get_employee_messages(user1_id: str, user2_id: str):
    """Fetch chat history between two users, ordered by time."""
    try:
        from database import supabase
        try:
            res = supabase.table("employee_messages").select(
                "id, sender_id, receiver_id, message_text, is_read, created_at, sender:employees!sender_id(name, username), receiver:employees!receiver_id(name, username)"
            ).or_(
                f"and(sender_id.eq.{user1_id},receiver_id.eq.{user2_id}),and(sender_id.eq.{user2_id},receiver_id.eq.{user1_id})"
            ).order("created_at").execute()
            return res.data or []
        except Exception:
            res = supabase.table("employee_messages").select(
                "id, sender_id, receiver_id, message_text, is_read, created_at"
            ).or_(
                f"and(sender_id.eq.{user1_id},receiver_id.eq.{user2_id}),and(sender_id.eq.{user2_id},receiver_id.eq.{user1_id})"
            ).order("created_at").execute()
            return res.data or []
    except Exception as e:
        print(f"Error fetching messages: {e}")
        return []


def send_employee_message(sender_id: str, receiver_id: str, message_text: str):
    """Send a new message to another employee."""
    try:
        from database import supabase
        data = {
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "message_text": message_text.strip(),
            "is_read": False
        }
        res = supabase.table("employee_messages").insert(data).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        print(f"Error sending message: {e}")
        return None


def mark_messages_as_read(sender_id: str, receiver_id: str):
    """Mark all unread messages from a sender to the current user (receiver) as read."""
    try:
        from database import supabase
        supabase.table("employee_messages").update({"is_read": True}).eq("sender_id", sender_id).eq("receiver_id", receiver_id).execute()
    except Exception as e:
        print(f"Error marking messages read: {e}")
