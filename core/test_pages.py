from datetime import date
from decimal import Decimal

import pytest

from .models import Account, BankAccountDetails, Person, User
from .services import create_expense


@pytest.mark.django_db
def test_financial_pages_require_authentication(client):
    for path in ('/people/', '/accounts/', '/transactions/'):
        response = client.get(path)
        assert response.status_code == 302
        assert response['Location'] == '/login/'


@pytest.mark.django_db
def test_financial_pages_render_only_authenticated_users_records(client):
    user = User.objects.create_user(email='owner@example.com', password='Strong-password-123!')
    other_user = User.objects.create_user(email='other@example.com', password='Strong-password-123!')
    person = Person.objects.create(user=user, name='Private person')
    other_person = Person.objects.create(user=other_user, name='Other person')
    bank = Account.objects.create(user=user, name='Private bank', account_type=Account.AccountType.BANK)
    BankAccountDetails.objects.create(account=bank, opening_balance=Decimal('100.00'))
    create_expense(
        user=user,
        transaction_date=date(2026, 9, 24),
        person_id=person.pk,
        account_id=bank.pk,
        amount='10.00',
        description='Private groceries',
    )
    client.force_login(user)

    people_response = client.get('/people/')
    accounts_response = client.get('/accounts/')
    transactions_response = client.get('/transactions/?search=Private')

    assert people_response.status_code == 200
    assert b'Private person' in people_response.content
    assert b'Other person' not in people_response.content
    assert b'Private bank' in accounts_response.content
    assert b'Private groceries' in transactions_response.content
    assert b'Other person' not in transactions_response.content


@pytest.mark.django_db
def test_transaction_page_combines_search_and_type_filters(client):
    user = User.objects.create_user(email='owner@example.com', password='Strong-password-123!')
    person = Person.objects.create(user=user, name='Family member')
    bank = Account.objects.create(user=user, name='Bank', account_type=Account.AccountType.BANK)
    BankAccountDetails.objects.create(account=bank, opening_balance=Decimal('100.00'))
    create_expense(
        user=user,
        transaction_date=date(2026, 9, 24),
        person_id=person.pk,
        account_id=bank.pk,
        amount='10.00',
        description='Groceries',
    )
    client.force_login(user)

    response = client.get('/transactions/?search=medicine&transaction_type=EXPENSE')

    assert response.status_code == 200
    assert b'No transactions match these filters.' in response.content
