# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-09-20 12:46
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rse', '0002_auto_20180919_1612'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rse',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL),
        ),
    ]
