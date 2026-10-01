"""Regression tests for the issues found in the previous review round."""
from datetime import date
from decimal import Decimal

import pytest

from .models import Account, BankAccountDetails, CreditCardDetails, Person, Transaction, User
from .services import (
    FinancialValidationError,
    account_summaries,
    bank_balance,
    create_card_payment,
    create_expense,
    create_received,
    create_transaction,
    credit_used,
    restore_transaction,
    update_account,
    update_person,
    void_transaction,
)


@pytest.fixture
def setup(db):
    user = User.objects.create_user(email='owner@example.com', password='Strong-password-123!')
    person = Person.objects.create(user=user, name='Family member')
    bank = Account.objects.create(user=user, name='Bank', account_type=Account.AccountType.BANK)
    BankAccountDetails.objects.create(account=bank, opening_balance=Decimal('0.00'))
    card = Account.objects.create(user=user, name='Card', account_type=Account.AccountType.CREDIT_CARD)
    CreditCardDetails.objects.create(account=card, credit_limit=Decimal('1000.00'), opening_available_credit=Decimal('1000.00'))
    return user, person, bank, card


def test_void_is_refused_if_it_would_make_a_balance_negative(setup):
    user, person, bank, _ = setup
    received = create_received(user=user, transaction_date=date(2026, 1, 1), person_id=person.pk, account_id=bank.pk, amount='100', description='in')
    create_expense(user=user, transaction_date=date(2026, 1, 2), person_id=person.pk, account_id=bank.pk, amount='100', description='out')

    with pytest.raises(FinancialValidationError):
        void_transaction(user=user, transaction_id=received.pk)
    assert bank_balance(user, bank) == Decimal('0.00')


def test_void_is_refused_if_it_would_make_credit_used_negative(setup):
    user, person, bank, card = setup
    create_received(user=user, transaction_date=date(2026, 1, 1), person_id=person.pk, account_id=bank.pk, amount='500', description='in')
    expense = create_expense(user=user, transaction_date=date(2026, 1, 2), person_id=person.pk, account_id=card.pk, amount='200', description='card')
    create_card_payment(user=user, transaction_date=date(2026, 1, 3), credit_card_id=card.pk, amount='200', payment_source='BANK_ACCOUNT', source_account_id=bank.pk)

    with pytest.raises(FinancialValidationError):
        void_transaction(user=user, transaction_id=expense.pk)
    assert credit_used(user, card) == Decimal('0.00')


def test_edit_keeps_the_original_effect_rows(setup):
    user, person, bank, _ = setup
    create_received(user=user, transaction_date=date(2026, 1, 1), person_id=person.pk, account_id=bank.pk, amount='500', description='in')
    expense = create_expense(user=user, transaction_date=date(2026, 1, 2), person_id=person.pk, account_id=bank.pk, amount='50', description='x')
    from .services import update_transaction

    update_transaction(
        user=user, transaction_id=expense.pk, transaction_type='EXPENSE', transaction_date=date(2026, 1, 2),
        person_id=person.pk, account_id=bank.pk, amount='60', description='x',
    )
    expense.refresh_from_db()
    assert expense.effects.count() == 2
    assert bank_balance(user, bank) == Decimal('440.00')


def test_backdated_transaction_is_rejected_if_it_breaks_the_balance_on_that_date(setup):
    user, person, bank, _ = setup
    create_received(user=user, transaction_date=date(2026, 6, 1), person_id=person.pk, account_id=bank.pk, amount='100', description='in')
    with pytest.raises(FinancialValidationError):
        create_expense(user=user, transaction_date=date(2026, 1, 1), person_id=person.pk, account_id=bank.pk, amount='100', description='backdated')


def test_voided_transaction_can_be_restored(setup):
    user, person, bank, _ = setup
    create_received(user=user, transaction_date=date(2026, 1, 1), person_id=person.pk, account_id=bank.pk, amount='10', description='in')
    expense = create_expense(user=user, transaction_date=date(2026, 1, 1), person_id=person.pk, account_id=bank.pk, amount='10', description='x')
    void_transaction(user=user, transaction_id=expense.pk)
    assert bank_balance(user, bank) == Decimal('10.00')
    restore_transaction(user=user, transaction_id=expense.pk)
    expense.refresh_from_db()
    assert expense.status == Transaction.Status.ACTIVE
    assert bank_balance(user, bank) == Decimal('0.00')


def test_income_bonus_extra_deposit_to_bank_without_a_person(setup):
    user, _, bank, _ = setup
    for tx_type, amount in (('INCOME', '1000'), ('BONUS', '500'), ('EXTRA', '250')):
        create_transaction(
            user=user, transaction_type=tx_type, transaction_date=date(2026, 1, 1),
            account_id=bank.pk, amount=amount, description=tx_type.title(),
        )
    assert bank_balance(user, bank) == Decimal('1750.00')


def test_account_summaries_matches_individual_lookups(setup):
    user, person, bank, card = setup
    create_expense(user=user, transaction_date=date(2026, 1, 1), person_id=person.pk, account_id=card.pk, amount='40', description='x')
    summaries = account_summaries(user, [bank, card])
    assert summaries[bank.pk]['balance'] == bank_balance(user, bank)
    assert summaries[card.pk]['used'] == credit_used(user, card)


def test_update_account_renames_and_adjusts_opening_balance(setup):
    user, _, bank, card = setup
    update_account(user=user, account_id=bank.pk, name='Renamed bank', opening_balance=Decimal('200.00'))
    bank.refresh_from_db()
    assert bank.name == 'Renamed bank'
    assert bank_balance(user, bank) == Decimal('200.00')

    update_account(user=user, account_id=card.pk, credit_limit=Decimal('1500.00'))
    assert credit_used(user, card) == Decimal('0.00')


def test_update_person_renames(setup):
    user, person, _, _ = setup
    update_person(user=user, person_id=person.pk, name='New name')
    person.refresh_from_db()
    assert person.name == 'New name'


@pytest.mark.django_db
def test_signup_page_requires_matching_password_confirmation(client):
    response = client.post(
        '/signup/',
        {'name': 'Owner', 'email': 'owner@example.com', 'password': 'Strong-password-123!', 'password_confirm': 'different'},
    )
    assert response.status_code == 200
    assert b'do not match' in response.content
    assert not User.objects.filter(email='owner@example.com').exists()


@pytest.mark.django_db
def test_people_page_offers_archive_and_edit_actions(client):
    user = User.objects.create_user(email='owner@example.com', password='Strong-password-123!')
    person = Person.objects.create(user=user, name='Mom')
    client.force_login(user)

    response = client.get('/people/')
    assert response.status_code == 200
    assert f'/people/{person.pk}/edit/'.encode() in response.content
    assert f'/people/{person.pk}/archive-toggle/'.encode() in response.content

    toggle = client.post(f'/people/{person.pk}/archive-toggle/')
    assert toggle.status_code == 302
    person.refresh_from_db()
    assert person.status == Person.Status.ARCHIVED


@pytest.mark.django_db
def test_accounts_page_offers_edit_and_archive_actions(client):
    user = User.objects.create_user(email='owner@example.com', password='Strong-password-123!')
    bank = Account.objects.create(user=user, name='SBI', account_type=Account.AccountType.BANK)
    BankAccountDetails.objects.create(account=bank, opening_balance=Decimal('500.00'))
    client.force_login(user)

    response = client.get('/accounts/')
    assert response.status_code == 200
    assert f'/accounts/{bank.pk}/edit/'.encode() in response.content
    assert f'/accounts/{bank.pk}/archive-toggle/'.encode() in response.content


@pytest.mark.django_db
def test_transactions_page_shows_restore_action_for_voided_transactions(client):
    user = User.objects.create_user(email='owner@example.com', password='Strong-password-123!')
    person = Person.objects.create(user=user, name='Mom')
    bank = Account.objects.create(user=user, name='Bank', account_type=Account.AccountType.BANK)
    BankAccountDetails.objects.create(account=bank, opening_balance=Decimal('100.00'))
    client.force_login(user)
    created = create_expense(user=user, transaction_date=date(2026, 1, 1), person_id=person.pk, account_id=bank.pk, amount='10', description='x')
    void_transaction(user=user, transaction_id=created.pk)

    response = client.get('/transactions/')
    assert response.status_code == 200
    assert f'/transactions/{created.pk}/restore/'.encode() in response.content


@pytest.mark.django_db
def test_dashboard_shows_current_account_balance_not_opening_balance(client):
    user = User.objects.create_user(email='owner@example.com', password='Strong-password-123!')
    person = Person.objects.create(user=user, name='Mom')
    bank = Account.objects.create(user=user, name='Bank', account_type=Account.AccountType.BANK)
    BankAccountDetails.objects.create(account=bank, opening_balance=Decimal('100.00'))
    client.force_login(user)
    create_received(user=user, transaction_date=date(2026, 1, 1), person_id=person.pk, account_id=bank.pk, amount='50', description='in')

    response = client.get('/')
    assert response.status_code == 200
    assert b'150.00' in response.content
