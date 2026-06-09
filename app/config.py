from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"

APP_TITLE = "HCDT Shift Assistant"
APP_DESCRIPTION = (
    "Human-centric digital twin for UAZ assembly-line workers. "
    "The platform combines digital trace, cognitive risk estimation, "
    "regulation automaton, explainable recommendations, and trust score."
)
