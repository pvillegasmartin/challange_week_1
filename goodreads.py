from bs4 import BeautifulSoup
import requests
import pandas as pd

def bookscraper(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

def scraper():
    base_url = 'https://www.goodreaders.com/'

    page = requests.get('https://www.goodreaders.com/')
    soup = BeautifulSoup(page.content, 'html.parser')

    df = pd.DataFrame(columns=["url","title"])


def preprocessing(data):
    data = pd.read_csv(data)