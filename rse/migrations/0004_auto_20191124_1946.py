# Generated by Django 2.2.3 on 2019-11-24 19:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rse', '0003_auto_20191124_1935'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rseallocation',
            name='deleted_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
