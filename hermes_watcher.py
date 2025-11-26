import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from pathlib import Path

# ==============================
# CONFIGURATION
# ==============================

# If HERMES_URL is not set as an env var, use this default:
URL = os.environ.get(
    "HERMES_URL",
    "https://www.hermes.com/us/en/category/women/bags-and-small-leather-goods/bags-and-clutches/#|",
)

# Snapshot file (stored in the repo)
SNAPSHOT_FILE = Path(__file__).parent / "snapshot.txt"

# Email settings are read from environment variables
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SMTP_USER = os.environ.get("SMTP_USER")  # e.g. your Gmail
SMTP_PASS = os.environ.get("SMTP_PASS")  # Gmail app password
EMAIL_TO = os.environ.get("EMAIL_TO", SMTP_USER)

EMAIL_ENABLED = bool(SMTP_USER and SMTP_PASS and EMAIL_TO)


# ==============================
# EMAIL NOTIFICATION
# ==============================

def send_email_notification(subject: str, body: str):
    """Send an email notification using SMTP and environment variables."""
    if not EMAIL_ENABLED:
        print("Email not enabled (missing SMTP_USER / SMTP_PASS / EMAIL_TO).")
        return

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = EMAIL_TO

    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e}")


# ==============================
# CORE LOGIC
# ==============================

def fetch_page_html(url: str) -> str:
    """Fetch HTML content for the given URL."""
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

def extract_product_list(html: str) -> str:
    """
    Extract a stable list of product names from the Hermès bags page.
    We sort and deduplicate so small ordering changes don't explode diffs.
    """
    soup = BeautifulSoup(html, "html.parser")

    product_links = soup.select("a[href*='/us/en/product/']")

    names = []
    for a in product_links:
        text = a.get_text(strip=True)
        if text:
            names.append(text)

    unique_names = sorted(set(names))

    if not unique_names:
        return "NO_PRODUCTS_FOUND"

    return "\n".join(unique_names)


def load_previous_snapshot() -> str:
    """Load the previous snapshot from snapshot.txt, or empty string if none."""
    if SNAPSHOT_FILE.exists():
        return SNAPSHOT_FILE.read_text(encoding="utf-8")
    return ""


def save_snapshot(content: str):
    """Save the current snapshot to snapshot.txt."""
    SNAPSHOT_FILE.write_text(content, encoding="utf-8")


def main():
    print(f"Checking Hermès page: {URL}")

    previous = load_previous_snapshot()
    html = fetch_page_html(URL)
    current = extract_product_list(html)

    if not previous:
        # First run: save and don't email
        print("No previous snapshot found. Saving current snapshot and exiting.")
        save_snapshot(current)
        return

    if current == previous:
        print("No change in product list.")
        return

    print("🔥 CHANGE DETECTED in Hermès product list.")
    print("Saving new snapshot and sending email...")

    # Prepare email body
    body = (
        f"Hermès bags page has changed.\n\nURL: {URL}\n\n"
        f"Previous product list:\n{previous}\n\n"
        f"New product list:\n{current}\n"
    )

    send_email_notification("Hermès bags page changed!", body)
    save_snapshot(current)


if __name__ == "__main__":
    main()
