import os
import time
import requests
import argparse
from Bio import Entrez
import xml.etree.ElementTree as ET
from datetime import datetime
import io
import pandas as pd
import numpy as np
import html
from typing import List, Dict

class PapersDownloader:
    headers = {"User-Agent": "Mozilla/5.0"}
    output_folder = "./literature"
    sleep_time = 0

    @classmethod
    def create_directory(cls) -> None:
        """
        Create the output directory if it doesn't exist.
        """
        if os.path.exists(cls.output_folder):
            for filename in os.listdir(cls.output_folder):
                file_path = os.path.join(cls.output_folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        os.rmdir(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")
        else:
            os.makedirs(cls.output_folder)

    @staticmethod
    def get_args() -> argparse.Namespace:
        """
        Get command-line arguments.
        
        Returns:
            argparse.Namespace: The parsed arguments.
        """
        parser = argparse.ArgumentParser(description="Download PDFs from PMC.")
        parser.add_argument("--query", type=str, help="Search query for PMC articles.")
        parser.add_argument("--email", type=str, help="Your email address for NCBI.")
        parser.add_argument("--top_n", type=int, help="Number of top articles to download.", default=10)
        parser.add_argument("--journal_w", type=float, help="Journal ranking weight.", default=0.9)
        parser.add_argument("--year_w", type=float, help="Publication year weight.", default=0.5)
        parser.add_argument("--citation_w", type=float, help="Citations weight.", default=0.7)
        args = parser.parse_args()
        return args

    @staticmethod
    def get_total_count(query:str, db:str="pmc") -> int:
        """
        Get the total number of articles found for a given query.
        
        Args:
            query (str): The search query.
            db (str): The database to search (default: "pmc").
        
        Returns:
            int: The total number of articles found.
        """
        print(f"{datetime.now()} - Searching for articles with query: {query}")
        try:
            handle = Entrez.esearch(db=db, term=query, retmax=0)
            record = Entrez.read(handle)
            print(f"{datetime.now()} - Total articles found: {record['Count']}")
            return int(record["Count"])
        except Exception as e:
            print(f"Error searching for query '{query}': {e}")
            return 0

    @staticmethod
    def get_pmc_ids(query:str, retstart:int, retmax:int=100, db:str="pmc")->List[str]:
        """
        Get a list of PMC IDs for a given query.
        
        Args:
            query (str): The search query.
            retstart (int): The start index for retrieving results.
            retmax (int): The maximum number of results to retrieve (default: 100).
            db (str): The database to search (default: "pmc").
            
        Returns:
            List[str]: A list of PMC IDs.
        """
        handle = Entrez.esearch(db=db, term=query, retstart=retstart, retmax=retmax)
        record = Entrez.read(handle)
        pmc_ids = record["IdList"]
        return pmc_ids

    @staticmethod
    def get_articles_info(id_list:List[str], db="pmc")->ET.Element:
        """
        Get detailed information about a list of articles.
        
        Args:
            id_list (List[str]): A list of article IDs.
            db (str): The database to search (default: "pmc").
        
        Returns:
            ET.Element: An XML element containing the article information.
        """
        # print datetime.now up to the seconds
        print(f"{datetime.now()} - Fetching articles info...")
        fetch_handle = Entrez.efetch(db=db, id=id_list, retmode="xml")
        data = fetch_handle.read()
        root = ET.fromstring(data)
        return root
    
    @classmethod
    def get_journal_ranking(cls)->pd.DataFrame:
        """
        Get the journal ranking based on the SJR (SCImago Journal Rank) indicator.
        
        Returns:
            pd.DataFrame: A DataFrame containing the journal titles and their SJR values.
        """
        print(f"{datetime.now()} - Fetching journal ranking...")
        # URL to the Excel dataset
        url = "https://www.scimagojr.com/journalrank.php?out=xls"
        # Send a GET request to fetch the content
        response = requests.get(url, headers=cls.headers)
        response.raise_for_status()  # Raise an error if the request failed
        # Load the content into a BytesIO stream and read it with pandas
        csv_data = io.BytesIO(response.content)
        df = pd.read_csv(csv_data, sep=';',decimal=",")
        df = df[['Title', 'SJR']]
        df["Title"] = df["Title"].apply(html.unescape)
        # Display the first few rows of the dataset
        return df


    @classmethod
    def get_articles_metrics(cls, query:str, db:str="pmc")->Dict:
        """
        Get metrics for articles based on the search query.
        
        Args:
            query (str): The search query.
            db (str): The database to search (default: "pmc").
            
        Returns:
            Dict: A dictionary of article metrics.
        """
        count = cls.get_total_count(query=query, db=db)
        pmc_ids=cls.get_pmc_ids(query=query, retstart=0, retmax=count, db=db)
        root = cls.get_articles_info(id_list=pmc_ids, db=db)
        journal_ranking=cls.get_journal_ranking()
        print(f"{datetime.now()} - Fetching articles metrics...")
        metrics={}
        for article in root.findall('.//article'):
            pmc_id=article.find(".//article-id[@pub-id-type='pmc']").text
            journal_elem = article.find('.//journal-meta//journal-title-group//journal-title')
            journal_title = journal_elem.text if journal_elem is not None else "N/A"
            journal_SJR = float(journal_ranking[journal_ranking['Title'] == journal_title]['SJR'].values[0]) if journal_title in journal_ranking['Title'].values else 0
            pub_date_elem = article.find('.//article-meta//pub-date/year')
            pub_year = int(pub_date_elem.text) if pub_date_elem is not None else "N/A"
            citations = 0
            # This will find all <ref> elements under any <ref-list>
            for ref in article.findall('.//ref-list//ref'):
                citations +=1
            metrics[pmc_id] = {"journal_title": journal_title, 
                               "journal_ranking":journal_SJR, 
                               "pub_year": pub_year, 
                               "citations": float(citations)}
        return metrics

    
    @staticmethod
    def rank_articles(metrics:Dict,journal_w=0.9,year_w=0.5,citation_w=0.7,**kwargs)->pd.DataFrame:
        """
        Rank articles based on journal ranking, publication year, and number of citations.
        
        Args:
            metrics (Dict): A dictionary of article metrics.
            journal_w (float): The weight for journal ranking (default: 0.9).
            year_w (float): The weight for publication year (default: 0.5).
            citation_w (float): The weight for number of citations (default: 0.7).
        
        Returns:
            pd.DataFrame: A DataFrame of ranked articles.
        """
        print(f"{datetime.now()} - Ranking articles...")
        df=pd.DataFrame(metrics)
        df=df.T
        ## normalize the columns
        df['journal_ranking'] = (df['journal_ranking'] - df['journal_ranking'].min()) / (df['journal_ranking'].max() - df['journal_ranking'].min())
        df['pub_year'] = (df['pub_year'] - df['pub_year'].min()) / (df['pub_year'].max() - df['pub_year'].min())
        # citations logaritmic before normalization
        df['citations'] = pd.to_numeric(df['citations'], errors='coerce').fillna(0)
        df['citations'] = np.log10(df['citations']+1e-6)
        df['citations'] = (df['citations'] - df['citations'].min()) / (df['citations'].max() - df['citations'].min())
        df['score']=journal_w*df['journal_ranking']+year_w*df['pub_year']+citation_w*df['citations']
        df.sort_values(by='score',ascending=False)
        return df

    @classmethod
    def get_top_n_articles(cls, query:str, n_top_articles=10, db="pmc",**kwargs)->pd.DataFrame:
        """
        Get the top N articles based on the ranking.
        
        Args:
            query (str): The search query.
            n_top_articles (int): The number of top articles to retrieve.
            db (str): The database to search (default: "pmc").
            **kwargs: Additional keyword arguments for ranking.
        
        Returns:
            pd.DataFrame: A DataFrame of the top N articles.
        """
        metrics=cls.get_articles_metrics(query=query, db=db)
        df=cls.rank_articles(metrics=metrics,**kwargs)
        print(f"{datetime.now()} - Getting top {n_top_articles} articles...")
        df=df.iloc[:n_top_articles]
        return df

    @classmethod
    def download_pdf(cls, pmc_id:str, pdf_url:str)->None:
        """
        Download a PDF file from a given URL.
        
        Args:
            pmc_id (str): The PMC ID of the article.
            pdf_url (str): The URL of the PDF file.
        
        Returns:
            None
        """
        response = requests.get(pdf_url, headers=cls.headers, timeout=30)
        if response.status_code == 200 and response.headers.get("Content-Type", "").startswith("application/pdf"):
            file_path = os.path.join(cls.output_folder, f"{pmc_id}.pdf")
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"      Downloaded {pmc_id}.pdf")
        else:
            print(f"      Failed to download {pmc_id} (Status: {response.status_code})")

    @classmethod
    def download_pdfs(cls, pmc_ids:List[str])->None:
        """
        Download PDF files for a list of PMC IDs.
        
        Args:
            pmc_ids (List[str]): A list of PMC IDs.
            
        Returns:
            None
        """
        for pmc_id in pmc_ids:
            if not pmc_id.startswith("PMC"):
                pmc_id = "PMC" + pmc_id
            pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/"
            try:
                cls.download_pdf(pmc_id=pmc_id, pdf_url=pdf_url)
            except Exception as e:
                print(f"      Error downloading {pmc_id}: {e}")
            time.sleep(cls.sleep_time)

    @classmethod
    def batch_download_pdfs(cls, query:str, retmax=100, db="pmc",**kwargs)->None:
        """
        Batch download PDF files for a given query.
        
        Args:
            query (str): The search query.
            retmax (int): The maximum number of articles to retrieve in each batch.
            db (str): The database to search (default: "pmc").
            **kwargs: Additional keyword arguments for ranking.
        
        Returns:
            None
        """
        top_n_articles=cls.get_top_n_articles(query=query, db=db,**kwargs)
        print(f"{datetime.now()} - Downloading top {top_n_articles.shape[0]} articles...")
        if top_n_articles.shape[0] == 0:
            return
        pmc_ids=top_n_articles.index.tolist()
        chunks = [pmc_ids[i:i+retmax] for i in range(0, len(pmc_ids), retmax)]
        for chunk in chunks:
            cls.download_pdfs(chunk)

    @classmethod
    def set_email(cls, email:str)->None:
        """
        Set the email address for the NCBI Entrez API.
        
        Args:
            email (str): The email address.
        
        Returns:
            None
        """
        if email == 'your.email@mail.com':
            raise ValueError("Please set your email address")
        Entrez.email = email


if __name__ == "__main__":
    args = PapersDownloader.get_args()
    query = args.query or '(Multiple Myeloma[Title]) AND ("2024/01/01"[Publication Date] : "2025/12/31"[Publication Date])'
    email = args.email or "your.email@example.com"
    PapersDownloader.set_email(email)
    PapersDownloader.create_directory()
    PapersDownloader.batch_download_pdfs(query=query)
