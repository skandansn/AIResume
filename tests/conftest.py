import sys
from pathlib import Path

# the app is laid out as a top level package directory, the same way the server
# and the Dockerfile run it
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "app"))

FIXTURES = Path(__file__).resolve().parent / "fixtures"
