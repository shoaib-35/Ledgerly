import json
from decimal import Decimal

import pytest

from .models import Account, Person, Transaction, User


@pytest.mark.django_db
def test_signup_establishes_session_and_me_returns_user(client):
    response = client.post(
        '/api/auth/signup/',
        data=json.dumps({'name': 'Owner', 'email': 'owner@example.com', 'password': 'Strong-password-123!'}),
        content_type='application/json',
    )

    assert response.status_code == 201
    assert response.json()['user']['email'] == 'owner@example.com'
    assert client.get('/api/auth/me/').status_code == 200
    assert User.objects.get(email='owner@example.com').preferences.currency == 'INR'


@pytest.mark.django_db
def test_financial_endpoints_require_authentication(client):
    response = client.get('/api/people/')

    assert response.status_code == 401
    assert response.json()['error']['code'] == 'AUTHENTICATION_REQUIRED'


@pytest.mark.django_db
def test_authenticated_user_can_create_owned_financial_records(client):
    user = User.objects.create_user(email='owner@example.com', password='Strong-password-123!')
    client.force_login(user)

    person_response = client.post(
        '/api/people/',
        data=json.dumps({'name': 'Family member'}),
        content_type='application/json',
    )
    account_response = client.post(
        '/api/accounts/',
        data=json.dumps({'name': 'Bank', 'account_type': 'BANK', 'opening_balance': '100.00'}),
        content_type='application/json',
    )

    person_id = person_response.json()['person']['id']
    account_id = account_response.json()['account']['id']
    transaction_response = client.post(
        '/api/transactions/',
        data=json.dumps(
            {
                'date': '2026-09-24',
                'person_id': person_id,
                'account_id': account_id,
                'transaction_type': 'EXPENSE',
                'amount': '25.00',
                'description': 'Groceries',
            }
        ),
        content_type='application/json',
    )

    assert person_response.status_code == 201
    assert account_response.status_code == 201
    assert transaction_response.status_code == 201
    assert transaction_response.json()['transaction']['amount'] == '25.00'
    assert Transaction.objects.filter(user=user).count() == 1
    assert Account.objects.filter(user=user).count() == 1
    assert Person.objects.filter(user=user).count() == 1


@pytest.mark.django_db
def test_cross_user_object_ids_return_not_found(client):
    owner = User.objects.create_user(email='owner@example.com', password='Strong-password-123!')
    other_user = User.objects.create_user(email='other@example.com', password='Strong-password-123!')
    person = Person.objects.create(user=owner, name='Private person')
    client.force_login(other_user)

    response = client.get(f'/api/people/{person.pk}/')

    assert response.status_code == 404
    assert response.json()['error']['code'] == 'NOT_FOUND'


@pytest.mark.django_db
def test_logout_invalidates_authenticated_session(client):
    user = User.objects.create_user(email='owner@example.com', password='Strong-password-123!')
    client.force_login(user)

    assert client.post('/api/auth/logout/').status_code == 200
    assert client.get('/api/auth/me/').status_code == 401
