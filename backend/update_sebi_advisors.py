import os
import requests
import pandas as pd
from datetime import datetime, timedelta

SEBI_ADVISOR_CSV_URL = "https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFpi=yes&intmId=14"  # Example, update with actual CSV link if available
LOCAL_CSV = "sebi_advisors.csv"
LAST_UPDATE_FILE = "sebi_advisors_last_update.txt"

# Check if update is needed (default: 7 days)
def needs_update():
    if not os.path.exists(LOCAL_CSV) or not os.path.exists(LAST_UPDATE_FILE):
        return True
    with open(LAST_UPDATE_FILE, 'r') as f:
        last_update = datetime.strptime(f.read().strip(), "%Y-%m-%d")
    return datetime.now() - last_update > timedelta(days=7)

# Download and save the latest CSV
def update_advisor_csv():
    print("Downloading latest SEBI advisor list...")
    r = requests.get(SEBI_ADVISOR_CSV_URL)
    if r.status_code == 200:
        with open(LOCAL_CSV, 'wb') as f:
            f.write(r.content)
        with open(LAST_UPDATE_FILE, 'w') as f:
            f.write(datetime.now().strftime("%Y-%m-%d"))
        print("SEBI advisor list updated.")
    else:
        print(f"Failed to download advisor list: {r.status_code}")

# Load advisors as DataFrame
def load_advisors():
    if needs_update():
        update_advisor_csv()
    return pd.read_csv(LOCAL_CSV)

if __name__ == "__main__":
    df = load_advisors()
    print(df.head())
    print(f"Loaded {len(df)} advisors.")
