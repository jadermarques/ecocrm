
import sys
import os

# Mimic container path setup
current_dir = os.path.abspath("platform_api")
sys.path.insert(0, current_dir)

try:
    print("Attempting to import app.main...")
    from app.main import app
    print("SUCCESS: app.main imported successfully.")
except Exception as e:
    print(f"FAILURE: {e}")
    import traceback
    traceback.print_exc()
