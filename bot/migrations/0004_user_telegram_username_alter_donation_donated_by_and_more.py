# Generated by Django 4.0.5 on 2022-07-29 08:59

from django.db import migrations, models
import django.db.models.deletion
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0003_remove_report_stream_alter_stream_meetup_block_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='telegram_username',
            field=models.CharField(blank=True, max_length=30, null=True, verbose_name='логин в телеграмме'),
        ),
        migrations.AlterField(
            model_name='donation',
            name='donated_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='donations', to='bot.user', verbose_name='от кого донат'),
        ),
        migrations.AlterField(
            model_name='question',
            name='author',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='asked_questions', to='bot.user', verbose_name='автор вопроса'),
        ),
        migrations.AlterField(
            model_name='report',
            name='block',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reports', to='bot.block', verbose_name='доклад'),
        ),
        migrations.AlterField(
            model_name='report',
            name='speaker',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reports', to='bot.user', verbose_name='докладчик'),
        ),
        migrations.AlterField(
            model_name='user',
            name='phone_number',
            field=phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128, null=True, region=None, verbose_name='номер телефона'),
        ),
    ]
