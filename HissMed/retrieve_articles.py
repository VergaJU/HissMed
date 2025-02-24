import os
import time
import requests
import argparse
from Bio import Entrez

class PapersDownloader:
    headers = {"User-Agent": "Mozilla/5.0"}
    output_folder = "data"
    sleep_time = .5

    @classmethod
    def create_directory(cls):
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
    def get_args():
        parser = argparse.ArgumentParser(description="Download PDFs from PMC.")
        parser.add_argument("--query", type=str, help="Search query for PMC articles.")
        parser.add_argument("--email", type=str, help="Your email address for NCBI.")
        args = parser.parse_args()
        return args

    @staticmethod
    def get_total_count(query, db="pmc"):
        try:
            handle = Entrez.esearch(db=db, term=query, retmax=0)
            record = Entrez.read(handle)
            return int(record["Count"])
        except Exception as e:
            print(f"Error searching for query '{query}': {e}")
            return 0

    @staticmethod
    def get_pmc_ids(query, retstart, retmax=100, db="pmc"):
        handle = Entrez.esearch(db="pmc", term=query, retstart=retstart, retmax=retmax)
        record = Entrez.read(handle)
        pmc_ids = record["IdList"]
        return pmc_ids

    @classmethod
    def download_pdf(cls, pmc_id, pdf_url):
        response = requests.get(pdf_url, headers=cls.headers, timeout=30)
        if response.status_code == 200 and response.headers.get("Content-Type", "").startswith("application/pdf"):
            file_path = os.path.join(cls.output_folder, f"{pmc_id}.pdf")
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"      Downloaded {pmc_id}.pdf")
        else:
            print(f"      Failed to download {pmc_id} (Status: {response.status_code})")

    @classmethod
    def download_pdfs(cls, pmc_ids):
        for pmc_id in pmc_ids:
            if not pmc_id.startswith("PMC"):
                pmc_id = "PMC" + pmc_id
            pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/"
            try:
                cls.download_pdf(pmc_id, pdf_url)
            except Exception as e:
                print(f"      Error downloading {pmc_id}: {e}")
            time.sleep(cls.sleep_time)

    @classmethod
    def batch_download_pdfs(cls, query, retmax=100, db="pmc"):
        total_count = cls.get_total_count(query, db)
        if total_count == 0:
            return
        for start in range(0, total_count, retmax):
            print(f"  Processing batch starting at record {start}")
            try:
                pmc_ids = cls.get_pmc_ids(query, start, retmax, db)
            except Exception as e:
                print(f"  Error retrieving batch starting at {start}: {e}")
                continue
            cls.download_pdfs(pmc_ids)

    @classmethod
    def run(cls, query, email):
        cls.create_directory()
        Entrez.email = email
        cls.batch_download_pdfs(query)


if __name__ == "__main__":
    args = PapersDownloader.get_args()
    query = args.query or '(Multiple Myeloma[Title]) AND ("2021/01/01"[Publication Date] : "2021/01/10"[Publication Date])'
    email = args.email or "your.email@example.com"
    PapersDownloader.run(query, email)