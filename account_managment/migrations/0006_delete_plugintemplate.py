# Generated by Django 4.1.5 on 2024-05-16 14:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account_managment', '0005_plugintemplate_delete_dashboardpermissions'),
    ]

    operations = [
        migrations.DeleteModel(
            name='PluginTemplate',
        ),
    ]