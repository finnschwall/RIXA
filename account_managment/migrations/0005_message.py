# Generated by Django 4.2.16 on 2025-02-13 20:32

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account_managment', '0004_rixauser_no_tracker_saving'),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expiration_date', models.DateTimeField()),
                ('seen_by', models.ManyToManyField(blank=True, related_name='seen_messages', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
