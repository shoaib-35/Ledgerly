"""Financial business rules.

Every change to money goes through this module. Views never touch balances
directly: a transaction is described once (``_build_plan``), its signed effects
are written, and then every affected account is re-checked chronologically so
that no bank balance goes below zero and no card goes over its limit on *any*
date - not just today.
"""
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction
from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce

from .models import (
    Account,
    BankAccountDetails,
    CardPaymentDetails,
    MoneyTransferDetails,
    CreditCardDetails,
    Person,
    Transaction,
    TransactionEffect,
    User,
)

ZERO = Decimal('0.00')
MONEY_FIELD = DecimalField(max_digits=19, decimal_places=2)

TYPES = Transaction.TransactionType
ACCOUNT_TYPES = Account.AccountType
EFFECTS = TransactionEffect.EffectType

# Chronological order used everywhere a running balance is needed.
EFFECT_ORDER = (
    'transaction__date',
    'transaction__created_at',
    'transaction__id',
    'created_at',
    'id',
)


class FinancialValidationError(ValueError):
    pass


class OwnershipError(FinancialValidationError):
    pass


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def _require_user(user):
    if not isinstance(user, User) or not user.is_authenticated:
        raise OwnershipError('An authenticated user is required.')


def _money(value):
    try:
        amount = Decimal(str(value)).quantize(Decimal('0.01'))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise FinancialValidationError('Amount must be a valid monetary value.') from exc
    if amount <= ZERO:
        raise FinancialValidationError('Amount must be greater than zero.')
    return amount


def _description(value, default=None):
    text = (value or '').strip() or (default or '')
    if not text:
        raise FinancialValidationError('Description is required.')
    return text


def _owned(model, user, pk, label):
    try:
        return model.objects.for_user(user).get(pk=pk)
    except (model.DoesNotExist, ValidationError, ValueError, TypeError) as exc:
        raise OwnershipError(f'{label} is not available to this user.') from exc


def _owned_person(user, person_id):
    return _owned(Person, user, person_id, 'Person')


def _owned_account(user, account_id):
    return _owned(Account, user, account_id, 'Account')


def _require_active_person(person):
    if person.status != Person.Status.ACTIVE:
        raise FinancialValidationError('Archived people cannot be used for new transactions.')


def _require_active_account(account):
    if account.status != Account.Status.ACTIVE:
        raise FinancialValidationError('Archived accounts cannot be used for new transactions.')


def _day(value):
    return f'{value:%d %b %Y}'


# --------------------------------------------------------------------------- #
# Balances
# --------------------------------------------------------------------------- #
def _active_effect_total(*, user, account=None, person=None, effect_type):
    _require_user(user)
    target_filter = {'account': account} if account is not None else {'person': person}
    result = TransactionEffect.objects.filter(
        transaction__user=user,
        transaction__status=Transaction.Status.ACTIVE,
        effect_type=effect_type,
        **target_filter,
    ).aggregate(total=Coalesce(Sum('amount'), Value(ZERO), output_field=MONEY_FIELD))
    return result['total']


def bank_balance(user, account):
    if account.account_type != ACCOUNT_TYPES.BANK:
        raise FinancialValidationError('Balance requested for a non-bank account.')
    try:
        details = account.bank_details
    except BankAccountDetails.DoesNotExist as exc:
        raise FinancialValidationError('Bank account details are missing.') from exc
    return details.opening_balance + _active_effect_total(
        user=user, account=account, effect_type=EFFECTS.BANK_BALANCE
    )


def credit_used(user, account):
    if account.account_type != ACCOUNT_TYPES.CREDIT_CARD:
        raise FinancialValidationError('Credit usage requested for a non-credit-card account.')
    try:
        details = account.credit_card_details
    except CreditCardDetails.DoesNotExist as exc:
        raise FinancialValidationError('Credit card details are missing.') from exc
    opening_used = details.credit_limit - details.opening_available_credit
    return opening_used + _active_effect_total(
        user=user, account=account, effect_type=EFFECTS.CREDIT_USED
    )


def credit_available(user, account):
    try:
        details = account.credit_card_details
    except CreditCardDetails.DoesNotExist as exc:
        raise FinancialValidationError('Credit card details are missing.') from exc
    return details.credit_limit - credit_used(user, account)


def person_position(user, person):
    """Positive: the user holds this person's money. Negative: the person owes the user."""
    return _active_effect_total(user=user, person=person, effect_type=EFFECTS.PERSON_BALANCE)


def _effect_totals(user):
    """One grouped query for every active effect total, keyed by (target id, effect type)."""
    rows = (
        TransactionEffect.objects.filter(
            transaction__user=user, transaction__status=Transaction.Status.ACTIVE
        )
        .values('account_id', 'person_id', 'effect_type')
        .annotate(total=Sum('amount'))
    )
    return {(row['account_id'] or row['person_id'], row['effect_type']): row['total'] for row in rows}


def account_summaries(user, accounts):
    """Current figures for many accounts without one query per account.

    Returns ``{account_id: {...}}``. Bank rows carry ``balance``; credit-card
    rows carry ``limit``, ``used`` and ``available``.
    """
    _require_user(user)
    totals = _effect_totals(user)
    summaries = {}
    for account in accounts:
        if account.account_type == ACCOUNT_TYPES.BANK:
            try:
                details = account.bank_details
            except BankAccountDetails.DoesNotExist as exc:
                raise FinancialValidationError('Bank account details are missing.') from exc
            summaries[account.pk] = {
                'balance': details.opening_balance + totals.get((account.pk, EFFECTS.BANK_BALANCE), ZERO)
            }
        else:
            try:
                details = account.credit_card_details
            except CreditCardDetails.DoesNotExist as exc:
                raise FinancialValidationError('Credit card details are missing.') from exc
            used = (
                details.credit_limit
                - details.opening_available_credit
                + totals.get((account.pk, EFFECTS.CREDIT_USED), ZERO)
            )
            summaries[account.pk] = {
                'limit': details.credit_limit,
                'used': used,
                'available': details.credit_limit - used,
            }
    return summaries


def person_positions(user, people):
    _require_user(user)
    totals = _effect_totals(user)
    return {person.pk: totals.get((person.pk, EFFECTS.PERSON_BALANCE), ZERO) for person in people}


def transaction_counts(user):
    """Number of active transactions touching each account/person (one query)."""
    counts = {}
    rows = (
        Transaction.objects.for_user(user)
        .filter(status=Transaction.Status.ACTIVE)
        .values('account_id', 'person_id')
    )
    for row in rows:
        for key in (row['account_id'], row['person_id']):
            if key:
                counts[key] = counts.get(key, 0) + 1
    return counts


def balance_snapshots(user):
    """Running balance after every active transaction, in chronological order.

    Returns ``{(transaction_id, target_id): value}`` where ``target_id`` is an
    account or person id. Bank accounts store the balance, credit cards the
    *available* credit, people their position.
    """
    _require_user(user)
    accounts = {
        a.pk: a
        for a in Account.objects.for_user(user).select_related('bank_details', 'credit_card_details')
    }
    running = {}
    for account in accounts.values():
        if account.account_type == ACCOUNT_TYPES.BANK and hasattr(account, 'bank_details'):
            running[account.pk] = account.bank_details.opening_balance
        elif hasattr(account, 'credit_card_details'):
            details = account.credit_card_details
            running[account.pk] = details.credit_limit - details.opening_available_credit

    rows = (
        TransactionEffect.objects.filter(
            transaction__user=user, transaction__status=Transaction.Status.ACTIVE
        )
        .order_by(*EFFECT_ORDER)
        .values_list('transaction_id', 'account_id', 'person_id', 'amount')
    )
    snapshots = {}
    for transaction_id, account_id, person_id, amount in rows:
        target = account_id or person_id
        running[target] = running.get(target, ZERO) + amount
        value = running[target]
        account = accounts.get(account_id)
        if account is not None and account.account_type == ACCOUNT_TYPES.CREDIT_CARD:
            value = account.credit_card_details.credit_limit - value
        snapshots[(transaction_id, target)] = value
    return snapshots


def _assert_timeline(user, account):
    """Re-play an account's active effects in date order and reject impossible states."""
    effects = (
        TransactionEffect.objects.filter(
            transaction__user=user, transaction__status=Transaction.Status.ACTIVE, account=account
        )
        .select_related('transaction')
        .order_by(*EFFECT_ORDER)
    )
    if account.account_type == ACCOUNT_TYPES.BANK:
        running = account.bank_details.opening_balance
        for effect in effects:
            running += effect.amount
            if running < ZERO:
                raise FinancialValidationError(
                    f'{account.name} would go below zero on {_day(effect.transaction.date)}.'
                )
    else:
        details = account.credit_card_details
        running = details.credit_limit - details.opening_available_credit
        for effect in effects:
            running += effect.amount
            if running < ZERO:
                raise FinancialValidationError(
                    f'{account.name} would be paid more than the credit used on '
                    f'{_day(effect.transaction.date)}.'
                )
            if running > details.credit_limit:
                raise FinancialValidationError(
                    f'{account.name} would exceed its credit limit on {_day(effect.transaction.date)}.'
                )


def _assert_timelines(user, accounts):
    seen = set()
    for account in accounts:
        if account is not None and account.pk not in seen:
            seen.add(account.pk)
            _assert_timeline(user, account)


# --------------------------------------------------------------------------- #
# Describing a transaction (shared by create and edit)
# --------------------------------------------------------------------------- #
@dataclass
class _Plan:
    person: object = None
    account: object = None
    source_account: object = None
    payment_source: object = None
    effects: list = field(default_factory=list)  # (person, account, effect_type, amount)

    @property
    def accounts(self):
        return [a for a in (self.account, self.source_account) if a is not None]


def _lock(*accounts):
    """Lock account rows in a stable order (no-op on SQLite, real on PostgreSQL)."""
    ids = sorted({a.pk for a in accounts if a is not None}, key=str)
    if not ids:
        return {}
    return {a.pk: a for a in Account.objects.select_for_update().filter(pk__in=ids).order_by('pk')}


def _build_plan(user, *, transaction_type, amount, person_id, account_id, payment_source, source_account_id):
    if transaction_type not in TYPES.values:
        raise FinancialValidationError('Unsupported transaction type.')
    plan = _Plan()
    person = account = source = None

    if transaction_type == TYPES.TRANSFER:
        if not account_id or not source_account_id:
            raise FinancialValidationError('Choose both a source account and a destination account.')
        source = _owned_account(user, source_account_id)
        account = _owned_account(user, account_id)
        _require_active_account(source)
        _require_active_account(account)
        if source.pk == account.pk:
            raise FinancialValidationError('Source and destination accounts must be different.')

        locked = _lock(source, account)
        source = locked.get(source.pk, source)
        account = locked.get(account.pk, account)
        plan.person = None
        plan.account = account
        plan.source_account = source
        if source.account_type == ACCOUNT_TYPES.BANK:
            plan.effects.append((None, source, EFFECTS.BANK_BALANCE, -amount))
        else:
            plan.effects.append((None, source, EFFECTS.CREDIT_USED, amount))
        if account.account_type == ACCOUNT_TYPES.BANK:
            plan.effects.append((None, account, EFFECTS.BANK_BALANCE, amount))
        else:
            plan.effects.append((None, account, EFFECTS.CREDIT_USED, -amount))
        return plan

    if transaction_type in (TYPES.EXPENSE, TYPES.RECEIVED):
        if not person_id or not account_id:
            raise FinancialValidationError('Choose a person and an account.')
        person = _owned_person(user, person_id)
        _require_active_person(person)
    elif not account_id:
        raise FinancialValidationError('Choose an account.')

    account = _owned_account(user, account_id)
    _require_active_account(account)

    if transaction_type == TYPES.CARD_PAYMENT:
        if account.account_type != ACCOUNT_TYPES.CREDIT_CARD:
            raise FinancialValidationError('Card payments require a credit-card account.')
        if payment_source == CardPaymentDetails.PaymentSource.BANK_ACCOUNT:
            if not source_account_id:
                raise FinancialValidationError('A bank source account is required.')
            source = _owned_account(user, source_account_id)
            _require_active_account(source)
            if source.account_type != ACCOUNT_TYPES.BANK:
                raise FinancialValidationError('Payment source must be a bank account.')
        elif payment_source == CardPaymentDetails.PaymentSource.CASH:
            if source_account_id:
                raise FinancialValidationError('Cash payments cannot have a source account.')
        else:
            raise FinancialValidationError('Unsupported payment source.')
        plan.payment_source = payment_source
    elif transaction_type == TYPES.EXPENSE:
        if account.account_type not in (ACCOUNT_TYPES.BANK, ACCOUNT_TYPES.CREDIT_CARD):
            raise FinancialValidationError('Unsupported account type.')
    else:  # RECEIVED, INCOME, BONUS, EXTRA all land in a bank account
        if account.account_type != ACCOUNT_TYPES.BANK:
            raise FinancialValidationError(
                f'{TYPES(transaction_type).label} must be deposited into a bank account.'
            )

    locked = _lock(account, source)
    account = locked.get(account.pk, account)
    source = locked.get(source.pk, source) if source is not None else None
    plan.person, plan.account, plan.source_account = person, account, source

    if transaction_type == TYPES.EXPENSE:
        plan.effects.append((person, None, EFFECTS.PERSON_BALANCE, -amount))
        if account.account_type == ACCOUNT_TYPES.BANK:
            plan.effects.append((None, account, EFFECTS.BANK_BALANCE, -amount))
        else:
            plan.effects.append((None, account, EFFECTS.CREDIT_USED, amount))
    elif transaction_type == TYPES.RECEIVED:
        plan.effects.append((person, None, EFFECTS.PERSON_BALANCE, amount))
        plan.effects.append((None, account, EFFECTS.BANK_BALANCE, amount))
    elif transaction_type == TYPES.CARD_PAYMENT:
        plan.effects.append((None, account, EFFECTS.CREDIT_USED, -amount))
        if source is not None:
            plan.effects.append((None, source, EFFECTS.BANK_BALANCE, -amount))
    else:
        plan.effects.append((None, account, EFFECTS.BANK_BALANCE, amount))
    return plan


def _write_effects(transaction, plan):
    for person, account, effect_type, amount in plan.effects:
        TransactionEffect.objects.create(
            transaction=transaction,
            person=person,
            account=account,
            effect_type=effect_type,
            amount=amount,
        )
    if transaction.transaction_type == TYPES.TRANSFER:
        MoneyTransferDetails.objects.create(
            transaction=transaction,
            source_account=plan.source_account,
            destination_account=plan.account,
        )
    elif plan.payment_source:
        CardPaymentDetails.objects.create(
            transaction=transaction,
            payment_source=plan.payment_source,
            source_account=plan.source_account,
        )


# --------------------------------------------------------------------------- #
# Transactions
# --------------------------------------------------------------------------- #
def create_transaction(
    *,
    user,
    transaction_type,
    transaction_date,
    amount,
    description,
    person_id=None,
    account_id=None,
    payment_source=None,
    source_account_id=None,
):
    _require_user(user)
    amount = _money(amount)
    default = (
        'Card payment' if transaction_type == TYPES.CARD_PAYMENT
        else 'Money transfer' if transaction_type == TYPES.TRANSFER
        else None
    )
    description = _description(description, default)

    with db_transaction.atomic():
        plan = _build_plan(
            user,
            transaction_type=transaction_type,
            amount=amount,
            person_id=person_id,
            account_id=account_id,
            payment_source=payment_source,
            source_account_id=source_account_id,
        )
        created = Transaction.objects.create(
            user=user,
            date=transaction_date,
            person=plan.person,
            account=plan.account,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
        )
        _write_effects(created, plan)
        _assert_timelines(user, plan.accounts)
        return created


def create_expense(*, user, transaction_date, person_id, account_id, amount, description):
    return create_transaction(
        user=user,
        transaction_type=TYPES.EXPENSE,
        transaction_date=transaction_date,
        person_id=person_id,
        account_id=account_id,
        amount=amount,
        description=description,
    )


def create_received(*, user, transaction_date, person_id, account_id, amount, description):
    return create_transaction(
        user=user,
        transaction_type=TYPES.RECEIVED,
        transaction_date=transaction_date,
        person_id=person_id,
        account_id=account_id,
        amount=amount,
        description=description,
    )


def create_card_payment(
    *, user, transaction_date, credit_card_id, amount, payment_source, source_account_id=None, description='Card payment'
):
    return create_transaction(
        user=user,
        transaction_type=TYPES.CARD_PAYMENT,
        transaction_date=transaction_date,
        account_id=credit_card_id,
        amount=amount,
        description=description,
        payment_source=payment_source,
        source_account_id=source_account_id,
    )


def create_money_transfer(
    *, user, transaction_date, source_account_id, destination_account_id, amount, description='Money transfer'
):
    if source_account_id == destination_account_id:
        raise FinancialValidationError('Source and destination accounts must be different.')
    return create_transaction(
        user=user,
        transaction_type=TYPES.TRANSFER,
        transaction_date=transaction_date,
        account_id=destination_account_id,
        amount=amount,
        description=description,
        source_account_id=source_account_id,
    )


def update_transaction(
    *,
    user,
    transaction_id,
    transaction_type,
    transaction_date,
    person_id=None,
    account_id=None,
    amount,
    description,
    payment_source=None,
    source_account_id=None,
):
    """Replace a transaction's effects atomically, keeping the same record."""
    _require_user(user)
    amount = _money(amount)
    default = (
        'Card payment' if transaction_type == TYPES.CARD_PAYMENT
        else 'Money transfer' if transaction_type == TYPES.TRANSFER
        else None
    )
    description = _description(description, default)

    with db_transaction.atomic():
        current = _lock_transaction(user, transaction_id)
        if current.status == Transaction.Status.VOIDED:
            raise FinancialValidationError('Voided transactions cannot be edited. Restore it first.')

        old_accounts = _effect_accounts(current)
        current.effects.all().delete()
        CardPaymentDetails.objects.filter(transaction=current).delete()
        MoneyTransferDetails.objects.filter(transaction=current).delete()

        plan = _build_plan(
            user,
            transaction_type=transaction_type,
            amount=amount,
            person_id=person_id,
            account_id=account_id,
            payment_source=payment_source,
            source_account_id=source_account_id,
        )
        current.date = transaction_date
        current.person = plan.person
        current.account = plan.account
        current.transaction_type = transaction_type
        current.amount = amount
        current.description = description
        current.save()
        _write_effects(current, plan)
        _assert_timelines(user, old_accounts + plan.accounts)
        return current


def _lock_transaction(user, transaction_id):
    try:
        return Transaction.objects.for_user(user).select_for_update().get(pk=transaction_id)
    except (Transaction.DoesNotExist, ValidationError, ValueError, TypeError) as exc:
        raise OwnershipError('Transaction is not available to this user.') from exc


def _effect_accounts(transaction):
    return [effect.account for effect in transaction.effects.select_related('account') if effect.account]


def void_transaction(*, user, transaction_id):
    """Exclude a transaction from all balances (its record and effects stay)."""
    _require_user(user)
    with db_transaction.atomic():
        current = _lock_transaction(user, transaction_id)
        if current.status == Transaction.Status.VOIDED:
            raise FinancialValidationError('Transaction is already voided.')
        current.status = Transaction.Status.VOIDED
        current.save(update_fields=('status', 'updated_at'))
        _assert_timelines(user, _effect_accounts(current))
        return current


def restore_transaction(*, user, transaction_id):
    """Bring a voided transaction back; refused if it no longer fits the balances."""
    _require_user(user)
    with db_transaction.atomic():
        current = _lock_transaction(user, transaction_id)
        if current.status != Transaction.Status.VOIDED:
            raise FinancialValidationError('Only voided transactions can be restored.')
        current.status = Transaction.Status.ACTIVE
        current.save(update_fields=('status', 'updated_at'))
        _assert_timelines(user, _effect_accounts(current))
        return current


# --------------------------------------------------------------------------- #
# People and accounts
# --------------------------------------------------------------------------- #
def update_person(*, user, person_id, name):
    _require_user(user)
    name = (name or '').strip()
    if not name:
        raise FinancialValidationError('Name is required.')
    person = _owned_person(user, person_id)
    person.name = name
    person.save(update_fields=('name', 'updated_at'))
    return person


def _set_person_status(user, person_id, status):
    _require_user(user)
    person = _owned_person(user, person_id)
    person.status = status
    person.save(update_fields=('status', 'updated_at'))
    return person


def archive_person(*, user, person_id):
    return _set_person_status(user, person_id, Person.Status.ARCHIVED)


def restore_person(*, user, person_id):
    return _set_person_status(user, person_id, Person.Status.ACTIVE)


def update_account(*, user, account_id, name=None, opening_balance=None, credit_limit=None):
    """Rename an account, correct a bank's opening balance, or change a card's limit."""
    _require_user(user)
    with db_transaction.atomic():
        account = _lock(_owned_account(user, account_id)).popitem()[1]
        if name is not None:
            name = name.strip()
            if not name:
                raise FinancialValidationError('Name is required.')
            account.name = name
            account.save(update_fields=('name', 'updated_at'))

        if account.account_type == ACCOUNT_TYPES.BANK and opening_balance is not None:
            if opening_balance < ZERO:
                raise FinancialValidationError('Opening balance cannot be negative.')
            details = account.bank_details
            details.opening_balance = opening_balance
            details.save(update_fields=('opening_balance', 'updated_at'))

        if account.account_type == ACCOUNT_TYPES.CREDIT_CARD and credit_limit is not None:
            if credit_limit <= ZERO:
                raise FinancialValidationError('Credit limit must be greater than zero.')
            details = account.credit_card_details
            # Keep the credit already in use at the start unchanged: only headroom moves.
            new_opening_available = details.opening_available_credit + (credit_limit - details.credit_limit)
            if new_opening_available < ZERO:
                raise FinancialValidationError('The new limit is lower than the credit already in use.')
            details.credit_limit = credit_limit
            details.opening_available_credit = new_opening_available
            details.save(update_fields=('credit_limit', 'opening_available_credit', 'updated_at'))

        _assert_timeline(user, account)
        return account


def _set_account_status(user, account_id, status):
    _require_user(user)
    account = _owned_account(user, account_id)
    account.status = status
    account.save(update_fields=('status', 'updated_at'))
    return account


def archive_account(*, user, account_id):
    return _set_account_status(user, account_id, Account.Status.ARCHIVED)


def restore_account(*, user, account_id):
    return _set_account_status(user, account_id, Account.Status.ACTIVE)
