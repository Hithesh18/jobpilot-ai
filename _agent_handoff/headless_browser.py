r"""
100% Silent Background Headless Browser Helper (Shared by Claude Code & Gemini Antigravity)
- Uses Chrome in `headless=True` mode with an isolated profile at `_agent_handoff/headless_profile`.
- NEVER opens visible windows, NEVER steals focus, and NEVER touches the user's main Chrome browser.
- Optional one-time login (run manually by user ONLY if they want portal cookies saved for headless runs):
    python _agent_handoff/headless_browser.py --login-once
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HANDOFF = Path(__file__).resolve().parent
sys.path.insert(0, str(HANDOFF))
from profile_loader import load_profile  # noqa: E402

PROF = load_profile()
CAND = PROF.get("candidate", {})

PROFILE_DIR = HANDOFF / "headless_profile"
FIRST_NAME = CAND.get("first_name", "Alex")
LAST_NAME = CAND.get("last_name", "Morgan")
FULL_NAME = CAND.get("full_name", "Alex Morgan")


def launch_silent_context(playwright_instance):
    """Launch 100% invisible headless Chrome context (0 windows, 0 focus stealing)."""
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    return playwright_instance.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR),
        channel="chrome",
        headless=True,
        viewport={"width": 1440, "height": 900},
        locale="en-GB",
        args=["--disable-blink-features=AutomationControlled", "--mute-audio"],
    )


def clear_and_set_verified(locator, expected_value: str) -> None:
    """Prevents duplicate-name autofill bugs (e.g. 'AlexAlex') on Greenhouse/Lever/Ashby/Personio."""
    locator.click()
    locator.press("Control+A")
    locator.press("Backspace")
    locator.fill("")
    locator.fill(expected_value)
    actual = locator.input_value().strip()
    if actual != expected_value:
        locator.evaluate(
            """(el, val) => {
                const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                setter.call(el, val);
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
            }""",
            expected_value,
        )
    final_val = locator.input_value().strip()
    assert final_val == expected_value, f"ABORT SUBMIT: Field value mismatch! Got '{final_val}', expected '{expected_value}'"


def login_once_interactive() -> None:
    """Run ONLY manually by user once if they wish to save portal session cookies for silent headless runs."""
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Opening one-time login window for isolated profile: {PROFILE_DIR}")
    print("Log into desired portals if needed, then close the browser window. All future agent runs stay 100% headless!")
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            channel="chrome",
            headless=False,
            viewport={"width": 1280, "height": 850},
        )
        pg = ctx.pages[0] if ctx.pages else ctx.new_page()
        pg.goto("https://www.stepstone.de")
        try:
            pg.wait_for_event("close", timeout=300_000)
        except Exception:
            pass
        ctx.close()
    print("Cookies saved! Agents can now run 100% invisibly in background (`headless=True`).")


if __name__ == "__main__":
    if "--login-once" in sys.argv:
        login_once_interactive()
    else:
        with sync_playwright() as p:
            ctx = launch_silent_context(p)
            page = ctx.new_page()
            page.goto("https://example.com", timeout=15000)
            print("SILENT_HEADLESS_READY:", page.title())
            ctx.close()
