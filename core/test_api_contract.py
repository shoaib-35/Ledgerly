import json
from datetime import date
from decimal import Decimal

import pytest

from .models import Account, BankAccountDetails, CreditCardDetails, Person, Transaction, User
from .services import create_expense


@pytest.fixture
def api_financial_setup():
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
        amount='30.00',
        description='Card purchase',
    )
    return user, person, bank, card


@pytest.mark.django_db
def test_dedicated_card_payment_api_uses_documented_contract(client, api_financial_setup):
    user, _, bank, card = api_financial_setup
    client.force_login(user)

    response = client.post(
        '/api/card-payments/',
        data=json.dumps(
            {
                'credit_card_account_id': str(card.pk),
                'amount': '10.00',
                'payment_source_type': 'BANK_ACCOUNT',
                'source_account_id': str(bank.pk),
                'date': '2026-09-24',
            }
        ),
        content_type='application/json',
    )

    assert response.status_code == 201
    assert response.json()['transaction']['transaction_type'] == 'CARD_PAYMENT'
    assert Transaction.objects.filter(user=user, transaction_type='CARD_PAYMENT').count() == 1


@pytest.mark.django_db
def test_person_and_account_history_and_position_are_scoped(client, api_financial_setup):
    user, person, bank, _ = api_financial_setup
    other_user = User.objects.create_user(email='other@example.com', password='Strong-password-123!')
    client.force_login(user)

    person_history = client.get(f'/api/people/{person.pk}/transactions/')
    position = client.get(f'/api/people/{person.pk}/position/')
    account_history = client.get(f'/api/accounts/{bank.pk}/transactions/')

    assert person_history.status_code == 200
    assert len(person_history.json()['results']) == 1
    assert position.json()['position'] == '-30.00'
    assert len(account_history.json()['results']) == 0

    client.force_login(other_user)
    assert client.get(f'/api/people/{person.pk}/transactions/').status_code == 404
    assert client.get(f'/api/people/{person.pk}/position/').status_code == 404
    assert client.get(f'/api/accounts/{bank.pk}/transactions/').status_code == 404
