# Generated by Django 2.2.7 on 2019-11-05 13:19

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('department', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='FinancialYear',
            fields=[
                ('year', models.IntegerField(primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField()),
                ('proj_costing_id', models.CharField(max_length=50, null=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('internal', models.BooleanField(default=False)),
                ('start', models.DateField()),
                ('end', models.DateField()),
                ('status', models.CharField(choices=[('P', 'Preparation'), ('R', 'Review'), ('F', 'Funded'), ('X', 'Rejected')], max_length=1)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='rse.Client')),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('polymorphic_ctype', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_rse.project_set+', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
        ),
        migrations.CreateModel(
            name='RSE',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employed_from', models.DateField()),
                ('employed_until', models.DateField()),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SalaryBand',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('grade', models.IntegerField(default=1)),
                ('grade_point', models.IntegerField(default=1)),
                ('salary', models.DecimalField(decimal_places=2, max_digits=8)),
                ('increments', models.BooleanField(default=True)),
                ('year', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='rse.FinancialYear')),
            ],
        ),
        migrations.CreateModel(
            name='ServiceProject',
            fields=[
                ('project_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='rse.Project')),
                ('days', models.IntegerField(default=1)),
                ('rate', models.DecimalField(decimal_places=2, max_digits=8)),
                ('charged', models.BooleanField(default=True)),
                ('invoice_received', models.DateField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('rse.project',),
        ),
        migrations.CreateModel(
            name='SalaryGradeChange',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rse.RSE')),
                ('salary_band', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='rse.SalaryBand')),
            ],
        ),
        migrations.CreateModel(
            name='RSEAllocation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('percentage', models.FloatField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('start', models.DateField()),
                ('end', models.DateField()),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rse.Project')),
                ('rse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rse.RSE')),
            ],
        ),
        migrations.CreateModel(
            name='AllocatedProject',
            fields=[
                ('project_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='rse.Project')),
                ('percentage', models.FloatField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('overheads', models.DecimalField(decimal_places=2, max_digits=8)),
                ('salary_band', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='rse.SalaryBand')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('rse.project',),
        ),
    ]
