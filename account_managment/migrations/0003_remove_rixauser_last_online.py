# Generated by Django 4.2.16 on 2024-11-26 17:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account_managment', '0002_rixauser_last_online'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rixauser',
            name='last_online',
        ),
    ]
