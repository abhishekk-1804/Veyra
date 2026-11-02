"""Test serving of vanilla HTML/CSS/JS frontend files."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_index_html_served() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Veyra" in response.text
    assert "AI-Native" in response.text


def test_css_served() -> None:
    response = client.get("/css/base.css")
    assert response.status_code == 200
    assert "text/css" in response.headers.get("content-type", "")
    assert "--font-sans" in response.text


def test_js_served() -> None:
    response = client.get("/js/app.js")
    assert response.status_code == 200
    assert "javascript" in response.headers.get("content-type", "")
    assert "Initializing Veyra" in response.text
