from django.db import models

class User(models.Model):

    telegram_token = models.IntegerField(
        'Идентифицатор пользователя в Телеграмме',
    )
    first_name = models.CharField(
        'Имя',
        max_length=50,
    )

    def __str__(self):
        return f"{self.first_name}"
