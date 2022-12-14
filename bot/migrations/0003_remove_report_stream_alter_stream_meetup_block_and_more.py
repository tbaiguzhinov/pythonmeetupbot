# Generated by Django 4.0.5 on 2022-07-29 08:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0002_meetup_alter_user_options_remove_user_telegram_token_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='report',
            name='stream',
        ),
        migrations.AlterField(
            model_name='stream',
            name='meetup',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='streams', to='bot.meetup', verbose_name='митап'),
        ),
        migrations.CreateModel(
            name='Block',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=50, verbose_name='название блока')),
                ('expert', models.ManyToManyField(blank=True, related_name='experting_blocks', to='bot.user', verbose_name='эксперт')),
                ('moderator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='moderating_blocks', to='bot.user', verbose_name='модератор')),
                ('stream', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocks', to='bot.stream', verbose_name='поток')),
            ],
            options={
                'verbose_name': 'блок',
                'verbose_name_plural': 'блоки',
            },
        ),
        migrations.AddField(
            model_name='report',
            name='block',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='bot.block', verbose_name='блок'),
            preserve_default=False,
        ),
    ]
