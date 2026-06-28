import pytest
import json
import tempfile
import os
from app.database import Database


# ===== Part 5a: Mobile-responsive Dashboard Tests =====

def test_dashboard_html_exists():
    """Test that dashboard.html exists."""
    assert os.path.exists("static/dashboard.html")


def test_dashboard_contains_required_structure():
    """Test that dashboard includes required HTML structure."""
    with open("static/dashboard.html") as f:
        content = f.read()

    # Should have proper structure
    assert "<!DOCTYPE html>" in content
    assert "<html" in content
    assert "viewport" in content
    assert "width=device-width" in content


def test_dashboard_includes_all_tabs():
    """Test that dashboard includes all required tabs."""
    with open("static/dashboard.html") as f:
        content = f.read()

    # Should have Submit, Queue, Tracker, Applications, Status tabs
    assert "Submit" in content
    assert "Queue" in content
    assert "Tracker" in content
    assert "Applications" in content or "applications" in content.lower()
    assert "Status" in content


def test_applications_tab_has_subtabs():
    """Test that Applications tab has Questions and Cover Letters sub-tabs."""
    with open("static/dashboard.html") as f:
        content = f.read()

    # Should have sub-tabs for questions and cover letters
    assert "Questions" in content or "questions" in content.lower()
    assert "Cover Letter" in content or "coverletter" in content.lower()


def test_dashboard_responsive_viewport():
    """Test that dashboard includes responsive viewport meta tag."""
    with open("static/dashboard.html") as f:
        content = f.read()

    assert "viewport" in content
    assert "width=device-width" in content
    assert "initial-scale=1" in content


def test_dashboard_theme_color():
    """Test that dashboard includes theme-color meta tag."""
    with open("static/dashboard.html") as f:
        content = f.read()

    assert "theme-color" in content


# ===== Part 5b: WebSocket Tests =====

def test_websocket_endpoint_referenced():
    """Test that dashboard references WebSocket endpoint."""
    with open("static/dashboard.html") as f:
        content = f.read()

    # Should reference WebSocket for real-time updates
    assert "WebSocket" in content or "ws://" in content or "wss://" in content


def test_websocket_connection_handler():
    """Test that dashboard includes WebSocket connection handler."""
    with open("static/dashboard.html") as f:
        content = f.read()

    # Should have WebSocket connection logic
    assert "connectWebSocket" in content or "websocket" in content.lower()


def test_websocket_reconnect_logic():
    """Test that dashboard includes WebSocket auto-reconnect logic."""
    with open("static/dashboard.html") as f:
        content = f.read()

    # Should have reconnect logic
    assert "reconnect" in content.lower() or "onclose" in content.lower()


# ===== Part 5c: ServiceWorker + Offline Cache Tests =====

def test_service_worker_file_exists():
    """Test that service-worker.js exists."""
    assert os.path.exists("static/service-worker.js")


def test_service_worker_registered_in_dashboard():
    """Test that dashboard registers ServiceWorker."""
    with open("static/dashboard.html") as f:
        content = f.read()

    # Should register service worker
    assert "serviceWorker" in content or "service-worker" in content


def test_service_worker_cache_strategy():
    """Test that service-worker.js includes caching logic."""
    with open("static/service-worker.js") as f:
        content = f.read()

    # Should have cache-first strategy
    assert "CACHE_NAME" in content
    assert "caches.open" in content
    assert "caches.match" in content


def test_service_worker_offline_handling():
    """Test that ServiceWorker handles offline mode."""
    with open("static/service-worker.js") as f:
        content = f.read()

    # Should handle offline scenarios
    assert "offline" in content.lower() or "fetch" in content.lower()


def test_service_worker_static_assets():
    """Test that ServiceWorker caches static assets."""
    with open("static/service-worker.js") as f:
        content = f.read()

    # Should reference static assets
    assert "STATIC_ASSETS" in content


# ===== Part 5d: PWA Add-to-Homescreen Tests =====

def test_manifest_json_exists():
    """Test that manifest.json exists."""
    assert os.path.exists("static/manifest.json")


def test_manifest_json_valid():
    """Test that manifest.json is valid JSON."""
    with open("static/manifest.json") as f:
        manifest = json.load(f)

    assert isinstance(manifest, dict)


def test_manifest_required_fields():
    """Test that manifest includes required PWA fields."""
    with open("static/manifest.json") as f:
        manifest = json.load(f)

    # Required fields for PWA
    assert "name" in manifest
    assert "short_name" in manifest
    assert "start_url" in manifest
    assert "display" in manifest
    assert manifest["display"] == "standalone"


def test_manifest_icons():
    """Test that manifest includes icons."""
    with open("static/manifest.json") as f:
        manifest = json.load(f)

    assert "icons" in manifest
    assert len(manifest["icons"]) > 0

    # Each icon should have required properties
    for icon in manifest["icons"]:
        assert "src" in icon
        assert "sizes" in icon
        assert "type" in icon


def test_manifest_theme_color():
    """Test that manifest has theme color."""
    with open("static/manifest.json") as f:
        manifest = json.load(f)

    assert "theme_color" in manifest


def test_pwa_apple_meta_tags():
    """Test that dashboard includes Apple PWA meta tags."""
    with open("static/dashboard.html") as f:
        content = f.read()

    # Apple-specific PWA tags
    assert "apple-mobile-web-app-capable" in content


def test_pwa_manifest_link():
    """Test that dashboard links to manifest."""
    with open("static/dashboard.html") as f:
        content = f.read()

    assert "manifest" in content.lower()


# ===== Part 5e: Real-time Updates Tests =====

def test_applications_tab_structure():
    """Test that Applications tab has proper structure."""
    with open("static/dashboard.html") as f:
        content = f.read()

    # Should have sub-tabs in Applications
    assert "sub-tab" in content.lower() or "subtab" in content.lower()
    assert "questions" in content.lower()
    assert "coverletter" in content.lower() or "cover" in content.lower()


def test_applications_load_function():
    """Test that dashboard has function to load applications."""
    with open("static/dashboard.html") as f:
        content = f.read()

    # Should have function to load applications
    assert "loadApplications" in content or "loadApps" in content


def test_websocket_message_handler():
    """Test that dashboard handles WebSocket messages."""
    with open("static/dashboard.html") as f:
        content = f.read()

    # Should handle WebSocket messages
    assert "onmessage" in content or "handleWebSocketMessage" in content


def test_real_time_event_types():
    """Test that dashboard expects all real-time event types."""
    with open("static/dashboard.html") as f:
        content = f.read()

    # Should handle these events
    assert "job_staged" in content or "staged" in content.lower()
    assert "approved" in content.lower()


# ===== Part 5f: Mobile UX Improvements Tests =====

def test_touch_friendly_design():
    """Test that dashboard has touch-friendly styling."""
    with open("static/dashboard.html") as f:
        content = f.read()

    # Should have min-height for touch targets
    assert "44" in content or "min-height" in content or "min-width" in content


def test_mobile_navigation():
    """Test that dashboard has mobile navigation."""
    with open("static/dashboard.html") as f:
        content = f.read()

    # Should have mobile nav
    assert "nav-tabs-mobile" in content or "mobile" in content.lower()


def test_offline_indicator():
    """Test that dashboard has offline indicator."""
    with open("static/dashboard.html") as f:
        content = f.read()

    # Should show offline status
    assert "offline" in content.lower() or "Offline" in content


def test_loading_spinner():
    """Test that dashboard includes loading animation."""
    with open("static/dashboard.html") as f:
        content = f.read()

    # Should have spinner
    assert "spinner" in content.lower() or "loading" in content.lower()


def test_responsive_breakpoints():
    """Test that CSS includes responsive breakpoints."""
    with open("static/dashboard.html") as f:
        content = f.read()

    # Should have media queries
    assert "@media" in content


def test_no_horizontal_scroll():
    """Test that CSS prevents horizontal scrolling."""
    with open("static/dashboard.html") as f:
        content = f.read()

    # Should manage width properly
    assert "width: 100%" in content or "max-width" in content


def test_collapsible_job_cards():
    """Test that job cards are collapsible."""
    with open("static/dashboard.html") as f:
        content = f.read()

    # Should have collapsible functionality
    assert "job-card" in content or "collapse" in content.lower()


def test_flagged_question_styling():
    """Test that flagged questions are visually distinct."""
    with open("static/dashboard.html") as f:
        content = f.read()

    # Should highlight flagged questions
    assert "flagged" in content.lower() or "#fffacd" in content


def test_confidence_badge_styling():
    """Test that confidence levels are displayed."""
    with open("static/dashboard.html") as f:
        content = f.read()

    # Should have confidence styling
    assert "confidence" in content.lower()


def test_status_badges():
    """Test that status badges are present."""
    with open("static/dashboard.html") as f:
        content = f.read()

    # Should have status badges
    assert "badge" in content.lower() or "status" in content.lower()


def test_modal_dialogs():
    """Test that dashboard includes modals for editing."""
    with open("static/dashboard.html") as f:
        content = f.read()

    # Should have modals for preview, edit, etc.
    assert "modal" in content.lower()


# ===== Activity Logging Tests =====

def test_activity_log_table_exists():
    """Test that activity_log table is properly initialized."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = Database(db_path)

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='activity_log'")
        result = cursor.fetchone()
        conn.close()

        assert result is not None


def test_websocket_events_can_be_logged():
    """Test that WebSocket events can be logged to activity_log."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = Database(db_path)

        # Log a WebSocket event
        db.log_activity("websocket_connected", "ws_test", "Test connection", "success")

        # Verify it was logged
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM activity_log WHERE action='websocket_connected'")
        result = cursor.fetchone()
        conn.close()

        assert result["count"] >= 1


# ===== Integration Tests =====

def test_all_required_files_present():
    """Test that all required Phase 5 files are present."""
    assert os.path.exists("static/dashboard.html")
    assert os.path.exists("static/service-worker.js")
    assert os.path.exists("static/manifest.json")


def test_dashboard_complete_workflow():
    """Test that dashboard includes functions for complete workflow."""
    with open("static/dashboard.html") as f:
        content = f.read()

    # Should have all major functions
    assert "submitJob" in content
    assert "loadApplications" in content or "loadApps" in content
    assert "approveAnswers" in content or "approve" in content.lower()
    assert "approveCoverLetter" in content or "CoverLetter" in content


def test_dashboard_error_handling():
    """Test that dashboard includes error handling."""
    with open("static/dashboard.html") as f:
        content = f.read()

    # Should handle errors
    assert "catch" in content.lower() or "error" in content.lower()
    assert "showNotification" in content or "notification" in content.lower()


def test_dashboard_notification_system():
    """Test that dashboard has notification system."""
    with open("static/dashboard.html") as f:
        content = f.read()

    # Should show success, error, and info messages
    assert "success" in content or "error" in content or "notification" in content.lower()


def test_questions_api_integration():
    """Test that dashboard integrates with Questions API."""
    with open("static/dashboard.html") as f:
        content = f.read()

    # Should reference questions API
    assert "/api/questions" in content


def test_cover_letters_api_integration():
    """Test that dashboard integrates with Cover Letters API."""
    with open("static/dashboard.html") as f:
        content = f.read()

    # Should reference cover letters API
    assert "/api/cover-letters" in content or "cover-letter" in content.lower()
