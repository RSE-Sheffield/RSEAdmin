# Generated by Django 2.2.3 on 2019-11-22 15:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rse', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='client',
            options={'ordering': ['name']},
        ),
    ]
