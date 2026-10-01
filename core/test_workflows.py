from datetime import date
from decimal import Decimal

import pytest

from .models import Account, BankAccountDetails, CardPaymentDetails, CreditCardDetails, Person, Transaction, User, UserPreferences
from .services import create_expense, credit_used


@pytest.mark.django_db
def test_card_pay_form_creates_bank_payment_effects(client):
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
    client.force_login(user)

    response = client.post(
        '/card-payments/new/',
        {
            'credit_card_id': str(card.pk),
            'amount': '10.00',
            'date': '2026-09-24',
            'payment_source': 'BANK_ACCOUNT',
            'source_account_id': str(bank.pk),
            'description': 'Payment from bank',
        },
    )

    assert response.status_code == 302
    payment = Transaction.objects.get(user=user, transaction_type=Transaction.TransactionType.CARD_PAYMENT)
    assert payment.card_payment_details.payment_source == CardPaymentDetails.PaymentSource.BANK_ACCOUNT
    assert credit_used(user, card) == Decimal('20.00')


@pytest.mark.django_db
def test_settings_persist_preferences_and_restore_archived_records(client):
    user = User.objects.create_user(email='owner@example.com', password='Strong-password-123!')
    person = Person.objects.create(user=user, name='Archived person', status=Person.Status.ARCHIVED)
    account = Account.objects.create(
        user=user,
        name='Archived account',
        account_type=Account.AccountType.BANK,
        status=Account.Status.ARCHIVED,
    )
    BankAccountDetails.objects.create(account=account, opening_balance=Decimal('0.00'))
    client.force_login(user)

    response = client.post(
        '/settings/',
        {'currency': 'USD', 'date_format': 'YYYY-MM-DD', 'theme': 'LIGHT'},
    )
    assert response.status_code == 302
    assert UserPreferences.objects.get(user=user).currency == 'USD'

    assert client.post(f'/settings/people/{person.pk}/restore/').status_code == 302
    assert client.post(f'/settings/accounts/{account.pk}/restore/').status_code == 302
    person.refresh_from_db()
    account.refresh_from_db()
    assert person.status == Person.Status.ACTIVE
    assert account.status == Account.Status.ACTIVE
