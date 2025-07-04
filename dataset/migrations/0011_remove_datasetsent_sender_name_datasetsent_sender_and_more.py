# Generated by Django 5.2.1 on 2025-06-19 07:39

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset', '0010_datasetsent'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='datasetsent',
            name='sender_name',
        ),
        migrations.AddField(
            model_name='datasetsent',
            name='sender',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='datasetsent',
            name='nama_model',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='datasetsent',
            name='name',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='datasetsent',
            name='status',
            field=models.CharField(choices=[('new', 'New'), ('in_progress', 'In Progress'), ('complete', 'Complete')], default='new', max_length=20),
        ),
    ]
