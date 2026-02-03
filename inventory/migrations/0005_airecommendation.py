# Generated migration for AIRecommendation model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0004_notification'),
    ]

    operations = [
        migrations.CreateModel(
            name='AIRecommendation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recommendation_type', models.CharField(choices=[('increase_stock', 'Increase Stock'), ('raise_price', 'Raise Price'), ('apply_discount', 'Apply Discount'), ('reduce_orders', 'Reduce Orders'), ('reorder_soon', 'Reorder Soon'), ('monitor', 'Monitor')], max_length=20)),
                ('recommendation_text', models.TextField()),
                ('trend_score', models.FloatField()),
                ('stock_level', models.IntegerField()),
                ('suggested_value', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('suggested_quantity', models.IntegerField(blank=True, null=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('applied', 'Applied'), ('dismissed', 'Dismissed')], default='pending', max_length=10)),
                ('applied_by', models.CharField(blank=True, max_length=100, null=True)),
                ('applied_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.product')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='airecommendation',
            constraint=models.UniqueConstraint(fields=('product', 'recommendation_type', 'status'), name='unique_pending_recommendation'),
        ),
    ]