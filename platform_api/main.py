import sys
import os

# Add the current directory (platform_api) to sys.path so that 'app' can be imported as a module
# This allows 'from app.main import app' to work and resolves internal imports like 'from app.core...'
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import the real FastAPI app
from app.main import app
