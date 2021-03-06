import logging
import os

from dotenv import load_dotenv


# Enabling logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

# Getting mode, so we could define run function for local and Heroku setup
load_dotenv()
mode = os.getenv('MODE', 'dev')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
PROVIDER_TOKEN = os.getenv('PROVIDER_TOKEN')


def keyboard_row_divider(full_list, row_width=2):
    """Divide list into rows for keyboard"""
    for i in range(0, len(full_list), row_width):
        yield full_list[i: i + row_width]


def escape_characters(text: str) -> str:
    """Screen characters for Markdown V2"""
    text = text.replace('\\', '')

    characters = ['.', '+']
    for character in characters:
        text = text.replace(character, f'\{character}')
    return text
