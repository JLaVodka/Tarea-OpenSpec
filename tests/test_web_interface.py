"""Recursos web del sistema y documentación API."""


def test_root_serves_the_application_interface(api_client):
    response = api_client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert '<main id="app-main">' in response.text
    assert "Reservas Académicas" in response.text


def test_interface_javascript_is_served_from_same_origin(api_client):
    response = api_client.get("/assets/app.js")

    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]
    assert "/auth/login" in response.text
    assert "/reservations" in response.text


def test_openapi_docs_remain_available_with_web_interface(api_client):
    response = api_client.get("/docs")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
