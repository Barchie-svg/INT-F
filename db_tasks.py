
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
