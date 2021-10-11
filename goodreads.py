from bs4 import BeautifulSoup
import requests
import pandas as pd
from time import sleep

def bookscraper(url):

    page_book = requests.get(url)
    soup_book = BeautifulSoup(page_book.content, 'html.parser')

    title = None
    author = None
    num_reviews = None
    num_ratings = None
    avg_rating = None
    num_pages = None
    original_publish_year = None
    series = None
    genres = None
    awards = None
    places = None

    try:
        title = soup_book.find("h1").text.strip()
    except:
        pass
    try:
        author = soup_book.find("span", itemprop="name").text.strip()
    except:
        pass
    try:
        num_reviews = int(soup_book.find("meta", itemprop="reviewCount").get('content'))
    except:
        pass
    try:
        num_ratings = int(soup_book.find("meta", itemprop="ratingCount").get('content'))
    except:
        pass
    try:
        avg_rating = float(soup_book.find("span", itemprop="ratingValue").text.strip())
    except:
        pass
    try:
        num_pages = int(soup_book.find("span", itemprop="numberOfPages").text.strip().split(' ')[0])
    except:
        pass
    try:
        details = soup_book.find("div", id="details")
        original_publish_year = details.find_all("div", class_="row")[-1].text.strip().split(' ')
        for element in original_publish_year:
            try:
                original_publish_year = int(element)
                break
            except:
                pass

    except:
        pass
    try:
        series = soup_book.find("h2", id="bookSeries").text.strip()
        if series.strip() == "" or series == None:
            series = 0
        else:
            series = 1
    except:
        series = 0
    try:
        genres_list = soup_book.find_all("a", class_="actionLinkLite bookPageGenreLink")
        genres = ";".join([genre.text for genre in genres_list])
    except:
        pass
    try:
        awards_list = soup_book.find_all("a", class_="award")
        awards = ";".join([award.text for award in awards_list])
    except:
        pass
    try:
        places_detail = details.find("div",id="bookDataBox").findChildren("div", recursive=False)
        i=0
        while i<len(places_detail):
            if places_detail[i].text == "Setting":
                places_html = places_detail[i+1]
                break
            i += 1
        places = ';'.join([place.text for place in places_html.find_all('a')])
    except:
        pass

    to_append = {"url": url , "title":title,"author":author,"num_reviews":num_reviews,"num_ratings":num_ratings,"avg_rating":avg_rating,\
                 "num_pages":num_pages,"original_publish_year":original_publish_year,"series":series,"genres":genres,"awards":awards,"places":places}
    return to_append

def scraper():
    base_url = 'https://www.goodreads.com'
    df = pd.DataFrame(columns=["url", "title","author","num_reviews","num_ratings","avg_rating","num_pages","original_publish_year","series","genres","awards","places"])
    for i in range(1,38):
        page = requests.get(f'https://www.goodreads.com/list/show/47.Best_Dystopian_and_Post_Apocalyptic_Fiction?page={i}')
        soup = BeautifulSoup(page.content, 'html.parser')

        book_titles = soup.find_all('a', class_="bookTitle")
        for book in book_titles:
            try:
                id_book = book.get('href')
                data_to_append = bookscraper(base_url+id_book)
                print(data_to_append['title'])
                df_to_append = pd.DataFrame(data_to_append, index=[0])
                df = df.append(df_to_append, ignore_index=True)
            except:
                pass
        df.to_csv(path_or_buf='book_database.csv', sep='&', header=True)

def preprocessing(data):
    data = pd.read_csv(data)

if __name__ == "__main__":
    scraper()