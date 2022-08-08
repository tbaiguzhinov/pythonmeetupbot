import json
import logging
import random

import requests
from django.conf import settings
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, Update
from telegram import error as telegram_error
from telegram.ext import CallbackContext, ConversationHandler

from bot.models import Block, Meetup, Report, Stream, User, Donation
from bot.static_text import greetings_message

START, HANDLE_MENU, HANDLE_PROGRAMS,\
    HANDLE_FORM, HANDLE_QUESTION, HANDLE_STREAM,\
    HANDLE_BLOCK, SEND_QUESTION, HANDLE_DONATION, CLOSE = range(10)

logger = logging.getLogger(__name__)


def create_greetings_menu(user_exists):
    keyboard = []
    programs_button = [InlineKeyboardButton('Программа', callback_data='programs')]
    keyboard.append(programs_button)
    questions_keyboard = [InlineKeyboardButton('Вопросы спикерам', callback_data='questions')]
    keyboard.append(questions_keyboard)
    if not user_exists:
        form_keyboard = [InlineKeyboardButton('Заполнить анкету', callback_data='form')]
        keyboard.append(form_keyboard)
    else:
        meeting_keyboard = [InlineKeyboardButton('Хочу знакомиться!', callback_data='meeting')]
        keyboard.append(meeting_keyboard)
    donation_button = [InlineKeyboardButton('Поддержать проект', callback_data='donation')]
    keyboard.append(donation_button)
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def create_menu(products):
    keyboard = []
    callbackdata, items = products
    for product in items:
        product_button = [InlineKeyboardButton(product.__str__(), callback_data=f'{callbackdata}_{product.id}')]
        keyboard.append(product_button) 
    back_button = [InlineKeyboardButton('Назад', callback_data='back')]
    keyboard.append(back_button)
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def start(update: Update, context: CallbackContext) -> int:
    clean_message(update, context)
    user_exists = User.objects.filter(telegram_id=update.effective_user.id).exists()
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text=greetings_message,
        reply_markup=create_greetings_menu(user_exists)
        )
    return HANDLE_MENU


def stream_handle_menu(update: Update, context: CallbackContext) -> int:
    clean_message(update, context)
    query = update.callback_query.data
    entity, stream_id = query.split('_')
    if entity == 'reports':
        stream = Stream.objects.get(id=int(stream_id))
        blocks = stream.blocks.all()
        program = ('blockreport', blocks)
        context.bot.send_message(
            chat_id=update.effective_message.chat_id,
            text='Выберите интересующий вас блок докладов',
            reply_markup=create_menu(program)
        )
        return HANDLE_BLOCK


def question_stream_handle_menu(update: Update, context: CallbackContext) -> int:
    clean_message(update, context)
    active_meetup = Meetup.objects.get(status=Meetup.OPEN)
    streams = active_meetup.streams.all()
    streams = ('stream', list(streams))
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text='Пожалуйста выберите поток',
        reply_markup=create_menu(streams)
    )
    return HANDLE_QUESTION


def handle_block_reports(update: Update, context: CallbackContext):
    clean_message(update, context)
    keyboard = []
    query = update.callback_query.data
    entity, stream_id = query.split('_')
    block = Block.objects.get(id=int(stream_id))
    reports = block.reports.all()
    rep_message = f'{block.starts_at}-{block.ends_at} Блок "{block.title}"\n\n'
    for report in reports:
        rep_message += form_report_message(report)
    if block.moderator:
        block_message = f'\nМодератор блока: {report.block.moderator.__str__()}'
        rep_message = rep_message + block_message
    if block.expert.all():
        experts = [expert for expert in report.block.expert.all()]
        all_experts = '\n'.join(str(expert) for expert in experts)
        expert_message = f'\nЭксперты блока: {all_experts}'
        rep_message = rep_message + expert_message
    back_button = [InlineKeyboardButton('Назад', callback_data='back')]
    keyboard.append(back_button)
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text=rep_message,
        reply_markup=reply_markup
    )
    return HANDLE_BLOCK


def form_report_message(report):
    report_message = f'Название доклада: {report.title}\nСпикер доклада:{report.speaker}\n\n'
    return report_message


def program_handle_menu(update: Update, context: CallbackContext) -> int:
    reports = Report.objects.all()
    streams = [report.block.stream for report in reports]
    current_streams = set(stream for stream in streams if stream.meetup.status == 'OP')
    program = ('reports', current_streams)
    clean_message(update, context)
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text='Пожалуйста выберите поток необходимой программы',
        reply_markup=create_menu(program)
        )
    return HANDLE_STREAM


def select_speaker_menu(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    entity, stream_id = query.data.split('_')
    blocks = Block.objects.filter(stream_id=stream_id)
    block_ids = [block.id for block in blocks]
    reports = Report.objects.filter(block_id__in=block_ids).select_related('speaker')
    keyboard = []
    for report in reports:
        try:
            speaker_details = f'{report.speaker.first_name} {report.speaker.last_name}' \
                          f', {report.speaker.job_title}, {report.speaker.company_name}' \
                          f' - {report.title}'
            product_button = [InlineKeyboardButton(
                speaker_details,
                callback_data=f'speaker_{report.speaker.telegram_id}'
            )]
            keyboard.append(product_button)
        except AttributeError:
            back_button = [InlineKeyboardButton(
                f'Пока на докладе {report.title} нет зарегистрированных спикеров',
                callback_data='back'
            )]
            keyboard.append(back_button)

    back_button = [InlineKeyboardButton('Назад', callback_data='back')]
    keyboard.append(back_button)
    reply_markup = InlineKeyboardMarkup(keyboard)
    clean_message(update, context)
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text='Пожалуйста, выберите спикера',
        reply_markup=reply_markup
        )
    return HANDLE_QUESTION


def save_chosen_speaker(update: Update, context: CallbackContext) -> int:
    clean_message(update, context)
    query = update.callback_query
    entity, speaker_id = query.data.split('_')
    user_data = context.user_data
    user_data['speaker_to_ask_id'] = speaker_id
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text='Введите вопрос',
    )
    return SEND_QUESTION


def send_message_to_speaker(update: Update, context: CallbackContext) -> int:
    question_text = update.message.text
    current_user = User.objects.get(telegram_id=update.effective_message.chat_id)
    current_user_details = f'{current_user.first_name} {current_user.last_name}, ' \
                           f'{current_user.job_title} at {current_user.company_name}:\n'
    speaker_to_ask_id = context.user_data.pop('speaker_to_ask_id')
    try:
        context.bot.send_message(
            chat_id=speaker_to_ask_id,
            text=current_user_details + question_text,
        )
    except telegram_error.BadRequest as e:
        logger.exception(e)
    user_exists = User.objects.filter(telegram_id=update.effective_user.id).exists()
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text='Спасибо за ваш вопрос!',
        reply_markup=create_greetings_menu(user_exists)
    )
    return HANDLE_MENU


def meeting_handle(update: Update, context: CallbackContext) -> int:
    users = User.objects.exclude(telegram_id=update.effective_user.id)
    random_user = random.choice(users)
    text = f'Имя: {random_user.first_name} {random_user.last_name} \n\
        Должность и компания: {random_user.job_title}, {random_user.company_name} \n\
        Имя пользователя: @{random_user.telegram_username}'
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text=text,
        reply_markup=create_greetings_menu(True)
    )
    return HANDLE_MENU


def form_handle(update: Update, context: CallbackContext):
    clean_message(update, context)
    user_data = context.user_data
    user_data['poll_questions'] = read_poll_questions()
    user_data['answers'] = []
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text=user_data['poll_questions'].pop('name'),
        )
    return HANDLE_FORM


def ask_form_questions(update: Update, context: CallbackContext):
    user_data = context.user_data
    if user_data['poll_questions']:
        for question in user_data['poll_questions']:
            user_data['answers'].extend([update.message.text])
            context.bot.send_message(
                chat_id=update.effective_message.chat_id,
                text=user_data['poll_questions'].pop(question),
                )
            return HANDLE_FORM
    else:
        user_data['answers'].extend([update.message.text])
        name, company, position, email = user_data['answers']
        try:
            first_name, last_name = name.split(' ')
        except ValueError:
            first_name = name
            last_name = None
        User.objects.create(
            first_name=first_name,
            last_name=last_name,
            company_name=company,
            job_title=position,
            email=email,
            telegram_id=update.effective_user.id,
            telegram_username=update.effective_user.username,
            questionnaire_filled=True,
            chat_id=update.effective_message.chat_id,
            meetups=Meetup.objects.filter(status='OP')
        )
        context.bot.send_message(
                chat_id=update.effective_message.chat_id,
                text='Опрос окончен, спасибо за участие!',
                reply_markup=create_greetings_menu(True)
                )
        return HANDLE_MENU


def select_amount_to_donate_menu(update: Update, context: CallbackContext) -> None:
    keyboard = []
    donation_amounts = [100, 150, 250, 500, 750, 1000]
    for donation_amount in donation_amounts:
        donation_button = [InlineKeyboardButton(
            donation_amount,
            callback_data=f'donation_{donation_amount}'
        )]
        keyboard.append(donation_button)
    back_button = [InlineKeyboardButton('Назад', callback_data='back')]
    keyboard.append(back_button)
    reply_markup = InlineKeyboardMarkup(keyboard)
    clean_message(update, context)
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text='Пожалуйста, выберите сумму:',
        reply_markup=reply_markup
    )
    return HANDLE_DONATION


def send_donation_invoice(update: Update, context: CallbackContext) -> None:
    clean_message(update, context)
    query = update.callback_query.data
    active_meetup = Meetup.objects.get(status=Meetup.OPEN)
    entity, donation_amount = query.split('_')
    chat_id = update.effective_message.chat_id
    title = 'Поддержать митап'
    description = f'Поддержать организаторов митапа {active_meetup.title} на сумму в {donation_amount} рублей'
    payload = f'{active_meetup.title}_donation'
    provider_token = settings.PAYMENT_SYSTEM_TOKEN
    currency = 'RUB'
    prices = [LabeledPrice('Donation', int(donation_amount) * 100)]
    context.bot.send_invoice(
        chat_id, title, description, payload, provider_token, currency, prices
    )
    user_data = context.user_data
    user_data['donation_amount'] = donation_amount
    return HANDLE_DONATION


def precheckout_callback(update: Update, context: CallbackContext) -> None:
    query = update.pre_checkout_query
    active_meetup = Meetup.objects.get(status=Meetup.OPEN)
    if query.invoice_payload != f'{active_meetup.title}_donation':
        query.answer(ok=False, error_message="Что-то пошло не так...")
    else:
        query.answer(ok=True)


def successful_donation_callback(update: Update, context: CallbackContext) -> None:
    current_user = User.objects.get(telegram_id=update.effective_message.chat_id)
    donation_amount = context.user_data.pop('donation_amount')
    Donation.objects.create(donated_by=current_user, sum=donation_amount)
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text='Спасибо за вашу поддержку!',
        reply_markup=create_greetings_menu(True)
    )
    return HANDLE_MENU


def read_poll_questions():
    with open('questions_to_clients.txt', 'r', encoding='utf8') as file_handler:
        poll_questions = json.load(file_handler)
    return poll_questions


def clean_message(update: Update, context: CallbackContext):
    message_id = update.effective_message.message_id
    chat_id = update.effective_message.chat_id
    context.bot.delete_message(chat_id=chat_id, message_id=message_id)


def handle_error(update: Update, context: CallbackContext):
    """Log Errors caused by Updates."""
    logger.warning(
        f'Update {update} caused error {context.error},\
        traceback {context.error.__traceback__}'
        )


def end_conversation(update: Update, context: CallbackContext):
    update.message.reply_text(
        'Пока!'
        )
    return ConversationHandler.END


def send_notifications_to_user(message: str, meetup_id: str) -> None:
    users = User.objects.filter(chat_id__isnull=False, meetups__id=meetup_id)
    users_telegram_chat_id = [user.chat_id for user in users]
    telegram_token = settings.TOKEN_TELEGRAM
    url = f'https://api.telegram.org/bot{telegram_token}/sendMessage'
    for user_telegram_chat_id in users_telegram_chat_id:
        try:
            requests.post(url, json={'chat_id': user_telegram_chat_id, 'text': message})
        except requests.HTTPError as err:
            logger.warning(f'Failed to send message to user chat id{user_telegram_chat_id}\
                \neror is {err}')
