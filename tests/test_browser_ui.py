import os
import sys
import time

def run_browser_tests():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright is not installed. Skipping browser tests.")
        return

    print("=== Starting Browser UI Testing ===")
    artifacts_dir = os.path.join(
        "/home/c795990/.gemini/antigravity-cli/brain/27767fa8-95ab-4d2e-8554-61f06f450db0"
    )
    os.makedirs(artifacts_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 1000})
        page = context.new_page()

        # 1. Navigate to Web UI
        print("[1] Navigating to http://localhost:5000/ ...")
        response = page.goto("http://localhost:5000/", wait_until="networkidle")
        assert response.status == 200, f"Expected status 200, got {response.status}"
        assert "Demo UI" in page.title(), f"Page title mismatch: {page.title()}"
        print("  ✓ Page loaded successfully with title 'Demo UI'.")

        # Wait for JSONEditor to be ready
        page.wait_for_selector('input[name*="username"]', timeout=5000)
        time.sleep(1)

        # 2. Check Visual Elements
        print("[2] Checking UI layout and components...")
        assert page.is_visible("#navbar"), "Navbar missing"
        assert page.is_visible("#preset-card"), "Presets card missing"
        assert page.is_visible("#config-form-content"), "Config editor missing"
        assert page.is_visible("#json-code"), "JSON preview missing"
        assert page.is_visible("#terminal-output"), "Terminal output missing"
        assert page.is_visible("#admin-login-btn"), "Admin login button missing"
        print("  ✓ All key UI sections (Navbar, Presets, Form Editor, JSON Pane, Terminal) are visible.")

        # Take screenshot of default Guest mode
        guest_screenshot_path = os.path.join(artifacts_dir, "guest_view.png")
        page.screenshot(path=guest_screenshot_path, full_page=True)
        print(f"  ✓ Saved guest view screenshot to {guest_screenshot_path}")

        # 3. Check that Readonly Fields are disabled in Guest Mode
        print("[3] Checking read-only fields in Guest Mode...")
        # System ID input should be readonly / disabled
        system_id_input = page.locator('input[name*="system_id"]')
        assert system_id_input.count() > 0, "System ID input not found"
        is_disabled = system_id_input.first.is_disabled() or bool(system_id_input.first.get_attribute("readonly"))
        assert is_disabled, "System ID field should be read-only for guests"
        print("  ✓ System ID and system settings are strictly read-only for guests.")

        # 4. Test Preset Switching
        print("[4] Testing Preset Selection...")
        page.select_option("#preset-select", "Christmas Special")
        page.click("#apply-preset-btn")
        time.sleep(1)

        # Check flash message
        flash_alert = page.locator("#flash-messages-content .alert")
        assert flash_alert.count() > 0, "Flash message expected after applying preset"
        assert "Christmas Special" in flash_alert.first.inner_text()
        print(f"  ✓ Preset applied successfully: {flash_alert.first.inner_text().strip()}")

        # 5. Test Admin Login Flow
        print("[5] Testing Admin Login Modal & Password Verification...")
        page.click("#admin-login-btn")
        page.wait_for_selector("#adminLoginModal.show", timeout=3000)
        assert page.is_visible("#adminLoginModal"), "Admin modal did not open"

        # Wrong password first
        page.fill("#admin-password-input", "wrongpass")
        page.click("#admin-login-submit-btn")
        time.sleep(0.5)
        error_box = page.locator("#admin-login-error")
        assert error_box.is_visible() and "Invalid" in error_box.inner_text(), "Expected login error message"
        print("  ✓ Incorrect password rejected with error alert.")

        # Correct password
        page.fill("#admin-password-input", "admin")
        page.click("#admin-login-submit-btn")
        time.sleep(1.5)

        # Verify Admin Mode UI
        assert page.is_visible("#admin-badge"), "Admin badge should be visible"
        assert page.is_visible("#admin-logout-btn"), "Admin logout button should be visible"
        print("  ✓ Logged in as Admin. 'Admin Mode' badge is active.")

        # 6. Verify Read-Only Fields are Now Editable
        print("[6] Checking that read-only fields are unlocked in Admin Mode...")
        system_id_input = page.locator('input[name*="system_id"]').first
        is_editable = not system_id_input.is_disabled() and not system_id_input.get_attribute("readonly")
        assert is_editable, "System ID field should be editable for admin"
        print("  ✓ Read-only fields unlocked and editable.")

        # Modify the unlocked field
        system_id_input.fill("SYS-ADMIN-OVERRIDE-2026")
        time.sleep(0.5)

        # Take screenshot of Admin mode
        admin_screenshot_path = os.path.join(artifacts_dir, "admin_view.png")
        page.screenshot(path=admin_screenshot_path, full_page=True)
        print(f"  ✓ Saved admin view screenshot to {admin_screenshot_path}")

        # 7. Test Save Action
        print("[7] Testing Save functionality in Admin Mode...")
        page.locator("#config-form-actions .save-action").click()
        time.sleep(1)
        save_alert = page.locator("#flash-messages-content .alert-success")
        assert save_alert.count() > 0, "Expected success flash message on save"
        print("  ✓ Configuration saved successfully.")

        # 8. Test Main Program Launch & Terminal Streaming
        print("[8] Testing Program Launch & Terminal Output Streaming...")
        page.locator("#terminal-output-control-group .launch-action").click()
        time.sleep(3)

        terminal_text = page.locator("#terminal-output-display").input_value()
        assert len(terminal_text) > 0, "Terminal output should not be empty"
        assert "Verifying user credential" in terminal_text or "Reservation" in terminal_text, "Expected execution logs in terminal"
        print("  ✓ Main program executed and logs streamed to terminal output:")
        for line in terminal_text.strip().split("\n")[:8]:
            print(f"     | {line}")

        # 9. Test Admin Logout
        print("[9] Testing Admin Logout...")
        page.click("#admin-logout-btn")
        time.sleep(1)
        assert page.is_visible("#admin-login-btn"), "Admin login button should return after logout"
        assert not page.is_visible("#admin-badge"), "Admin badge should disappear after logout"
        print("  ✓ Successfully logged out from Admin Mode.")

        browser.close()
        print("\n🎉 ALL BROWSER INTERACTION & STYLE TESTS PASSED SUCCESSFULLY! 🎉")

if __name__ == "__main__":
    run_browser_tests()
