# Generated by Django 4.0.4 on 2022-05-28 14:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0022_post_api_post_code_19502b_idx'),
    ]

    operations = [
        migrations.AddField(
            model_name='commentlike',
            name='likes_count',
            field=models.IntegerField(default=0),
        ),
    ]
