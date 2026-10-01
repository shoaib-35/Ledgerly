from decimal import Decimal

import pytest

from .models import Account, BankAccountDetails, Person, Transaction, User


@pytest.mark.django_db
def test_html_forms_create_edit_and_void_a_transaction(client):
    user = User.objects.create_user(email='owner@example.com', password='Strong-password-123!')
    client.force_login(user)

    person_response = client.post('/people/new/', {'name': 'Family member'})
    account_response = client.post(
        '/accounts/new/',
        {'name': 'Bank', 'account_type': 'BANK', 'opening_balance': '100.00'},
    )
    person = Person.objects.get(user=user)
    account = Account.objects.get(user=user)
    transaction_response = client.post(
        '/transactions/new/',
        {
            'transaction_type': 'EXPENSE',
            'date': '2026-09-24',
            'person_id': str(person.pk),
            'account_id': str(account.pk),
            'amount': '25.00',
            'description': 'Groceries',
        },
    )

    created = Transaction.objects.get(user=user)
    assert person_response.status_code == 302
    assert account_response.status_code == 302
    assert transaction_response.status_code == 302
    assert created.amount == Decimal('25.00')
    assert created.effects.count() == 2

    edit_response = client.post(
        f'/transactions/{created.pk}/edit/',
        {
            'transaction_type': 'EXPENSE',
            'date': '2026-09-25',
            'person_id': str(person.pk),
            'account_id': str(account.pk),
            'amount': '10.00',
            'description': 'Updated groceries',
        },
    )
    created.refresh_from_db()
    assert edit_response.status_code == 302
    assert created.amount == Decimal('10.00')
    assert created.description == 'Updated groceries'

    void_response = client.post(f'/transactions/{created.pk}/void/')
    created.refresh_from_db()
    assert void_response.status_code == 302
    assert created.status == Transaction.Status.VOIDED
    assert BankAccountDetails.objects.get(account=account).opening_balance == Decimal('100.00')
