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
    settings = cat.mad_hatter.get_plugin().load_settings()
    log.info(f"User email: {settings['email']}")  # Log the user email
    email = settings['email']
    top_n_articles = settings['top_n_articles']
    top_references = settings['top_references'] # not used now
    citation_weight = settings['citation_weight']
    year_weight = settings['year_weight']
    journal_weight = settings['journal_weight']
    PapersDownloader.set_email(email=email)
    log.info(f"Saving articles in {os.path.join(os.getcwd(),'literature')}")  # Log the output folder
    PapersDownloader.create_directory()
    PapersDownloader.batch_download_pdfs(query=user_message, top_n_articles=top_n_articles, citation_w=citation_weight, year_w=year_weight, journal_w=journal_weight)
    log.info(f"Downloaded articles") # Log the download status
    return user_message

