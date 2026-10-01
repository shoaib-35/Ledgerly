from datetime import date
from decimal import Decimal

import pytest

from .models import Account, BankAccountDetails, CreditCardDetails, Person, User
from .services import create_expense


@pytest.mark.django_db
def test_dashboard_api_separates_bank_and_credit_values(client):
    user = User.objects.create_user(email='owner@example.com', password='Strong-password-123!')
    person = Person.objects.create(user=user, name='Family member')
    bank = Account.objects.create(user=user, name='Bank', account_type=Account.AccountType.BANK)
    BankAccountDetails.objects.create(account=bank, opening_balance=Decimal('100.00'))
    card = Account.objects.create(user=user, name='Card', account_type=Account.AccountType.CREDIT_CARD)
    CreditCardDetails.objects.create(
        account=card,
        credit_limit=Decimal('100.00'),
        opening_available_credit=Decimal('100.00'),
    )
    create_expense(
        user=user,
        transaction_date=date(2026, 9, 24),
        person_id=person.pk,
        account_id=card.pk,
        amount='25.00',
        description='Card purchase',
    )
    client.force_login(user)

    response = client.get('/api/dashboard/')

    assert response.status_code == 200
    payload = response.json()
    assert payload['financial_overview'] == {
        'bank_balance': '100.00',
        'credit_used': '25.00',
        'credit_available': '75.00',
    }
    assert payload['family_positions'][0]['position'] == '-25.00'
    assert payload['recent_transactions'][0]['description'] == 'Card purchase'


@pytest.mark.django_db
def test_dashboard_html_requires_authentication_and_renders_for_owner(client):
    user = User.objects.create_user(email='owner@example.com', password='Strong-password-123!')

    response = client.get('/')
    assert response.status_code == 302
    assert response['Location'] == '/login/'

    client.force_login(user)
    response = client.get('/')

    assert response.status_code == 200
    assert b'Financial overview' in response.content
    assert b'Family positions' in response.content
