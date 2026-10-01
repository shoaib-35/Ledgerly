from django.utils import timezone

from .services import account_summaries, person_positions


def dashboard_data(user):
    accounts = list(user.accounts.filter(status='ACTIVE').select_related('bank_details', 'credit_card_details'))
    people = list(user.people.filter(status='ACTIVE'))
    recent_transactions = list(
        user.transactions.select_related('person', 'account').prefetch_related('effects')[:6]
    )

    summaries = account_summaries(user, accounts)
    positions = person_positions(user, people)
    total_held = sum((position for position in positions.values() if position > 0), start=0)
    total_receivables = sum((-position for position in positions.values() if position < 0), start=0)

    bank_balance = sum((summaries[a.pk]['balance'] for a in accounts if a.account_type == 'BANK'), start=0)
    credit_used = sum((summaries[a.pk]['used'] for a in accounts if a.account_type == 'CREDIT_CARD'), start=0)
    credit_available = sum(
        (summaries[a.pk]['available'] for a in accounts if a.account_type == 'CREDIT_CARD'), start=0
    )

    hour = timezone.localtime().hour
    time_of_day = 'morning' if hour < 12 else 'afternoon' if hour < 18 else 'evening'

    return {
        'greeting': f'Good {time_of_day},',
        'user_display_name': user.get_full_name() or user.email,
        'financial_overview': {
            'bank_balance': bank_balance,
            'credit_used': credit_used,
            'credit_available': credit_available,
        },
        'family_position_overview': {
            'held': total_held,
            'receivables': total_receivables,
            'current': total_held - total_receivables,
        },
        'accounts': accounts,
        'account_summaries': summaries,
        'people': people,
        'person_positions': positions,
        'recent_transactions': recent_transactions,
        'today': timezone.localdate(),
    }
