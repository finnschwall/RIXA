# Generated by Django 4.2.16 on 2024-11-26 17:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account_managment', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='rixauser',
            name='last_online',
            field=models.DateTimeField(auto_now=True),
        ),
    ]