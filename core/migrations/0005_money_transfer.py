# Generated manually because the build environment does not include Django.
import uuid

from django.db import migrations, models
from django.db.models import F


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_alter_transaction_transaction_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='transaction_type',
            field=models.CharField(
                choices=[
                    ('EXPENSE', 'Expense'),
                    ('RECEIVED', 'Received'),
                    ('INCOME', 'Income'),
                    ('BONUS', 'Bonus'),
                    ('EXTRA', 'Extra'),
                    ('CARD_PAYMENT', 'Card payment'),
                    ('TRANSFER', 'Money transfer'),
                ],
                max_length=16,
            ),
        ),
        migrations.CreateModel(
            name='MoneyTransferDetails',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('destination_account', models.ForeignKey(on_delete=models.deletion.PROTECT, related_name='money_transfer_destinations', to='core.account')),
                ('source_account', models.ForeignKey(on_delete=models.deletion.PROTECT, related_name='money_transfer_sources', to='core.account')),
                ('transaction', models.OneToOneField(on_delete=models.deletion.PROTECT, related_name='money_transfer_details', to='core.transaction')),
            ],
        ),
        migrations.AddConstraint(
            model_name='moneytransferdetails',
            constraint=models.CheckConstraint(
                condition=~models.Q(('source_account', F('destination_account'))),
                name='transfer_source_differs_destination',
            ),
        ),
    ]
