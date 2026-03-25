from sql_queries import supabase

def check_all():
    print("--- System Settings ---")
    try:
        res = supabase.table("system_settings").select("*").execute()
        for row in res.data:
            print(f"Key: {row['key']} | Value: {row['value']}")
            if "Tech" in row['value'] or "Africa" in row['value'] or "Afri" in row['value']:
                print(">>> FOUND POTENTIAL BRANDING ISSUE IN SETTINGS!")
    except Exception as e:
        print(f"Error reading system_settings: {e}")

    print("\n--- Employee Data (Recent) ---")
    try:
        res = supabase.table("employees").select("id, name, username, email, role").limit(10).execute()
        for row in res.data:
            print(f"Name: {row['name']} | Email: {row['email']} | User: {row['username']}")
            if "Tech" in row['name'] or "Africa" in row['name']:
                 print(">>> FOUND POTENTIAL BRANDING ISSUE IN EMPLOYEE NAME!")
    except Exception as e:
        print(f"Error reading employees: {e}")

if __name__ == "__main__":
    check_all()
