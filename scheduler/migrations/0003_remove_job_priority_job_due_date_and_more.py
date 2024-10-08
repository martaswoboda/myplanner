# Generated by Django 5.1.1 on 2024-09-18 23:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0002_job_importance_job_urgency'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='job',
            name='priority',
        ),
        migrations.AddField(
            model_name='job',
            name='due_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='job',
            name='importance',
            field=models.IntegerField(choices=[(1, 'Low'), (2, 'Medium'), (3, 'High')], default=2),
        ),
        migrations.AlterField(
            model_name='job',
            name='urgency',
            field=models.IntegerField(choices=[(1, 'Low'), (2, 'Medium'), (3, 'High')], default=2),
        ),
    ]
