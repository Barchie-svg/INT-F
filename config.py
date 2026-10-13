import os

# ── Supabase ──────────────────────────────────────────────
SUPABASE_URL = os.environ.get(
    "SUPABASE_URL",
    "https://uzhudokuovsjqlwixcpz.supabase.co"
)
SUPABASE_KEY = os.environ.get(
    "SUPABASE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV6aHVkb2t1b3ZzanFsd2l4Y3B6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MTg3NTU5NywiZXhwIjoyMTA3NDUxNTk3fQ.WRGs0QBo_8npkvIrvjo9Rk1GGAPDEbyPuo5vbm97bS4"
)

# ── Flask ──────────────────────────────────────────────────
SECRET_KEY = os.environ.get("SECRET_KEY", "supersecretkey-ids-2026")

# Hardcoded emails have been removed. System administrators can update 
# these dynamically via the database ('system_settings' table) 
# and the Admin Dashboard.