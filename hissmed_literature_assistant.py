from cat.mad_hatter.decorators import tool, hook, plugin
from datetime import datetime, date
from cat.looking_glass.stray_cat import StrayCat
from cat.log import log
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__)))

from HissMed.retrieve_articles import PapersDownloader

@tool
def hisscat_download_literature(user_message, cat):
    """ run this tools whenever message starts with HissMed search"""
    log.info(f"User is searching for: {user_message}")  # Log the user message
    log.info(f"Action input: {action_input}") # Log the action input
    settings = cat.mad_hatter.get_plugin().load_settings()
    log.info(f"User email: {settings['email']}")  # Log the user email
    PapersDownloader.set_email(email=settings['email'])
    log.info(f"Saving articles in {os.path.join(os.getcwd(),'literature')}")  # Log the output folder
    PapersDownloader.run(user_message) # Download the articles
    log.info(f"Downloaded articles") # Log the download status
    return user_message

