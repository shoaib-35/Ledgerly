from .models import UserPreferences

CURRENCY_SYMBOLS = {
    'INR': '\u20b9',
    'USD': '$',
    'EUR': '\u20ac',
    'GBP': '\u00a3',
    'AED': '\u062f.\u0625',
    'AUD': 'A$',
    'CAD': 'C$',
    'JPY': '\u00a5',
    'SGD': 'S$',
}

DATE_FORMATS = {
    'DD/MM/YYYY': 'd/m/Y',
    'MM/DD/YYYY': 'm/d/Y',
    'YYYY-MM-DD': 'Y-m-d',
}


def preferences(request):
    """Make the signed-in user's display preferences available to every template."""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {}
    prefs, _ = UserPreferences.objects.get_or_create(user=user)
    return {
        'preferences': prefs,
        'currency_symbol': CURRENCY_SYMBOLS.get(prefs.currency, prefs.currency + ' '),
        'date_format_django': DATE_FORMATS.get(prefs.date_format, 'd/m/Y'),
    }
