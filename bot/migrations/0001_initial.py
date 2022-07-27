# Generated by Django 4.0.5 on 2022-07-27 15:01

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telegram_token', models.IntegerField(verbose_name='Идентифицатор пользователя в Телеграмме')),
                ('first_name', models.CharField(max_length=50, verbose_name='Имя')),
            ],
        ),
    ]
