# Generated by Django 4.0.4 on 2022-07-04 09:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0046_profile_show_activity_alter_profile_email'),
    ]

    operations = [
        migrations.RenameField(
            model_name='profile',
            old_name='type',
            new_name='account_type',
        ),
    ]
