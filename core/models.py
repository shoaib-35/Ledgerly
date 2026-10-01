import uuid

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator
from django.db import models


class UserOwnedQuerySet(models.QuerySet):
    def for_user(self, user):
        if not getattr(user, 'is_authenticated', False):
            return self.none()
        return self.filter(user=user)


class UserOwnedManager(models.Manager.from_queryset(UserOwnedQuerySet)):
    pass


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The email address is required.')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_staff') is not True or extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_staff=True and is_superuser=True.')
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    username = None
    objects = UserManager()


class TimestampedModel(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserPreferences(TimestampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    currency = models.CharField(max_length=3, default='INR')
    date_format = models.CharField(max_length=32, default='DD/MM/YYYY')
    theme = models.CharField(max_length=16, default='SYSTEM')


class Person(TimestampedModel):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        ARCHIVED = 'ARCHIVED', 'Archived'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='people')
    name = models.CharField(max_length=120)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    objects = UserOwnedManager()

    class Meta:
        ordering = ('name',)
        indexes = [models.Index(fields=('user', 'status'))]


class Account(TimestampedModel):
    class AccountType(models.TextChoices):
        BANK = 'BANK', 'Bank'
        CREDIT_CARD = 'CREDIT_CARD', 'Credit card'

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        ARCHIVED = 'ARCHIVED', 'Archived'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts')
    name = models.CharField(max_length=120)
    account_type = models.CharField(max_length=16, choices=AccountType.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    objects = UserOwnedManager()

    class Meta:
        ordering = ('name',)
        indexes = [
            models.Index(fields=('user', 'account_type')),
            models.Index(fields=('user', 'status')),
        ]


class BankAccountDetails(TimestampedModel):
    account = models.OneToOneField(Account, on_delete=models.PROTECT, related_name='bank_details')
    opening_balance = models.DecimalField(
        max_digits=19,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )


class CreditCardDetails(TimestampedModel):
    account = models.OneToOneField(Account, on_delete=models.PROTECT, related_name='credit_card_details')
    credit_limit = models.DecimalField(max_digits=19, decimal_places=2, validators=[MinValueValidator(0.01)])
    opening_available_credit = models.DecimalField(
        max_digits=19,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(opening_available_credit__lte=models.F('credit_limit')),
                name='opening_credit_within_limit',
            ),
        ]


class Transaction(TimestampedModel):
    class TransactionType(models.TextChoices):
        EXPENSE = 'EXPENSE', 'Expense'
        RECEIVED = 'RECEIVED', 'Received'
        INCOME = 'INCOME', 'Income'
        BONUS = 'BONUS', 'Bonus'
        EXTRA = 'EXTRA', 'Extra'
        CARD_PAYMENT = 'CARD_PAYMENT', 'Card payment'
        TRANSFER = 'TRANSFER', 'Money transfer'

        @classmethod
        def bank_income_types(cls):
            """Money that lands in a bank account without touching any person's ledger."""
            return (cls.INCOME, cls.BONUS, cls.EXTRA)

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        VOIDED = 'VOIDED', 'Voided'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    date = models.DateField()
    person = models.ForeignKey(Person, on_delete=models.PROTECT, null=True, blank=True, related_name='transactions')
    account = models.ForeignKey(Account, on_delete=models.PROTECT, null=True, blank=True, related_name='transactions')
    transaction_type = models.CharField(max_length=16, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=19, decimal_places=2, validators=[MinValueValidator(0.01)])
    description = models.TextField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    objects = UserOwnedManager()

    class Meta:
        ordering = ('-date', '-created_at')
        indexes = [
            models.Index(fields=('user', 'date')),
            models.Index(fields=('user', 'status')),
            models.Index(fields=('user', 'transaction_type')),
            models.Index(fields=('person', 'date')),
            models.Index(fields=('account', 'date')),
        ]


class TransactionEffect(TimestampedModel):
    class EffectType(models.TextChoices):
        PERSON_BALANCE = 'PERSON_BALANCE', 'Person balance'
        BANK_BALANCE = 'BANK_BALANCE', 'Bank balance'
        CREDIT_USED = 'CREDIT_USED', 'Credit used'

    transaction = models.ForeignKey(Transaction, on_delete=models.PROTECT, related_name='effects')
    person = models.ForeignKey(Person, on_delete=models.PROTECT, null=True, blank=True, related_name='effects')
    account = models.ForeignKey(Account, on_delete=models.PROTECT, null=True, blank=True, related_name='effects')
    effect_type = models.CharField(max_length=16, choices=EffectType.choices)
    amount = models.DecimalField(max_digits=19, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    (models.Q(person__isnull=False) & models.Q(account__isnull=True))
                    | (models.Q(person__isnull=True) & models.Q(account__isnull=False))
                ),
                name='effect_exactly_one_target',
            ),
            models.CheckConstraint(condition=~models.Q(amount=0), name='effect_amount_nonzero'),
        ]
        indexes = [
            models.Index(fields=('transaction',)),
            models.Index(fields=('person', 'effect_type')),
            models.Index(fields=('account', 'effect_type')),
        ]


class MoneyTransferDetails(TimestampedModel):
    """Records the two account endpoints of a money transfer."""

    transaction = models.OneToOneField(Transaction, on_delete=models.PROTECT, related_name='money_transfer_details')
    source_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name='money_transfer_sources'
    )
    destination_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name='money_transfer_destinations'
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(source_account=models.F('destination_account')),
                name='transfer_source_differs_destination',
            ),
        ]


class CardPaymentDetails(TimestampedModel):
    class PaymentSource(models.TextChoices):
        BANK_ACCOUNT = 'BANK_ACCOUNT', 'Bank account'
        CASH = 'CASH', 'Cash'

    transaction = models.OneToOneField(Transaction, on_delete=models.PROTECT, related_name='card_payment_details')
    payment_source = models.CharField(max_length=16, choices=PaymentSource.choices)
    source_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='card_payment_sources',
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    (models.Q(payment_source='BANK_ACCOUNT', source_account__isnull=False))
                    | (models.Q(payment_source='CASH', source_account__isnull=True))
                ),
                name='payment_source_matches_account',
            ),
        ]
