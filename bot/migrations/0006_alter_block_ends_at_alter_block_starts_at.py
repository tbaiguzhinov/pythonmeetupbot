# Generated by Django 4.0.5 on 2022-07-30 13:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0005_remove_report_ends_at_remove_report_starts_at_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='block',
            name='ends_at',
            field=models.TimeField(verbose_name='время окончания'),
        ),
        migrations.AlterField(
            model_name='block',
            name='starts_at',
            field=models.TimeField(verbose_name='время начала'),
        ),
    ]
