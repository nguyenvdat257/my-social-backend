# Generated by Django 4.0.4 on 2022-06-17 07:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0040_rename_reply_to_chat_chat_reply_to_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='chatreaction',
            old_name='chat',
            new_name='reply_to',
        ),
        migrations.RenameField(
            model_name='chatroomprofile',
            old_name='last_read_chat',
            new_name='last_seen',
        ),
    ]