from datetime import date
from decimal import Decimal

import pytest

from .models import (
    Account,
    BankAccountDetails,
    CardPaymentDetails,
    CreditCardDetails,
    Person,
    Transaction,
    TransactionEffect,
    User,
)
from .services import (
    FinancialValidationError,
    OwnershipError,
    bank_balance,
    archive_account,
    archive_person,
    create_card_payment,
    create_expense,
    create_received,
    credit_available,
    credit_used,
    person_position,
    restore_account,
    restore_person,
    update_transaction,
)


@pytest.fixture
def financial_setup():
    user = User.objects.create_user(email='owner@example.com', password='test-password')
    person = Person.objects.create(user=user, name='Family member')
    bank = Account.objects.create(user=user, name='Bank', account_type=Account.AccountType.BANK)
    BankAccountDetails.objects.create(account=bank, opening_balance=Decimal('100.00'))
    card = Account.objects.create(user=user, name='Card', account_type=Account.AccountType.CREDIT_CARD)
    CreditCardDetails.objects.create(
        account=card,
        credit_limit=Decimal('100.00'),
        opening_available_credit=Decimal('100.00'),
    )
    return user, person, bank, card


@pytest.mark.django_db
def test_bank_expense_and_received_money_generate_signed_effects(financial_setup):
    user, person, bank, _ = financial_setup

    expense = create_expense(
        user=user,
        transaction_date=date(2026, 9, 24),
        person_id=person.pk,
        account_id=bank.pk,
        amount='25.00',
        description='Groceries',
    )
    received = create_received(
        user=user,
        transaction_date=date(2026, 9, 24),
        person_id=person.pk,
        account_id=bank.pk,
        amount='15.00',
        description='Reimbursement',
    )

    assert expense.effects.count() == 2
    assert received.effects.count() == 2
    assert person_position(user, person) == Decimal('-10.00')
    assert bank_balance(user, bank) == Decimal('90.00')


@pytest.mark.django_db
def test_card_expense_and_bank_payment_update_credit_and_cash(financial_setup):
    user, person, bank, card = financial_setup

    create_expense(
        user=user,
        transaction_date=date(2026, 9, 24),
        person_id=person.pk,
        account_id=card.pk,
        amount='30.00',
        description='Card purchase',
    )
    create_card_payment(
        user=user,
        transaction_date=date(2026, 9, 24),
        credit_card_id=card.pk,
        amount='10.00',
        payment_source=CardPaymentDetails.PaymentSource.BANK_ACCOUNT,
        source_account_id=bank.pk,
    )

    assert credit_used(user, card) == Decimal('20.00')
    assert credit_available(user, card) == Decimal('80.00')
    assert bank_balance(user, bank) == Decimal('90.00')
    assert Transaction.objects.filter(user=user).count() == 2


@pytest.mark.django_db
def test_void_preserves_effects_but_excludes_them_from_balances(financial_setup):
    user, person, bank, _ = financial_setup
    created = create_expense(
        user=user,
        transaction_date=date(2026, 9, 24),
        person_id=person.pk,
        account_id=bank.pk,
        amount='25.00',
        description='Voided expense',
    )

    from .services import void_transaction

    void_transaction(user=user, transaction_id=created.pk)

    created.refresh_from_db()
    assert created.status == Transaction.Status.VOIDED
    assert created.effects.count() == 2
    assert person_position(user, person) == Decimal('0.00')
    assert bank_balance(user, bank) == Decimal('100.00')

    with pytest.raises(FinancialValidationError):
        void_transaction(user=user, transaction_id=created.pk)


@pytest.mark.django_db
def test_update_replaces_effects_on_the_same_transaction(financial_setup):
    user, person, bank, card = financial_setup
    created = create_expense(
        user=user,
        transaction_date=date(2026, 9, 24),
        person_id=person.pk,
        account_id=bank.pk,
        amount='25.00',
        description='Original expense',
    )

    updated = update_transaction(
        user=user,
        transaction_id=created.pk,
        transaction_type=Transaction.TransactionType.EXPENSE,
        transaction_date=date(2026, 9, 25),
        person_id=person.pk,
        account_id=card.pk,
        amount='10.00',
        description='Updated card expense',
    )

    assert updated.pk == created.pk
    assert updated.status == Transaction.Status.ACTIVE
    assert updated.effects.count() == 2
    assert bank_balance(user, bank) == Decimal('100.00')
    assert credit_used(user, card) == Decimal('10.00')
    assert person_position(user, person) == Decimal('-10.00')


@pytest.mark.django_db
def test_failed_update_rolls_back_original_transaction(financial_setup):
    user, person, bank, card = financial_setup
    created = create_expense(
        user=user,
        transaction_date=date(2026, 9, 24),
        person_id=person.pk,
        account_id=bank.pk,
        amount='25.00',
        description='Original expense',
    )

    with pytest.raises(FinancialValidationError):
        update_transaction(
            user=user,
            transaction_id=created.pk,
            transaction_type=Transaction.TransactionType.EXPENSE,
            transaction_date=date(2026, 9, 25),
            person_id=person.pk,
            account_id=card.pk,
            amount='101.00',
            description='Invalid replacement',
        )

    created.refresh_from_db()
    assert created.status == Transaction.Status.ACTIVE
    assert created.effects.count() == 2
    assert bank_balance(user, bank) == Decimal('75.00')
    assert person_position(user, person) == Decimal('-25.00')


@pytest.mark.django_db
def test_archive_blocks_new_transactions_and_restore_reactivates_records(financial_setup):
    user, person, bank, _ = financial_setup
    archive_person(user=user, person_id=person.pk)
    archive_account(user=user, account_id=bank.pk)

    with pytest.raises(FinancialValidationError):
        create_expense(
            user=user,
            transaction_date=date(2026, 9, 24),
            person_id=person.pk,
            account_id=bank.pk,
            amount='10.00',
            description='Archived attempt',
        )

    restore_person(user=user, person_id=person.pk)
    restore_account(user=user, account_id=bank.pk)
    created = create_expense(
        user=user,
        transaction_date=date(2026, 9, 24),
        person_id=person.pk,
        account_id=bank.pk,
        amount='10.00',
        description='Restored expense',
    )

    assert created.status == Transaction.Status.ACTIVE


@pytest.mark.django_db
def test_cash_payment_does_not_change_bank_balance(financial_setup):
    user, person, _, card = financial_setup
    create_expense(
        user=user,
        transaction_date=date(2026, 9, 24),
        person_id=person.pk,
        account_id=card.pk,
        amount='30.00',
        description='Card purchase',
    )

    payment = create_card_payment(
        user=user,
        transaction_date=date(2026, 9, 24),
        credit_card_id=card.pk,
        amount='10.00',
        payment_source=CardPaymentDetails.PaymentSource.CASH,
    )

    assert payment.card_payment_details.source_account is None
    assert credit_used(user, card) == Decimal('20.00')
    assert payment.effects.filter(effect_type=TransactionEffect.EffectType.BANK_BALANCE).count() == 0


@pytest.mark.django_db
def test_services_reject_cross_user_references(financial_setup):
    user, person, _, _ = financial_setup
    other_user = User.objects.create_user(email='other@example.com', password='test-password')
    other_bank = Account.objects.create(user=other_user, name='Other bank', account_type=Account.AccountType.BANK)

    with pytest.raises(OwnershipError):
        create_expense(
            user=user,
            transaction_date=date(2026, 9, 24),
            person_id=person.pk,
            account_id=other_bank.pk,
            amount='10.00',
            description='Cross-user attempt',
        )

    assert Transaction.objects.filter(user=user).count() == 0


@pytest.mark.django_db
def test_services_reject_balance_limit_violations(financial_setup):
    user, person, bank, card = financial_setup

    with pytest.raises(FinancialValidationError):
        create_expense(
            user=user,
            transaction_date=date(2026, 9, 24),
            person_id=person.pk,
            account_id=bank.pk,
            amount='101.00',
            description='Too large',
        )

    with pytest.raises(FinancialValidationError):
        create_expense(
            user=user,
            transaction_date=date(2026, 9, 24),
            person_id=person.pk,
            account_id=card.pk,
            amount='101.00',
            description='Too large',
        )

    assert Transaction.objects.filter(user=user).count() == 0
