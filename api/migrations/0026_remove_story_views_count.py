# Generated by Django 4.0.4 on 2022-05-30 10:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0025_story_like_profiles_story_view_profiles'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='story',
            name='views_count',
        ),
    ]
