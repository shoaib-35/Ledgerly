from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Account,
    BankAccountDetails,
    CardPaymentDetails,
    CreditCardDetails,
    Person,
    Transaction,
    TransactionEffect,
    User,
    UserPreferences,
)


@admin.register(User)
class ExpenseTrackerUserAdmin(UserAdmin):
    """Uses Django's built-in password widget/hashing instead of a plain text field."""

    ordering = ('email',)
    list_display = ('email', 'first_name', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'first_name', 'password1', 'password2')}),
    )


admin.site.register(
    [
        Account,
        BankAccountDetails,
        CardPaymentDetails,
        CreditCardDetails,
        Person,
        Transaction,
        TransactionEffect,
        UserPreferences,
    ]
)
