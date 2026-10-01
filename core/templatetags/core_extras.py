from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
def money(value, symbol):
    """Format a Decimal/string amount with the user's currency symbol, e.g. '1,234.00' -> '\u20b91,234.00'."""
    if value in (None, ''):
        return ''
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return f'{symbol}{value}'
    formatted = f'{amount:,.2f}'
    if amount < 0:
        return f'-{symbol}{formatted[1:]}'
    return f'{symbol}{formatted}'


@register.filter
def position_label(value):
    """-25.00 -> 'Receivable', 30.00 -> 'Held', 0 -> 'Settled' (sign only, no currency)."""
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return ''
    if amount > 0:
        return 'Held'
    if amount < 0:
        return 'Receivable'
    return 'Settled'


@register.filter
@stringfilter
def initial(value):
    return value[:1].upper() if value else '?'


@register.filter
def get_item(mapping, key):
    """Look up a dict value by key inside a template (mapping|get_item:key)."""
    if mapping is None:
        return None
    return mapping.get(key)


@register.filter
def abs_money(value, symbol):
    if value in (None, ''):
        return ''
    try:
        amount = abs(float(value))
    except (TypeError, ValueError):
        return ''
    return f'{symbol}{amount:,.2f}'
