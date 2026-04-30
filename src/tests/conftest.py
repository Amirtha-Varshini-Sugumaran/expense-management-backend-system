import sys
from pathlib import Path

# Add "<project_root>/src" to Python path so "import core..." works in tests
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))
