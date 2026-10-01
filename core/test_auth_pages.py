import pytest

from .models import User


@pytest.mark.django_db
def test_browser_entry_redirects_to_login_but_api_keeps_json_auth_error(client):
    page_response = client.get('/')
    api_response = client.get('/api/people/')

    assert page_response.status_code == 302
    assert page_response['Location'] == '/login/'
    assert api_response.status_code == 401
    assert api_response.json()['error']['code'] == 'AUTHENTICATION_REQUIRED'


@pytest.mark.django_db
def test_signup_page_creates_session_and_opens_dashboard(client):
    response = client.post(
        '/signup/',
        {
            'name': 'Owner',
            'email': 'owner@example.com',
            'password': 'Strong-password-123!',
            'password_confirm': 'Strong-password-123!',
        },
    )

    assert response.status_code == 302
    assert response['Location'] == '/'
    assert User.objects.filter(email='owner@example.com').exists()
    assert client.get('/').status_code == 200
