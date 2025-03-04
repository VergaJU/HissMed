from cat.mad_hatter.decorators import tool, hook, plugin
from cat.looking_glass.stray_cat import StrayCat
from cat.log import log
from cat.agent import Agent
from cat.memory import Memory
import os
import sys
from cat.rabbit_hole import RabbitHole
from datetime import datetime, date

sys.path.append(os.path.join(os.path.dirname(__file__)))

from HissMed.retrieve_articles import PapersDownloader

@tool
def hisscat_download_literature(user_message, cat):
    """ run this tools whenever message starts with HissMed search"""
    log.info(f"{datetime.now()} User is searching for: {user_message}")  # Log the user message
    settings = cat.mad_hatter.get_plugin().load_settings()
    log.info(f"{datetime.now()} User email: {settings['email']}")  # Log the user email
    email = settings['email']
    n_top_articles = settings['top_n_articles']
    citation_weight = settings['citation_weight']
    year_weight = settings['year_weight']
    journal_weight = settings['journal_weight']
    PapersDownloader.set_email(email=email)
    log.info(f"{datetime.now()} Saving articles in {os.path.join(os.getcwd(),'literature')}")  # Log the output folder
    PapersDownloader.create_directory()
    PapersDownloader.batch_download_pdfs(query=user_message, n_top_articles=n_top_articles, citation_w=citation_weight, year_w=year_weight, journal_w=journal_weight)
    log.info(f"{datetime.now()} Downloaded articles") # Log the download status
    load_files_to_memory(cat, directory='./literature')
    return user_message


@tool
def rag_tool(query, cat) -> str:
    """
    run this tools whenever message starts with Please tell me about

    Process a query using Retrieval Augmented Generation (RAG) and cite documents from memory.
    """
    # Initialize the Agent and Memory
    agent = Agent(cat)
    memory = Memory(cat)
    settings = cat.mad_hatter.get_plugin().load_settings()
    top_references = settings['top_references']
    # Retrieve relevant documents based on the query
    relevant_documents = memory.retrieve_documents(query, max_results=top_references)

    # Prepare the prompt for the LLM
    prompt = f"You are a research assistant that, based on the following documents, answer the query.
                If the information required is not in the documents answer 'I am sorry, I need more information'.
                The query: '{query}'.\n\n"
    for doc in relevant_documents:
        prompt += f"Document: {doc.title}\nContent: {doc.content}\n\n"

    # Generate the response using the LLM
    response = agent.generate_response(prompt)

    # Add citations to the response
    citations = [f"[{i+1}] {doc.title}" for i, doc in enumerate(relevant_documents)]
    response += "\n\nCitations:\n" + "\n".join(citations)

    return response


@tool
def delete_declarative_memory(cat):
    """
    When the user asks you to Flush the memory, run this tool to clear the declarative memory."""
    # Initialize the Memory
    memory = Memory(cat)

    # Attempt to clear the declarative memory
    success = memory.clear_declarative_memory()

    if success:
        return "All entries in declarative memory have been successfully deleted."
    else:
        return "Failed to delete entries in declarative memory."


def load_files_to_memory(cat, directory='./literature'):
    """
    Load supported files from the specified directory into the Cat's declarative memory.

    Args:
        cat: The Cat instance.
        directory (str): The directory containing files to load.
    """
    # Initialize the Rabbit Hole
    rabbit_hole = RabbitHole(cat)

    # Iterate through files in the directory
    for filename in os.listdir(directory):
        if filename.endswith(('.txt', '.md', '.pdf', '.html')):
            file_path = os.path.join(directory, filename)
            # Load the file into the declarative memory
            with open(file_path, 'rb') as file:
                rabbit_hole.insert_memory(file)
            print(f"{datetime.now()} Loaded {filename} into memory.")
