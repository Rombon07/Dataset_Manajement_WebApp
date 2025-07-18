# Generated by Django 5.2.1 on 2025-06-19 07:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset', '0009_datasetrequest_dataset'),
    ]

    operations = [
        migrations.CreateModel(
            name='DatasetSent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sender_name', models.CharField(max_length=100)),
                ('dataset_id', models.IntegerField()),
                ('request_id', models.IntegerField()),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('status', models.CharField(blank=True, max_length=50, null=True)),
                ('file_url', models.URLField()),
                ('nama_model', models.CharField(max_length=255)),
                ('kebutuhan', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
