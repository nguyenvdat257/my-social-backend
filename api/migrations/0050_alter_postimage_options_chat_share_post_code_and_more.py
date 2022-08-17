# Generated by Django 4.0.4 on 2022-08-16 08:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0049_recentsearch_modified_alter_comment_reply_to'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='postimage',
            options={'ordering': ['order']},
        ),
        migrations.AddField(
            model_name='chat',
            name='share_post_code',
            field=models.CharField(blank=True, max_length=11, null=True),
        ),
        migrations.AddField(
            model_name='chat',
            name='share_post_img',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='chat',
            name='type',
            field=models.CharField(choices=[('N', 'normal'), ('S', 'share_post')], default='N', max_length=2),
        ),
        migrations.AlterField(
            model_name='chat',
            name='body',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='chat',
            name='chatroom',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chat_set', to='api.chatroom'),
        ),
        migrations.AlterField(
            model_name='chatroomprofile',
            name='chatroom',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chatroom_profile', to='api.chatroom'),
        ),
        migrations.AlterField(
            model_name='chatroomprofile',
            name='profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='profile_chatroom', to='api.profile'),
        ),
    ]