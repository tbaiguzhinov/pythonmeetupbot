from email import message
import os
#import time
#from functools import partial
from django.core.exceptions import FieldError
from dotenv import load_dotenv
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, ConversationHandler, Filters,
                          MessageHandler, Updater)
from bot.static_text import greetings_message
from bot.models import User, Meetup, Stream, Report, Donation, Question, Block
import json
import logging


START, HANDLE_MENU, HANDLE_PROGRAMS,\
    HANDLE_FORM, HANDLE_QUESTION, HANDLE_STREAM,\
    HANDLE_BLOCK, SEND_QUESTION, CLOSE = range(9)

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


def start(update: Update, context: CallbackContext) -> None:
    clean_message(update, context)
    user_exists = User.objects.filter(telegram_id=update.effective_user.id).exists()
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text=greetings_message,
        reply_markup=create_greetings_menu(user_exists)
        )
    return HANDLE_MENU


def stream_handle_menu(update: Update, context: CallbackContext) -> None:
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
    elif entity == 'questions':
        pass


def question_stream_handle_menu(update: Update, context: CallbackContext) -> None:
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
    rep_message = ''
    for report in reports:
        rep_message += form_report_message(report)
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
    report_message = f'{report.title}\n{report.speaker}'
    return report_message


def program_handle_menu(update: Update, context: CallbackContext) -> None:
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


def select_speaker_menu(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    entity, stream_id = query.data.split('_')
    blocks = Block.objects.filter(stream_id=stream_id)
    block_ids = [block.id for block in blocks]
    reports = Report.objects.filter(block_id__in=block_ids).select_related('speaker')
    keyboard = []
    for report in reports:
        speaker_details = f'{report.speaker.first_name} {report.speaker.last_name}' \
                          f', {report.speaker.job_title}, {report.speaker.company_name}' \
                          f' - {report.title}'
        product_button = [InlineKeyboardButton(
            speaker_details,
            callback_data=f'speaker_{report.speaker.telegram_id}'
        )]
        keyboard.append(product_button)
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


def save_chosen_speaker(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    entity, speaker_id = query.data.split('_')
    user_data = context.user_data
    user_data['speaker_to_ask_id'] = speaker_id
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text='Введите вопрос',
    )
    return SEND_QUESTION


def send_message_to_speaker(update: Update, context: CallbackContext) -> None:
    question_text = update.message.text
    current_user = User.objects.get(telegram_id=update.effective_message.chat_id)
    current_user_details = f'{current_user.first_name} {current_user.last_name} ,' \
                           f'{current_user.job_title} at {current_user.company_name}:\n'
    speaker_to_ask_id = context.user_data.pop('speaker_to_ask_id')
    context.bot.send_message(
        chat_id=speaker_to_ask_id,
        text=current_user_details + question_text,
    )
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text='Спасибо за ваш вопрос!',
        reply_markup=create_greetings_menu()
    )
    return HANDLE_MENU


def meeting_handle(update: Update, context: CallbackContext) -> None:
    users = User.objects.exclude(telegram_id=update.effective_user.id,)
    print(users)
    pass


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
            questionnaire_filled=True
        )
        context.bot.send_message(
                chat_id=update.effective_message.chat_id,
                text='Опрос окончен, спасибо за участие!',
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
