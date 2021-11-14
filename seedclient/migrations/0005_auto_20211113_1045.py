# Generated by Django 3.2.9 on 2021-11-13 10:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seedclient', '0004_speedingtorrent_speedpoint'),
    ]

    operations = [
        migrations.AddField(
            model_name='speedpoint',
            name='tracker',
            field=models.CharField(max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='speedingtorrent',
            name='name',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='speedingtorrent',
            name='status',
            field=models.CharField(max_length=32, null=True),
        ),
        migrations.AlterField(
            model_name='speedingtorrent',
            name='tracker',
            field=models.CharField(max_length=128, null=True),
        ),
    ]