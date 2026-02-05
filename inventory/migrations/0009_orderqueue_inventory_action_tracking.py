# Generated migration for inventory action tracking

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('inventory', '0008_orderqueue_message_received_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderqueue',
            name='inventory_action',
            field=models.CharField(choices=[('none', 'No Action'), ('acknowledged', 'Acknowledged'), ('ordered', 'Ordered with Supplier')], default='none', max_length=20),
        ),
        migrations.AddField(
            model_name='orderqueue',
            name='inventory_action_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inventory_actions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='orderqueue',
            name='inventory_action_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='orderqueue',
            name='admin_marked_received',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='orderqueue',
            name='admin_marked_received_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]