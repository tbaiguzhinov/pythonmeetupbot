# Generated by Django 4.0.5 on 2022-07-30 12:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0004_user_telegram_username_alter_donation_donated_by_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='report',
            name='ends_at',
        ),
        migrations.RemoveField(
            model_name='report',
            name='starts_at',
        ),
        migrations.AddField(
            model_name='block',
            name='ends_at',
            field=models.TimeField(null=True, verbose_name='время окончания'),
        ),
        migrations.AddField(
            model_name='block',
            name='starts_at',
            field=models.TimeField(null=True, verbose_name='время начала'),
        ),
        migrations.AlterField(
            model_name='user',
            name='job_title',
            field=models.CharField(blank=True, max_length=50, verbose_name='Название должности'),
        ),
    ]
