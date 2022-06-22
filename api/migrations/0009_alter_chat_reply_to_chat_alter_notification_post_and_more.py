# Generated by Django 4.0.4 on 2022-05-20 06:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_alter_post_video'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chat',
            name='reply_to_chat',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, to='api.chat'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='post',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.post'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='sender_profile',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sender_profile', to='api.profile'),
        ),
        migrations.AlterField(
            model_name='story',
            name='music',
            field=models.FileField(blank=True, null=True, upload_to='music'),
        ),
        migrations.AlterField(
            model_name='story',
            name='video',
            field=models.FileField(blank=True, null=True, upload_to='videos'),
        ),
    ]
