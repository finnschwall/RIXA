# Generated by Django 4.1.5 on 2024-05-15 15:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account_managment', '0003_invitation'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitation',
            name='url',
            field=models.URLField(blank=True),
        ),
    ]