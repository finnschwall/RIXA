# Generated by Django 4.2.16 on 2024-11-01 16:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dashboard', '0002_chatconfiguration_chat_title'),
    ]

    operations = [
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.TextField(primary_key=True, serialize=False)),
                ('tracker_yaml', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now=True)),
                ('model_key', models.CharField(blank=True, help_text='Identifier of the LLM used', max_length=100, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conversations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Conversation',
                'verbose_name_plural': 'Conversations',
                'ordering': ['-timestamp'],
                'unique_together': {('id', 'user')},
            },
        ),
    ]
