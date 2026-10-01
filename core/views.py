import json
import base64
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from functools import wraps
from uuid import UUID

from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction as db_transaction
from django.http import JsonResponse
from django.db.models import Q
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import (
    Account,
    Person,
    Transaction,
    User,
    UserPreferences,
)
from .dashboard import dashboard_data
from .services import (
    FinancialValidationError,
    OwnershipError,
    account_summaries,
    archive_account,
    archive_person,
    bank_balance,
    balance_snapshots,
    create_card_payment,
    create_money_transfer,
    create_transaction,
    credit_available,
    credit_used,
    person_position,
    person_positions,
    restore_account,
    restore_person,
    restore_transaction,
    transaction_counts,
    update_account,
    update_person,
    update_transaction,
    void_transaction,
)
from .import_export import export_transactions, import_transactions, template_response


def _error(message, code='VALIDATION_ERROR', status=400):
    return JsonResponse({'error': {'code': code, 'message': message}}, status=status)


def _body(request):
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        raise FinancialValidationError('Request body must be valid JSON.')
    if not isinstance(payload, dict):
        raise FinancialValidationError('Request body must be a JSON object.')
    return payload


def _date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise FinancialValidationError('Date must use ISO-8601 format YYYY-MM-DD.') from exc


def _decimal(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise FinancialValidationError('Amount must be a valid monetary value.') from exc


def _uuid(value, field_name):
    try:
        return UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise FinancialValidationError(f'{field_name} must be a valid UUID.') from exc


def _encode_cursor(item):
    value = '|'.join((item.date.isoformat(), item.created_at.isoformat(), str(item.pk)))
    return base64.urlsafe_b64encode(value.encode()).decode()


def _decode_cursor(value):
    try:
        decoded = base64.urlsafe_b64decode(value.encode()).decode().split('|')
        if len(decoded) != 3:
            raise ValueError
        return date.fromisoformat(decoded[0]), datetime.fromisoformat(decoded[1]), UUID(decoded[2])
    except (ValueError, TypeError, UnicodeDecodeError) as exc:
        raise FinancialValidationError('Cursor is invalid.') from exc


def _handle_service_error(error):
    if isinstance(error, OwnershipError):
        return _error(str(error), 'NOT_FOUND', 404)
    return _error(str(error), 'VALIDATION_ERROR', 400)


def authenticated(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if not request.path.startswith('/api/'):
                return redirect('login-page')
            return _error('Authentication is required.', 'AUTHENTICATION_REQUIRED', 401)
        return view(request, *args, **kwargs)

    return wrapped


def _user_data(user):
    return {'id': str(user.pk), 'name': user.get_full_name() or user.email, 'email': user.email}


def _money_string(value):
    return format(value, '.2f')


PASSWORD_CRITERIA = (
    'At least 8 characters',
    'Not entirely numeric',
    "Not one of the 20,000 most common passwords",
    'Not too similar to your name or email',
)


# --------------------------------------------------------------------------- #
# JSON authentication API (unchanged contract - used by tests and any client)
# --------------------------------------------------------------------------- #
@require_http_methods(['POST'])
def signup(request):
    try:
        payload = _body(request)
        email = str(payload.get('email', '')).strip().lower()
        password = payload.get('password', '')
        name = str(payload.get('name', '')).strip()
        if not email or not password or not name:
            raise FinancialValidationError('Name, email, and password are required.')
        validate_password(password)
        with db_transaction.atomic():
            user = User.objects.create_user(email=email, password=password, first_name=name)
            UserPreferences.objects.create(user=user)
        login(request, user)
        return JsonResponse({'user': _user_data(user)}, status=201)
    except (FinancialValidationError, ValidationError) as error:
        message = '; '.join(error.messages) if isinstance(error, ValidationError) else str(error)
        return _error(message)
    except IntegrityError:
        return _error('An account with this email already exists.', 'EMAIL_TAKEN', 409)


@require_http_methods(['POST'])
def login_view(request):
    try:
        payload = _body(request)
        user = authenticate(
            request,
            email=str(payload.get('email', '')).strip().lower(),
            password=payload.get('password', ''),
        )
    except FinancialValidationError as error:
        return _error(str(error))
    if user is None:
        return _error('Invalid email or password.', 'INVALID_CREDENTIALS', 401)
    login(request, user)
    return JsonResponse({'user': _user_data(user)})


@require_http_methods(['POST'])
def logout_view(request):
    logout(request)
    return JsonResponse({'status': 'ok'})


@require_http_methods(['POST'])
@authenticated
def logout_page(request):
    logout(request)
    return redirect('login-page')


@require_http_methods(['GET'])
@authenticated
def current_user(request):
    return JsonResponse({'user': _user_data(request.user)})


# --------------------------------------------------------------------------- #
# HTML auth pages
# --------------------------------------------------------------------------- #
@require_http_methods(['GET', 'POST'])
def login_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    error = None
    if request.method == 'POST':
        user = authenticate(
            request,
            email=request.POST.get('email', '').strip().lower(),
            password=request.POST.get('password', ''),
        )
        if user is None:
            error = 'Invalid email or password.'
        else:
            login(request, user)
            return redirect('dashboard')
    return render(request, 'core/login.html', {'error': error})


@require_http_methods(['GET', 'POST'])
def signup_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    error = None
    form = {'name': '', 'email': ''}
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        name = request.POST.get('name', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        form = {'name': name, 'email': email}
        try:
            if not email or not name or not password:
                raise FinancialValidationError('Name, email, and password are required.')
            if password != password_confirm:
                raise FinancialValidationError('Passwords do not match.')
            validate_password(password, user=User(email=email, first_name=name))
            with db_transaction.atomic():
                user = User.objects.create_user(email=email, password=password, first_name=name)
                UserPreferences.objects.create(user=user)
            login(request, user)
            return redirect('dashboard')
        except (FinancialValidationError, ValidationError) as validation_error:
            error = (
                '; '.join(validation_error.messages)
                if isinstance(validation_error, ValidationError)
                else str(validation_error)
            )
        except IntegrityError:
            error = 'An account with this email already exists.'
    return render(
        request,
        'core/signup.html',
        {'error': error, 'form': form, 'password_criteria': PASSWORD_CRITERIA, 'active_nav': ''},
    )


# --------------------------------------------------------------------------- #
# Dashboard
# --------------------------------------------------------------------------- #
@require_http_methods(['GET'])
@authenticated
def dashboard_api(request):
    data = dashboard_data(request.user)
    summaries = data['account_summaries']
    positions = data['person_positions']
    return JsonResponse(
        {
            'greeting': data['greeting'],
            'financial_overview': {
                key: _money_string(value) for key, value in data['financial_overview'].items()
            },
            'family_position_overview': {
                key: _money_string(value) for key, value in data['family_position_overview'].items()
            },
            'accounts': [_account_data(account, request.user, summaries) for account in data['accounts']],
            'family_positions': [
                _person_data(person, request.user, positions) for person in data['people']
            ],
            'recent_transactions': [
                _transaction_data(transaction, request.user) for transaction in data['recent_transactions']
            ],
        }
    )


@require_http_methods(['GET'])
@authenticated
def dashboard_page(request):
    context = dashboard_data(request.user)
    context['active_nav'] = 'dashboard'
    return render(request, 'core/dashboard.html', context)


# --------------------------------------------------------------------------- #
# People
# --------------------------------------------------------------------------- #
@require_http_methods(['GET'])
@authenticated
def people_page(request):
    people_qs = list(request.user.people.all())
    positions = person_positions(request.user, [p for p in people_qs if p.status == Person.Status.ACTIVE])
    counts = transaction_counts(request.user)
    return render(
        request,
        'core/people.html',
        {
            'people': people_qs,
            'positions': positions,
            'counts': counts,
            'active_nav': 'people',
        },
    )


@require_http_methods(['GET', 'POST'])
@authenticated
def person_form_page(request):
    error = None
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            error = 'Name is required.'
        else:
            Person.objects.create(user=request.user, name=name)
            return redirect('people-page')
    return render(request, 'core/person_form.html', {'error': error, 'active_nav': 'people'})


@require_http_methods(['GET', 'POST'])
@authenticated
def person_edit_page(request, person_id):
    try:
        person = Person.objects.for_user(request.user).get(pk=person_id)
    except Person.DoesNotExist:
        return _error('Person was not found.', 'NOT_FOUND', 404)
    error = None
    if request.method == 'POST':
        try:
            update_person(user=request.user, person_id=person.pk, name=request.POST.get('name', ''))
            return redirect('people-page')
        except FinancialValidationError as service_error:
            error = str(service_error)
    return render(
        request, 'core/person_form.html', {'error': error, 'person': person, 'active_nav': 'people'}
    )


@require_http_methods(['POST'])
@authenticated
def person_archive_toggle_page(request, person_id):
    try:
        person = Person.objects.for_user(request.user).get(pk=person_id)
        if person.status == Person.Status.ACTIVE:
            archive_person(user=request.user, person_id=person.pk)
        else:
            restore_person(user=request.user, person_id=person.pk)
    except (Person.DoesNotExist, OwnershipError):
        return _error('Person was not found.', 'NOT_FOUND', 404)
    return redirect(request.POST.get('next') or 'people-page')


# --------------------------------------------------------------------------- #
# Accounts
# --------------------------------------------------------------------------- #
@require_http_methods(['GET'])
@authenticated
def accounts_page(request):
    accounts_qs = list(request.user.accounts.select_related('bank_details', 'credit_card_details').all())
    summaries = account_summaries(request.user, accounts_qs)
    counts = transaction_counts(request.user)
    return render(
        request,
        'core/accounts.html',
        {
            'accounts': accounts_qs,
            'summaries': summaries,
            'counts': counts,
            'active_nav': 'accounts',
        },
    )


@require_http_methods(['GET', 'POST'])
@authenticated
def account_form_page(request):
    error = None
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            account_type = request.POST.get('account_type')
            if not name or account_type not in Account.AccountType.values:
                raise FinancialValidationError('Name and account type are required.')
            with db_transaction.atomic():
                from .models import BankAccountDetails, CreditCardDetails

                account = Account.objects.create(user=request.user, name=name, account_type=account_type)
                if account_type == Account.AccountType.BANK:
                    opening_balance = _decimal(request.POST.get('opening_balance', '0'))
                    if opening_balance < 0:
                        raise FinancialValidationError('Opening balance cannot be negative.')
                    BankAccountDetails.objects.create(account=account, opening_balance=opening_balance)
                else:
                    credit_limit = _decimal(request.POST.get('credit_limit'))
                    opening_available = _decimal(request.POST.get('opening_available_credit', credit_limit))
                    if credit_limit <= 0 or opening_available < 0 or opening_available > credit_limit:
                        raise FinancialValidationError('Opening available credit must be within the credit limit.')
                    CreditCardDetails.objects.create(
                        account=account,
                        credit_limit=credit_limit,
                        opening_available_credit=opening_available,
                    )
            return redirect('accounts-page')
        except FinancialValidationError as service_error:
            error = str(service_error)
    return render(request, 'core/account_form.html', {'error': error, 'active_nav': 'accounts'})


@require_http_methods(['GET', 'POST'])
@authenticated
def account_edit_page(request, account_id):
    try:
        account = Account.objects.for_user(request.user).select_related(
            'bank_details', 'credit_card_details'
        ).get(pk=account_id)
    except Account.DoesNotExist:
        return _error('Account was not found.', 'NOT_FOUND', 404)
    error = None
    if request.method == 'POST':
        try:
            kwargs = {'user': request.user, 'account_id': account.pk, 'name': request.POST.get('name', '')}
            if account.account_type == Account.AccountType.BANK:
                kwargs['opening_balance'] = _decimal(request.POST.get('opening_balance'))
            else:
                kwargs['credit_limit'] = _decimal(request.POST.get('credit_limit'))
            update_account(**kwargs)
            return redirect('accounts-page')
        except FinancialValidationError as service_error:
            error = str(service_error)
    return render(
        request, 'core/account_form.html', {'error': error, 'account': account, 'active_nav': 'accounts'}
    )


@require_http_methods(['POST'])
@authenticated
def account_archive_toggle_page(request, account_id):
    try:
        account = Account.objects.for_user(request.user).get(pk=account_id)
        if account.status == Account.Status.ACTIVE:
            archive_account(user=request.user, account_id=account.pk)
        else:
            restore_account(user=request.user, account_id=account.pk)
    except (Account.DoesNotExist, OwnershipError):
        return _error('Account was not found.', 'NOT_FOUND', 404)
    return redirect(request.POST.get('next') or 'accounts-page')


# --------------------------------------------------------------------------- #
# Transactions
# --------------------------------------------------------------------------- #
def _apply_transaction_filters(queryset, get):
    person_id = get.get('person_id')
    account_id = get.get('account_id')
    account_type = get.get('account_type')
    transaction_type = get.get('transaction_type')
    status = get.get('status')
    date_from = get.get('date_from')
    date_to = get.get('date_to')
    amount_min = get.get('amount_min')
    amount_max = get.get('amount_max')
    search = get.get('search')
    if person_id:
        queryset = queryset.filter(person_id=_uuid(person_id, 'person_id'))
    if account_id:
        account_uuid = _uuid(account_id, 'account_id')
        queryset = queryset.filter(
            Q(account_id=account_uuid) | Q(money_transfer_details__source_account_id=account_uuid)
        ).distinct()
    if account_type:
        if account_type not in Account.AccountType.values:
            raise FinancialValidationError('account_type is invalid.')
        queryset = queryset.filter(account__account_type=account_type)
    if transaction_type:
        if transaction_type not in Transaction.TransactionType.values:
            raise FinancialValidationError('transaction_type is invalid.')
        queryset = queryset.filter(transaction_type=transaction_type)
    if status:
        if status not in Transaction.Status.values:
            raise FinancialValidationError('status is invalid.')
        queryset = queryset.filter(status=status)
    if date_from:
        queryset = queryset.filter(date__gte=_date(date_from))
    if date_to:
        queryset = queryset.filter(date__lte=_date(date_to))
    if amount_min:
        queryset = queryset.filter(amount__gte=_decimal(amount_min))
    if amount_max:
        queryset = queryset.filter(amount__lte=_decimal(amount_max))
    if search:
        queryset = queryset.filter(
            Q(description__icontains=search)
            | Q(person__name__icontains=search)
            | Q(account__name__icontains=search)
        )
    return queryset


@require_http_methods(['GET'])
@authenticated
def transactions_page(request):
    try:
        queryset = _apply_transaction_filters(
            request.user.transactions.select_related('person', 'account').prefetch_related('effects'),
            request.GET,
        )
    except FinancialValidationError as error:
        return _error(str(error))
    queryset = list(queryset)
    snapshots = balance_snapshots(request.user)

    rows = []
    for item in queryset:
        target_id = item.account_id or item.person_id
        rows.append({'transaction': item, 'balance_after': snapshots.get((item.pk, target_id))})

    active_filters = sum(
        1
        for key in (
            'person_id', 'account_id', 'account_type', 'transaction_type', 'status',
            'date_from', 'date_to', 'amount_min', 'amount_max', 'search',
        )
        if request.GET.get(key)
    )

    return render(
        request,
        'core/transactions.html',
        {
            'rows': rows,
            'filters': request.GET,
            'active_filters': active_filters,
            'people': request.user.people.all(),
            'accounts': request.user.accounts.all(),
            'transaction_types': tuple((value, label) for value, label in Transaction.TransactionType.choices if value != Transaction.TransactionType.TRANSFER),
            'active_nav': 'transactions',
        },
    )


@require_http_methods(['GET', 'POST'])
@authenticated
def transaction_import_page(request):
    error = None
    imported = duplicates = None
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            error = 'Choose a CSV, XLS, or XLSX file to import.'
        else:
            try:
                imported, duplicates = import_transactions(uploaded_file, request.user)
            except FinancialValidationError as service_error:
                error = str(service_error)
            else:
                return render(
                    request,
                    'core/transaction_import.html',
                    {
                        'imported': imported,
                        'duplicates': duplicates,
                        'active_nav': 'transactions',
                    },
                )
    return render(
        request,
        'core/transaction_import.html',
        {
            'error': error,
            'active_nav': 'transactions',
        },
    )


@require_http_methods(['GET'])
@authenticated
def transaction_export_page(request):
    file_format = request.GET.get('format', 'xlsx').lower()
    try:
        transactions_qs = (
            request.user.transactions
            .select_related('person', 'account')
            .prefetch_related(
                'money_transfer_details__source_account',
                'money_transfer_details__destination_account',
                'card_payment_details__source_account',
            )
            .order_by('date', 'created_at', 'id')
        )
        return export_transactions(transactions_qs, file_format)
    except FinancialValidationError as service_error:
        return _error(str(service_error))


@require_http_methods(['GET'])
@authenticated
def transaction_import_template(request):
    try:
        return template_response(request.GET.get('format', 'xlsx'))
    except FinancialValidationError as service_error:
        return _error(str(service_error))


def _active_form_options(user):
    return {
        'people': user.people.filter(status=Person.Status.ACTIVE),
        'accounts': user.accounts.filter(status=Account.Status.ACTIVE),
        'bank_accounts': user.accounts.filter(
            status=Account.Status.ACTIVE, account_type=Account.AccountType.BANK
        ),
        'credit_cards': user.accounts.filter(
            status=Account.Status.ACTIVE, account_type=Account.AccountType.CREDIT_CARD
        ),
    }


def _transaction_form_context(user, transaction=None, error=None):
    context = _active_form_options(user)
    context.update(
        {
            'transaction': transaction,
            'error': error,
            'transaction_types': Transaction.TransactionType.choices,
            'active_nav': 'transactions',
        }
    )
    return context


def _submit_transaction(request, current=None):
    """Shared create/update handler for the HTML transaction form."""
    transaction_type = request.POST.get('transaction_type')
    kwargs = dict(
        user=request.user,
        transaction_type=transaction_type,
        transaction_date=_date(request.POST.get('date')),
        person_id=request.POST.get('person_id') or None,
        account_id=request.POST.get('account_id') or None,
        amount=request.POST.get('amount'),
        description=request.POST.get('description', ''),
        payment_source=request.POST.get('payment_source') or None,
        source_account_id=request.POST.get('source_account_id') or None,
    )
    if current is None:
        return create_transaction(**kwargs)
    return update_transaction(transaction_id=current.pk, **kwargs)


@require_http_methods(['GET', 'POST'])
@authenticated
def transaction_form_page(request):
    error = None
    if request.method == 'POST':
        try:
            _submit_transaction(request)
            return redirect('transactions-page')
        except (FinancialValidationError, OwnershipError) as service_error:
            error = str(service_error)
    return render(request, 'core/transaction_form.html', _transaction_form_context(request.user, error=error))


@require_http_methods(['GET', 'POST'])
@authenticated
def money_transfer_form_page(request, transaction_id=None):
    error = None
    current = None
    if transaction_id is not None:
        try:
            current = (
                Transaction.objects.for_user(request.user)
                .select_related('money_transfer_details__source_account', 'money_transfer_details__destination_account')
                .get(pk=transaction_id, transaction_type=Transaction.TransactionType.TRANSFER)
            )
        except Transaction.DoesNotExist:
            return _error('Money transfer was not found.', 'NOT_FOUND', 404)

    if request.method == 'POST':
        try:
            kwargs = dict(
                user=request.user,
                transaction_date=_date(request.POST.get('date')),
                source_account_id=request.POST.get('source_account_id'),
                destination_account_id=request.POST.get('destination_account_id'),
                amount=request.POST.get('amount'),
                description=request.POST.get('description', ''),
            )
            if current is None:
                create_money_transfer(**kwargs)
            else:
                update_transaction(
                    user=request.user,
                    transaction_id=current.pk,
                    transaction_type=Transaction.TransactionType.TRANSFER,
                    transaction_date=kwargs['transaction_date'],
                    account_id=kwargs['destination_account_id'],
                    amount=kwargs['amount'],
                    description=kwargs['description'],
                    source_account_id=kwargs['source_account_id'],
                )
            return redirect('transactions-page')
        except (FinancialValidationError, OwnershipError) as service_error:
            error = str(service_error)

    return render(
        request,
        'core/money_transfer_form.html',
        {
            'transaction': current,
            'accounts': request.user.accounts.filter(status=Account.Status.ACTIVE),
            'error': error,
            'today': timezone.localdate(),
            'active_nav': 'transactions',
        },
    )


@require_http_methods(['GET', 'POST'])
@authenticated
def transaction_edit_page(request, transaction_id):
    try:
        current = Transaction.objects.for_user(request.user).get(pk=transaction_id)
    except Transaction.DoesNotExist:
        return _error('Transaction was not found.', 'NOT_FOUND', 404)
    error = None
    if request.method == 'POST':
        try:
            _submit_transaction(request, current=current)
            return redirect('transactions-page')
        except (FinancialValidationError, OwnershipError) as service_error:
            error = str(service_error)
    return render(request, 'core/transaction_form.html', _transaction_form_context(request.user, current, error))


@require_http_methods(['POST'])
@authenticated
def transaction_void_page(request, transaction_id):
    try:
        void_transaction(user=request.user, transaction_id=transaction_id)
    except (FinancialValidationError, OwnershipError) as service_error:
        return _error(
            str(service_error), 'VALIDATION_ERROR' if isinstance(service_error, FinancialValidationError) else 'NOT_FOUND'
        )
    return redirect('transactions-page')


@require_http_methods(['POST'])
@authenticated
def transaction_restore_page(request, transaction_id):
    try:
        restore_transaction(user=request.user, transaction_id=transaction_id)
    except (FinancialValidationError, OwnershipError) as service_error:
        return _error(
            str(service_error), 'VALIDATION_ERROR' if isinstance(service_error, FinancialValidationError) else 'NOT_FOUND'
        )
    return redirect('transactions-page')


@require_http_methods(['GET', 'POST'])
@authenticated
def card_payment_form_page(request):
    error = None
    if request.method == 'POST':
        try:
            create_card_payment(
                user=request.user,
                transaction_date=_date(request.POST.get('date')),
                credit_card_id=request.POST.get('credit_card_id'),
                amount=request.POST.get('amount'),
                payment_source=request.POST.get('payment_source'),
                source_account_id=request.POST.get('source_account_id') or None,
                description=request.POST.get('description', 'Card payment'),
            )
            return redirect('transactions-page')
        except (FinancialValidationError, OwnershipError) as service_error:
            error = str(service_error)
    return render(
        request,
        'core/card_payment_form.html',
        {
            'credit_cards': request.user.accounts.filter(
                status=Account.Status.ACTIVE, account_type=Account.AccountType.CREDIT_CARD
            ),
            'bank_accounts': request.user.accounts.filter(
                status=Account.Status.ACTIVE, account_type=Account.AccountType.BANK
            ),
            'error': error,
            'active_nav': 'transactions',
        },
    )


# --------------------------------------------------------------------------- #
# Profile
# --------------------------------------------------------------------------- #
@require_http_methods(['GET', 'POST'])
@authenticated
def profile_page(request):
    user = request.user
    profile_error = None
    password_error = None
    profile_success = None
    password_success = None

    if request.method == 'POST':
        form_type = request.POST.get('form_type', 'profile')

        if form_type == 'profile':
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip().lower()
            current_password = request.POST.get('profile_current_password', '')

            if not first_name:
                profile_error = 'First name is required.'
            elif not email:
                profile_error = 'Email address is required.'
            elif email != user.email.lower() and not user.check_password(current_password):
                profile_error = 'Enter your current password to change your email address.'
            elif User.objects.exclude(pk=user.pk).filter(email=email).exists():
                profile_error = 'That email address is already in use.'
            else:
                user.first_name = first_name
                user.last_name = last_name
                user.email = User.objects.normalize_email(email)
                user.save(update_fields=('first_name', 'last_name', 'email'))
                profile_success = 'Profile details updated successfully.'

        elif form_type == 'password':
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')

            if not user.check_password(current_password):
                password_error = 'Current password is incorrect.'
            elif new_password != confirm_password:
                password_error = 'New passwords do not match.'
            else:
                try:
                    validate_password(new_password, user=user)
                except ValidationError as exc:
                    password_error = ' '.join(exc.messages)
                else:
                    user.set_password(new_password)
                    user.save(update_fields=('password',))
                    update_session_auth_hash(request, user)
                    password_success = 'Password changed successfully.'

    return render(
        request,
        'core/profile.html',
        {
            'profile_error': profile_error,
            'password_error': password_error,
            'profile_success': profile_success,
            'password_success': password_success,
            'active_nav': '',
        },
    )


# --------------------------------------------------------------------------- #
# Settings
# --------------------------------------------------------------------------- #
@require_http_methods(['GET', 'POST'])
@authenticated
def settings_page(request):
    prefs, _ = UserPreferences.objects.get_or_create(user=request.user)
    error = None
    if request.method == 'POST':
        currency = request.POST.get('currency', '').strip().upper()
        date_format = request.POST.get('date_format', '').strip()
        theme = request.POST.get('theme', '').strip().upper()
        if len(currency) != 3 or not date_format or theme not in {'SYSTEM', 'LIGHT', 'DARK'}:
            error = 'Choose a valid currency, date format, and theme.'
        else:
            prefs.currency = currency
            prefs.date_format = date_format
            prefs.theme = theme
            prefs.save(update_fields=('currency', 'date_format', 'theme', 'updated_at'))
            return redirect('settings-page')
    return render(
        request,
        'core/settings.html',
        {
            'preferences': prefs,
            'currency_options': ('INR', 'USD', 'EUR', 'GBP', 'AED', 'AUD', 'CAD', 'JPY', 'SGD'),
            'archived_people': request.user.people.filter(status=Person.Status.ARCHIVED),
            'archived_accounts': request.user.accounts.filter(status=Account.Status.ARCHIVED),
            'voided_transactions': request.user.transactions.filter(status=Transaction.Status.VOIDED)[:20],
            'error': error,
            'active_nav': 'settings',
        },
    )


@require_http_methods(['POST'])
@authenticated
def restore_person_page(request, person_id):
    try:
        restore_person(user=request.user, person_id=person_id)
    except OwnershipError:
        return _error('Person was not found.', 'NOT_FOUND', 404)
    return redirect('settings-page')


@require_http_methods(['POST'])
@authenticated
def restore_account_page(request, account_id):
    try:
        restore_account(user=request.user, account_id=account_id)
    except OwnershipError:
        return _error('Account was not found.', 'NOT_FOUND', 404)
    return redirect('settings-page')


# --------------------------------------------------------------------------- #
# JSON data helpers (shared by page context and JSON API)
# --------------------------------------------------------------------------- #
def _person_data(person, user, positions=None):
    position = positions.get(person.pk) if positions is not None else person_position(user, person)
    return {
        'id': str(person.pk),
        'name': person.name,
        'status': person.status,
        'position': _money_string(position),
        'created_at': person.created_at.isoformat(),
        'updated_at': person.updated_at.isoformat(),
    }


@require_http_methods(['GET', 'POST'])
@authenticated
def people(request):
    if request.method == 'GET':
        return JsonResponse({'results': [_person_data(person, request.user) for person in request.user.people.all()]})
    try:
        payload = _body(request)
        name = str(payload.get('name', '')).strip()
        if not name:
            raise FinancialValidationError('Name is required.')
        person = Person.objects.create(user=request.user, name=name)
        return JsonResponse({'person': _person_data(person, request.user)}, status=201)
    except FinancialValidationError as error:
        return _error(str(error))


@require_http_methods(['GET', 'PATCH', 'POST'])
@authenticated
def person_detail(request, person_id):
    try:
        person = Person.objects.for_user(request.user).get(pk=person_id)
    except Person.DoesNotExist:
        return _error('Person was not found.', 'NOT_FOUND', 404)
    if request.method == 'GET':
        return JsonResponse({'person': _person_data(person, request.user)})
    if request.method == 'POST':
        action = request.GET.get('action')
        if action not in {'archive', 'restore'}:
            return _error('Unsupported person action.')
        try:
            person = archive_person(user=request.user, person_id=person.pk) if action == 'archive' else restore_person(
                user=request.user, person_id=person.pk
            )
            return JsonResponse({'person': _person_data(person, request.user)})
        except FinancialValidationError as error:
            return _handle_service_error(error)
    try:
        payload = _body(request)
        name = str(payload.get('name', '')).strip()
        if not name:
            raise FinancialValidationError('Name is required.')
        person.name = name
        person.save(update_fields=('name', 'updated_at'))
        return JsonResponse({'person': _person_data(person, request.user)})
    except FinancialValidationError as error:
        return _error(str(error))


@require_http_methods(['GET'])
@authenticated
def person_transactions(request, person_id):
    try:
        person = Person.objects.for_user(request.user).get(pk=person_id)
    except Person.DoesNotExist:
        return _error('Person was not found.', 'NOT_FOUND', 404)
    transactions_for_person = (
        Transaction.objects.for_user(request.user)
        .filter(person=person)
        .select_related('person', 'account')
        .prefetch_related('effects')
    )
    return JsonResponse(
        {'results': [_transaction_data(item, request.user) for item in transactions_for_person]}
    )


@require_http_methods(['GET'])
@authenticated
def person_position_api(request, person_id):
    try:
        person = Person.objects.for_user(request.user).get(pk=person_id)
    except Person.DoesNotExist:
        return _error('Person was not found.', 'NOT_FOUND', 404)
    return JsonResponse({'person_id': str(person.pk), 'position': _money_string(person_position(request.user, person))})


def _account_data(account, user, summaries=None):
    data = {
        'id': str(account.pk),
        'name': account.name,
        'account_type': account.account_type,
        'status': account.status,
        'created_at': account.created_at.isoformat(),
        'updated_at': account.updated_at.isoformat(),
    }
    summary = summaries.get(account.pk) if summaries is not None else None
    if account.account_type == Account.AccountType.BANK:
        data['opening_balance'] = str(account.bank_details.opening_balance)
        data['balance'] = str(summary['balance'] if summary else bank_balance(user, account))
    else:
        data['credit_limit'] = str(account.credit_card_details.credit_limit)
        data['opening_available_credit'] = str(account.credit_card_details.opening_available_credit)
        data['used_credit'] = str(summary['used'] if summary else credit_used(user, account))
        data['available_credit'] = str(summary['available'] if summary else credit_available(user, account))
    return data


@require_http_methods(['GET', 'POST'])
@authenticated
def accounts(request):
    if request.method == 'GET':
        return JsonResponse({'results': [_account_data(account, request.user) for account in request.user.accounts.all()]})
    try:
        from .models import BankAccountDetails, CreditCardDetails

        payload = _body(request)
        name = str(payload.get('name', '')).strip()
        account_type = payload.get('account_type')
        if not name or account_type not in Account.AccountType.values:
            raise FinancialValidationError('Name and a valid account type are required.')
        with db_transaction.atomic():
            account = Account.objects.create(user=request.user, name=name, account_type=account_type)
            if account_type == Account.AccountType.BANK:
                opening_balance = _decimal(payload.get('opening_balance', '0'))
                if opening_balance < 0:
                    raise FinancialValidationError('Opening balance cannot be negative.')
                BankAccountDetails.objects.create(account=account, opening_balance=opening_balance)
            else:
                credit_limit = _decimal(payload.get('credit_limit'))
                opening_available = _decimal(payload.get('opening_available_credit', credit_limit))
                if credit_limit <= 0 or opening_available < 0 or opening_available > credit_limit:
                    raise FinancialValidationError('Opening available credit must be within the credit limit.')
                CreditCardDetails.objects.create(
                    account=account,
                    credit_limit=credit_limit,
                    opening_available_credit=opening_available,
                )
        return JsonResponse({'account': _account_data(account, request.user)}, status=201)
    except FinancialValidationError as error:
        return _error(str(error))


@require_http_methods(['GET', 'PATCH', 'POST'])
@authenticated
def account_detail(request, account_id):
    try:
        account = Account.objects.for_user(request.user).get(pk=account_id)
    except Account.DoesNotExist:
        return _error('Account was not found.', 'NOT_FOUND', 404)
    if request.method == 'GET':
        return JsonResponse({'account': _account_data(account, request.user)})
    if request.method == 'POST':
        action = request.GET.get('action')
        if action not in {'archive', 'restore'}:
            return _error('Unsupported account action.')
        try:
            account = archive_account(user=request.user, account_id=account.pk) if action == 'archive' else restore_account(
                user=request.user, account_id=account.pk
            )
            return JsonResponse({'account': _account_data(account, request.user)})
        except FinancialValidationError as error:
            return _handle_service_error(error)
    try:
        payload = _body(request)
        name = str(payload.get('name', '')).strip()
        if not name:
            raise FinancialValidationError('Name is required.')
        account.name = name
        account.save(update_fields=('name', 'updated_at'))
        return JsonResponse({'account': _account_data(account, request.user)})
    except FinancialValidationError as error:
        return _error(str(error))


@require_http_methods(['GET'])
@authenticated
def account_transactions(request, account_id):
    try:
        account = Account.objects.for_user(request.user).get(pk=account_id)
    except Account.DoesNotExist:
        return _error('Account was not found.', 'NOT_FOUND', 404)
    transactions_for_account = (
        Transaction.objects.for_user(request.user)
        .filter(Q(account=account) | Q(money_transfer_details__source_account=account))
        .distinct()
        .select_related('person', 'account')
        .prefetch_related('effects', 'money_transfer_details')
    )
    return JsonResponse(
        {'results': [_transaction_data(item, request.user) for item in transactions_for_account]}
    )


def _transaction_data(transaction, user):
    data = {
        'id': str(transaction.pk),
        'date': transaction.date.isoformat(),
        'person_id': str(transaction.person_id) if transaction.person_id else None,
        'account_id': str(transaction.account_id) if transaction.account_id else None,
        'transaction_type': transaction.transaction_type,
        'amount': str(transaction.amount),
        'description': transaction.description,
        'status': transaction.status,
        'effects': [
            {
                'id': str(effect.pk),
                'person_id': str(effect.person_id) if effect.person_id else None,
                'account_id': str(effect.account_id) if effect.account_id else None,
                'effect_type': effect.effect_type,
                'amount': str(effect.amount),
            }
            for effect in transaction.effects.all()
        ],
    }
    if transaction.transaction_type == Transaction.TransactionType.TRANSFER:
        details = getattr(transaction, 'money_transfer_details', None)
        if details:
            data['source_account_id'] = str(details.source_account_id)
            data['destination_account_id'] = str(details.destination_account_id)
    return data


@require_http_methods(['GET', 'POST'])
@authenticated
def transactions(request):
    if request.method == 'GET':
        try:
            queryset = _apply_transaction_filters(
                request.user.transactions.select_related('person', 'account').prefetch_related('effects'),
                request.GET,
            )
            queryset = queryset.order_by('-date', '-created_at', '-id')
            cursor = request.GET.get('cursor')
            if cursor:
                cursor_date, cursor_created, cursor_id = _decode_cursor(cursor)
                queryset = queryset.filter(
                    Q(date__lt=cursor_date)
                    | Q(date=cursor_date, created_at__lt=cursor_created)
                    | Q(date=cursor_date, created_at=cursor_created, id__lt=cursor_id)
                )
            try:
                limit = min(max(int(request.GET.get('limit', '50')), 1), 100)
            except ValueError as exc:
                raise FinancialValidationError('limit must be a positive integer.') from exc
            items = list(queryset[: limit + 1])
            has_more = len(items) > limit
            items = items[:limit]
            return JsonResponse(
                {
                    'results': [_transaction_data(item, request.user) for item in items],
                    'next_cursor': _encode_cursor(items[-1]) if has_more else None,
                    'has_more': has_more,
                }
            )
        except FinancialValidationError as error:
            return _error(str(error))
    try:
        payload = _body(request)
        created = create_transaction(
            user=request.user,
            transaction_type=payload.get('transaction_type'),
            transaction_date=_date(payload.get('date')),
            person_id=payload.get('person_id'),
            account_id=payload.get('account_id'),
            amount=payload.get('amount'),
            description=payload.get('description', ''),
            payment_source=payload.get('payment_source'),
            source_account_id=payload.get('source_account_id'),
        )
        return JsonResponse({'transaction': _transaction_data(created, request.user)}, status=201)
    except (FinancialValidationError, OwnershipError) as error:
        return _handle_service_error(error)


@require_http_methods(['POST'])
@authenticated
def card_payments_api(request):
    try:
        payload = _body(request)
        created = create_card_payment(
            user=request.user,
            transaction_date=_date(payload.get('date')),
            credit_card_id=payload.get('credit_card_account_id', payload.get('credit_card_id')),
            amount=payload.get('amount'),
            payment_source=payload.get('payment_source_type', payload.get('payment_source')),
            source_account_id=payload.get('source_account_id'),
            description=payload.get('description', 'Card payment'),
        )
        return JsonResponse({'transaction': _transaction_data(created, request.user)}, status=201)
    except (FinancialValidationError, OwnershipError) as error:
        return _handle_service_error(error)


@require_http_methods(['POST'])
@authenticated
def money_transfers_api(request):
    try:
        payload = _body(request)
        created = create_money_transfer(
            user=request.user,
            transaction_date=_date(payload.get('date')),
            source_account_id=payload.get('source_account_id'),
            destination_account_id=payload.get('destination_account_id'),
            amount=payload.get('amount'),
            description=payload.get('description', 'Money transfer'),
        )
        return JsonResponse({'transaction': _transaction_data(created, request.user)}, status=201)
    except (FinancialValidationError, OwnershipError) as error:
        return _handle_service_error(error)


@require_http_methods(['GET', 'PATCH', 'POST'])
@authenticated
def transaction_detail(request, transaction_id):
    try:
        current = Transaction.objects.for_user(request.user).get(pk=transaction_id)
    except Transaction.DoesNotExist:
        return _error('Transaction was not found.', 'NOT_FOUND', 404)
    if request.method == 'GET':
        return JsonResponse({'transaction': _transaction_data(current, request.user)})
    if request.method == 'POST':
        action = request.GET.get('action')
        if action not in {'void', 'restore'}:
            return _error('Unsupported transaction action.')
        try:
            current = (
                void_transaction(user=request.user, transaction_id=current.pk)
                if action == 'void'
                else restore_transaction(user=request.user, transaction_id=current.pk)
            )
            return JsonResponse({'transaction': _transaction_data(current, request.user)})
        except FinancialValidationError as error:
            return _handle_service_error(error)
    try:
        payload = _body(request)
        updated = update_transaction(
            user=request.user,
            transaction_id=current.pk,
            transaction_type=payload.get('transaction_type', current.transaction_type),
            transaction_date=_date(payload.get('date', current.date.isoformat())),
            person_id=payload.get('person_id', current.person_id),
            account_id=payload.get('account_id', current.account_id),
            amount=payload.get('amount', current.amount),
            description=payload.get('description', current.description),
            payment_source=payload.get('payment_source'),
            source_account_id=payload.get('source_account_id'),
        )
        return JsonResponse({'transaction': _transaction_data(updated, request.user)})
    except (FinancialValidationError, OwnershipError) as error:
        return _handle_service_error(error)
