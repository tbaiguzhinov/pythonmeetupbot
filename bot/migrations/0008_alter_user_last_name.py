# Generated by Django 4.0.5 on 2022-07-30 13:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0007_merge_20220730_1924'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='last_name',
            field=models.CharField(blank=True, max_length=30, null=True, verbose_name='фамилия'),
        ),
    ]