# Generated by Django 3.2.19 on 2023-07-24 16:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('timetracking', '0002_auto_20200106_1046'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timesheetentry',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]