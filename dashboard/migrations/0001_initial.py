# Generated by Django 4.1.5 on 2024-05-16 14:45

import dashboard.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ChatConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('system_message', models.TextField()),
                ('included_plugins', models.JSONField(default=dashboard.models.generate_default_plugins)),
                ('document_tags', models.JSONField(default=dashboard.models.generate_default_document_tags)),
            ],
        ),
    ]