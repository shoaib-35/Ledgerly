from datetime import date
from decimal import Decimal

import pytest

from core.models import Account, BankAccountDetails, CreditCardDetails, Transaction, MoneyTransferDetails
from core.services import create_money_transfer, bank_balance, credit_used, credit_available


@pytest.mark.django_db
def test_bank_to_bank_transfer_moves_both_balances(user):
    source = Account.objects.create(user=user, name='Source', account_type=Account.AccountType.BANK)
    destination = Account.objects.create(user=user, name='Destination', account_type=Account.AccountType.BANK)
    BankAccountDetails.objects.create(account=source, opening_balance=Decimal('1000.00'))
    BankAccountDetails.objects.create(account=destination, opening_balance=Decimal('250.00'))

    transfer = create_money_transfer(
        user=user,
        transaction_date=date(2026, 9, 25),
        source_account_id=source.pk,
        destination_account_id=destination.pk,
        amount='125.00',
        description='Move savings',
    )

    assert transfer.transaction_type == Transaction.TransactionType.TRANSFER
    assert bank_balance(user, source) == Decimal('875.00')
    assert bank_balance(user, destination) == Decimal('375.00')
    details = MoneyTransferDetails.objects.get(transaction=transfer)
    assert details.source_account_id == source.pk
    assert details.destination_account_id == destination.pk


@pytest.mark.django_db
def test_card_to_bank_transfer_uses_credit_and_increases_bank(user):
    card = Account.objects.create(user=user, name='Card', account_type=Account.AccountType.CREDIT_CARD)
    bank = Account.objects.create(user=user, name='Bank', account_type=Account.AccountType.BANK)
    CreditCardDetails.objects.create(account=card, credit_limit=Decimal('5000.00'), opening_available_credit=Decimal('5000.00'))
    BankAccountDetails.objects.create(account=bank, opening_balance=Decimal('100.00'))

    create_money_transfer(
        user=user,
        transaction_date=date(2026, 9, 25),
        source_account_id=card.pk,
        destination_account_id=bank.pk,
        amount='400.00',
    )

    assert credit_used(user, card) == Decimal('400.00')
    assert credit_available(user, card) == Decimal('4600.00')
    assert bank_balance(user, bank) == Decimal('500.00')


@pytest.mark.django_db
def test_transfer_rejects_same_account(user):
    account = Account.objects.create(user=user, name='Bank', account_type=Account.AccountType.BANK)
    BankAccountDetails.objects.create(account=account, opening_balance=Decimal('1000.00'))

    with pytest.raises(ValueError):
        create_money_transfer(
            user=user,
            transaction_date=date(2026, 9, 25),
            source_account_id=account.pk,
            destination_account_id=account.pk,
            amount='50.00',
        )
