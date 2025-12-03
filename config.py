import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "YOUR_POLYGON_KEY")
DATA_PROVIDER = os.getenv("DATA_PROVIDER", "polygon") # Options: "polygon", "yfinance"

# Risk Free Rate (can be fetched dynamically, but hardcoded for now)
RISK_FREE_RATE = 0.045  # 4.5%

# Scanner Settings
MIN_VOLUME = 50
MIN_OI = 100
IV_LOW_THRESHOLD = 0.20
IV_HIGH_THRESHOLD = 0.80

# Output Paths
OUTPUT_DIR = "outputs"
REPORTS_DIR = os.path.join(OUTPUT_DIR, "reports")
CHARTS_DIR = os.path.join(OUTPUT_DIR, "charts")
