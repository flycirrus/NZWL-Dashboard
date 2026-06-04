"""Take screenshots of every NZWL Dashboard page via Playwright."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8501"
OUT = Path(__file__).parent / "screenshots"
OUT.mkdir(exist_ok=True)

PAGES = [
    ("login",            None),
    ("dashboard",        "Dashboard"),
    ("faelligkeiten",    "Faelligkeiten"),
    ("kreditor_debitor", "Kreditor-Debitor"),
    ("nicht_verknuepft", "Nicht verknüpft"),
    ("admin",            "Admin-Bereich"),
]


def wait_for_streamlit(page, timeout=8000):
    """Wait until Streamlit finishes rendering."""
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        pass
    time.sleep(2)


def login(page):
    """Log in as admin."""
    page.goto(BASE, wait_until="networkidle", timeout=15000)
    time.sleep(3)

    # Fill login form
    inputs = page.locator("input")
    inputs.nth(0).fill("admin")
    inputs.nth(1).fill("pwd")

    # Click "Einloggen"
    page.locator("button", has_text="Einloggen").click()
    wait_for_streamlit(page, 10000)
    time.sleep(3)


def navigate_to(page, page_name):
    """Click a sidebar radio button to navigate."""
    sidebar = page.locator('[data-testid="stSidebar"]')
    radio = sidebar.locator(f'label:has-text("{page_name}")')
    if radio.count() > 0:
        radio.first.click()
        wait_for_streamlit(page)
        time.sleep(2)
    else:
        print(f"  WARNING: Could not find nav item '{page_name}'")


def take_full_page_screenshot(page, name):
    """Screenshot the full page content."""
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    print(f"  Saved: {path.name}")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,
        )
        page = context.new_page()

        # 1) Login page screenshot
        print("Taking: login")
        page.goto(BASE, wait_until="networkidle", timeout=15000)
        time.sleep(4)
        take_full_page_screenshot(page, "login")

        # 2) Log in
        print("Logging in as admin...")
        login(page)

        # 3) Screenshot each page
        for slug, nav_name in PAGES:
            if nav_name is None:
                continue
            print(f"Taking: {slug}")
            navigate_to(page, nav_name)
            take_full_page_screenshot(page, slug)

        browser.close()
        print("\nDone! Screenshots in:", OUT)


if __name__ == "__main__":
    main()
