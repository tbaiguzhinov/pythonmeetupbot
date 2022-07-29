from django.core.management.base import BaseCommand

import json

import logging

from datetime import datetime

from bot.models import Meetup, Block, Stream, Report



def load_program(file_path):
    with open(file_path, 'r', encoding='utf8') as file:
        program = json.load(file)
    content = program['meet-up']
    meet_up = Meetup.objects.get_or_create(
        title=content['title'],
        date=datetime.strptime(content['date'], '%Y-%m-%d'),
    )


class Command(BaseCommand):
    help="Indicate path to .json with program information"

    def add_arguments(self, parser):
        parser.add_argument('file_path')

    def handle(self, *args, **options):
        file_path = options['file_path']
        try:
            load_program(file_path)
        except FileNotFoundError:
            logging.error(" File not found")
        except json.JSONDecodeError:
            logging.error(" Error in .json file, please check encoding")
        except KeyError:
            logging.error(" Error in data formatting, please refer back to instruction")