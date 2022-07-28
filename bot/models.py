from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class User(models.Model):
    telegram_id = models.IntegerField(
        'Идентификатор пользователя в Телеграмме',
        unique=True
    )
    first_name = models.CharField(
        'имя',
        max_length=30,
        blank=True
    )
    last_name = models.CharField(
        'фамилия',
        max_length=30,
        blank=True
    )
    company_name = models.CharField(
        'название компании',
        max_length=50,
        blank=True
    )
    job_title = models.CharField(
        'название компании',
        max_length=50,
        blank=True
    )
    email = models.EmailField(
        'электронная почта',
        blank=True
    )
    phone_number = PhoneNumberField(
        'номер телефона',
        blank=True,
        null=True
    )
    is_speaker = models.BooleanField(
        'является докладчиком',
        default=False,
        db_index=True
    )
    questionnaire_filled = models.BooleanField(
        'анкета заполнена',
        default=False,
        db_index=True
    )

    telegram_username = models.CharField(
        'логин в телеграмме',
        max_length=30,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Meetup(models.Model):
    title = models.CharField(
        'название митапа',
        max_length=100
    )
    date = models.DateField(
        'дата проведения',
        unique=True
    )
    participants = models.ManyToManyField(
        User,
        verbose_name='участники',
        related_name='meetups',
        blank=True
    )

    class Meta:
        verbose_name = 'митап'
        verbose_name_plural = 'митапы'

    def __str__(self):
        return f'{self.title} - {self.date}'


class Stream(models.Model):
    title = models.CharField(
        'название потока',
        max_length=50
    )
    meetup = models.ForeignKey(
        Meetup,
        related_name='streams',
        verbose_name='поток',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'поток'
        verbose_name_plural = 'потоки'

    def __str__(self):
        return f'{self.title}'


class Report(models.Model):
    title = models.CharField(
        'название доклада',
        max_length=50
    )
    meetup = models.ForeignKey(
        Meetup,
        related_name='reports',
        verbose_name='митап',
        on_delete=models.CASCADE
    )
    stream = models.ForeignKey(
        Stream,
        related_name='reports',
        verbose_name='поток',
        on_delete=models.SET_NULL
    )
    speaker = models.ForeignKey(
        User,
        related_name='reports',
        verbose_name='докладчик',
        on_delete=models.SET_NULL
    )
    starts_at = models.TimeField(
        'время начала',
        db_index=True
    )
    ends_at = models.TimeField(
        'время окончания',
        db_index=True
    )

    class Meta:
        verbose_name = 'доклад'
        verbose_name_plural = 'доклады'

    def __str__(self):
        return f'{self.title}, {self.starts_at} - {self.ends_at}'


class Donation(models.Model):
    sum = models.DecimalField(
        'сумма доната',
        max_digits=10,
        decimal_places=2,
        db_index=True
    )
    donated_at = models.DateTimeField(
        'дата и время доната',
        auto_now_add=True,
    )
    donor = models.ForeignKey(
        User,
        related_name='donations',
        verbose_name='от кого донат',
        on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = 'донат'
        verbose_name_plural = 'донаты'

    class Meta:
        verbose_name = 'поток'
        verbose_name_plural = 'потоки'

    def __str__(self):
        return f'{self.title}'


class Report(models.Model):
    title = models.CharField(
        'название доклада',
        max_length=50
    )
    stream = models.ForeignKey(
        Stream,
        related_name='reports',
        verbose_name='доклад',
        on_delete=models.SET_NULL,
        null= True
    )
    starts_at = models.TimeField(
        'время начала'
    )
    ends_at = models.TimeField(
        'время окончания'
    )
    speaker = models.ForeignKey(
        User,
        related_name='reports',
        verbose_name='докладчик',
        on_delete=models.SET_NULL,
        null= True
    )

    class Meta:
        verbose_name = 'доклад'
        verbose_name_plural = 'доклады'

    def __str__(self):
        return f'{self.title}, {self.starts_at} - {self.ends_at}'


class Donation(models.Model):
    sum = models.DecimalField(
        'сумма доната',
        max_digits=10,
        decimal_places=2
    )
    donated_at = models.DateTimeField(
        'дата и время доната',
        auto_now_add=True
    )
    donated_by = models.ForeignKey(
        User,
        related_name='donations',
        verbose_name='от кого донат',
        on_delete=models.SET_NULL,
        null=True
    )

    class Meta:
        verbose_name = 'донат'
        verbose_name_plural = 'донаты'

    def __str__(self):
        return f'{self.sum} рублей от ' \
               f'{self.donated_by.first_name} {self.donated_by.last_name}'


class Question(models.Model):
    text = models.TextField(
        'текст вопроса'
    )
    author = models.ForeignKey(
        User,
        related_name='asked_questions',
        verbose_name='автор вопроса',
        on_delete=models.SET_NULL,
        null= True
    )
    recipient = models.ForeignKey(
        User,
        related_name='received_questions',
        verbose_name='адресат вопроса',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'вопрос'
        verbose_name_plural = 'вопросы'

    def __str__(self):
        return f'вопрос для {self.recipient.first_name} {self.recipient.last_name}'

class Question(models.Model):
    text = models.TextField(
        'текст вопроса'
    )
    author = models.ForeignKey(
        User,
        related_name='asked_questions',
        verbose_name='автор вопроса',
        on_delete=models.SET_NULL
    )
    recipient = models.ForeignKey(
        User,
        related_name='received_questions',
        verbose_name='адресат вопроса',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'вопрос'
        verbose_name_plural = 'вопросы'

    def __str__(self):
        return f'вопрос для {self.recipient.first_name} {self.recipient.last_name}'
