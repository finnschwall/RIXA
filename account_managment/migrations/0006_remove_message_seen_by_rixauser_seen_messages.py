# Generated by Django 4.2.16 on 2025-02-13 20:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account_managment', '0005_message'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='seen_by',
        ),
        migrations.AddField(
            model_name='rixauser',
            name='seen_messages',
            field=models.ManyToManyField(blank=True, related_name='seen_by', to='account_managment.message'),
        ),
    ]
