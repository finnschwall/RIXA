# Generated by Django 4.2.16 on 2025-01-20 17:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0006_alter_chatconfiguration_custom_user_settings'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='chat_mode',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
