# Generated by Django 4.1.5 on 2023-04-18 11:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account_managment', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DashboardPermissions',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'permissions': (('request_GPU', 'Is user allowed to request GPU intensive resources'),),
                'managed': False,
                'default_permissions': (),
            },
        ),
        migrations.DeleteModel(
            name='GamePermissions',
        ),
    ]
