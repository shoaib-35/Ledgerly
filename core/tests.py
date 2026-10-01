from decimal import Decimal

import pytest
from django.db import IntegrityError
from django.contrib.auth.models import AnonymousUser

from .models import Account, Person, Transaction, TransactionEffect, User


@pytest.mark.django_db
def test_financial_roots_are_owned_by_the_authenticated_user():
    first_user = User.objects.create_user(email='first@example.com', password='test-password')
    second_user = User.objects.create_user(email='second@example.com', password='test-password')
    Person.objects.create(user=first_user, name='First person')
    Account.objects.create(user=second_user, name='Second account', account_type=Account.AccountType.BANK)

    assert list(first_user.people.values_list('name', flat=True)) == ['First person']
    assert list(first_user.accounts.values_list('name', flat=True)) == []
    assert list(second_user.people.values_list('name', flat=True)) == []

    assert list(Person.objects.for_user(first_user).values_list('name', flat=True)) == ['First person']
    assert list(Person.objects.for_user(second_user).values_list('name', flat=True)) == []
    assert not Person.objects.for_user(AnonymousUser()).exists()


@pytest.mark.django_db
def test_effect_requires_exactly_one_financial_target():
    user = User.objects.create_user(email='owner@example.com', password='test-password')
    person = Person.objects.create(user=user, name='Family member')
    account = Account.objects.create(user=user, name='Bank', account_type=Account.AccountType.BANK)
    transaction = Transaction.objects.create(
        user=user,
        date='2026-09-24',
        person=person,
        account=account,
        transaction_type=Transaction.TransactionType.EXPENSE,
        amount=Decimal('10.00'),
        description='Test expense',
    )

    with pytest.raises(IntegrityError):
        TransactionEffect.objects.create(
            transaction=transaction,
            person=person,
            account=account,
            effect_type=TransactionEffect.EffectType.PERSON_BALANCE,
            amount=Decimal('-10.00'),
        )
