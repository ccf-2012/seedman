# Generated by Django 3.2.8 on 2021-11-14 07:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seedclient', '0005_auto_20211113_1045'),
    ]

    operations = [
        migrations.AddField(
            model_name='speedpoint',
            name='sum_delta_download',
            field=models.BigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='speedpoint',
            name='sum_delta_upload',
            field=models.BigIntegerField(default=0),
        ),
    ]