import subprocess
import sys
import venv
from pathlib import Path

# Find root of project folder
root = Path(__file__).parent

# Set root by platform type
if sys.platform == "win32":
    vpy = root / ".venv" / "Scripts/python.exe"
else:
    vpy = root / ".venv" / "bin/python"

# Double check requirements.txt exists before downloading
if not (root / "requirements.txt").exists():
    sys.exit("requirements.txt not found")

# Check if venv exists, if not create
if not vpy.exists():
    venv.create(root / ".venv", with_pip=True)

# Runs install on requirements.txt with pip
subprocess.run([str(vpy), "-m", "pip", "install", "-r", "requirements.txt"], cwd=root, check=True)

# Checks if road data is in root and downloads from OSM if not
if not (root / "roads.graphml").exists():
    print("roads.graphml is missing. Downloading it from OpenStreetMap (this can take a few minutes)...")
    subprocess.run([str(vpy), "graph_data.py"], cwd=root, check=True)

# Runs the UI with streamlit
subprocess.run([str(vpy), "-m", "streamlit", "run", "ui.py"], cwd=root)