from datetime import date
from decimal import Decimal
import json

import pytest

from .models import Account, BankAccountDetails, Person, Transaction, User
from .services import create_expense


@pytest.mark.django_db
def test_transaction_api_combines_filters_and_cursor_pages(client):
    user = User.objects.create_user(email='owner@example.com', password='Strong-password-123!')
    other_user = User.objects.create_user(email='other@example.com', password='Strong-password-123!')
    person = Person.objects.create(user=user, name='Family member')
    other_person = Person.objects.create(user=other_user, name='Other member')
    bank = Account.objects.create(user=user, name='Bank', account_type=Account.AccountType.BANK)
    other_bank = Account.objects.create(user=other_user, name='Other bank', account_type=Account.AccountType.BANK)
    BankAccountDetails.objects.create(account=bank, opening_balance=Decimal('500.00'))
    BankAccountDetails.objects.create(account=other_bank, opening_balance=Decimal('500.00'))
    for transaction_date, amount, description in (
        (date(2026, 9, 21), '10.00', 'Groceries'),
        (date(2026, 9, 22), '20.00', 'Medicine'),
        (date(2026, 9, 23), '30.00', 'Groceries again'),
    ):
        create_expense(
            user=user,
            transaction_date=transaction_date,
            person_id=person.pk,
            account_id=bank.pk,
            amount=amount,
            description=description,
        )
    create_expense(
        user=other_user,
        transaction_date=date(2026, 9, 24),
        person_id=other_person.pk,
        account_id=other_bank.pk,
        amount='30.00',
        description='Other groceries',
    )
    client.force_login(user)

    first_page = client.get(
        f'/api/transactions/?person_id={person.pk}&account_type=BANK&search=groceries&amount_min=10&limit=1'
    )

    assert first_page.status_code == 200
    first_payload = first_page.json()
    assert [item['description'] for item in first_payload['results']] == ['Groceries again']
    assert first_payload['has_more'] is True

    second_page = client.get(
        f"/api/transactions/?person_id={person.pk}&account_type=BANK&search=groceries&amount_min=10&limit=1&cursor={first_payload['next_cursor']}"
    )

    assert second_page.status_code == 200
    assert [item['description'] for item in second_page.json()['results']] == ['Groceries']
    assert all(item['description'] != 'Other groceries' for item in second_page.json()['results'])


@pytest.mark.django_db
def test_transaction_api_rejects_invalid_filter_values(client):
    user = User.objects.create_user(email='owner@example.com', password='Strong-password-123!')
    client.force_login(user)

    response = client.get('/api/transactions/?transaction_type=UNKNOWN')

    assert response.status_code == 400
    assert response.json()['error']['code'] == 'VALIDATION_ERROR'
