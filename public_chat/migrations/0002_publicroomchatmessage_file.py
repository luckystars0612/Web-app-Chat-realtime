# Generated by Django 3.2.7 on 2021-11-07 04:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('public_chat', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='publicroomchatmessage',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to=''),
        ),
    ]
