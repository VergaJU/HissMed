from cat.mad_hatter.decorators import tool, hook, plugin
from datetime import datetime, date
from cat.looking_glass.stray_cat import StrayCat
from cat.log import log
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__)))

from HissMed.retrieve_articles import PapersDownloader


def settings_model():
    settings = cat.mad_hatter.get_plugin().load_settings()
    return settings


@tool
def hisscat_download_literature(user_message, cat):
    """ run this tool whenever the message starts with HissMed search"""
    # user_message = StrayCat.working_memory.user_message_json.text
    log.debug(f"User message received: {user_message}")  # Log the user message
    # Check if the input matches the 'HissMed search: <query>' format
    if user_message.startswith("HissMed search: "):
        settings = settings_model()
        PapersDownloader.set_email(email=settings['email'])
        # Extract the query
        query = user_message[len("HissMed search: "):]
        # Print the query
        log.debug(f"Query received: {query}")
        PapersDownloader.run(query)
    return user_message
