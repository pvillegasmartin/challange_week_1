from bs4 import BeautifulSoup
import requests
import pandas as pd
from time import sleep
import matplotlib.pyplot as plt
import plotly.express as px
import streamlit as st

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

    for i in range(20,38):
        df = pd.DataFrame(columns=["url", "title", "author", "num_reviews", "num_ratings", "avg_rating", "num_pages",
                                   "original_publish_year", "series", "genres", "awards", "places"])
        page = requests.get(f'https://www.goodreads.com/list/show/47.Best_Dystopian_and_Post_Apocalyptic_Fiction?page={i}')
        soup = BeautifulSoup(page.content, 'html.parser')
        print(i)
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
        df.to_csv(path_or_buf='book_database.csv', mode='a', sep='&', header=False)

def preprocessing(data):
    data = pd.read_csv(data, sep='&')
    #Filter data
    data['original_publish_year'] = pd.to_numeric(data['original_publish_year'], errors='coerce')
    # TODO think which columns can't have None values and drop na
    data = data.dropna(subset=['avg_rating','original_publish_year'])
    data = data[data['original_publish_year'] <= 2021]
    data = data.drop_duplicates(subset=['title'])
    data = data.reset_index(drop=True)



    # MinMax Normilization on avg_rating and scaling from 0 to 10 and saving it into the minmax_norm_rating
    data['minmax_norm_rating'] = 1 + (data['avg_rating'] - data['avg_rating'].min()) / (\
                data['avg_rating'].max() - data['avg_rating'].min()) * 9
    # Mean normilization
    data['mean_norm_rating'] = 1 + (data['avg_rating'] - data['avg_rating'].mean()) / (\
                data['avg_rating'].max() - data['avg_rating'].min()) * 9
    data['awards'] = data['awards'].str.split(';').str.len()
    return data

def best_author_book(author, data):
    return data[data['author']==author].sort_values("minmax_norm_rating", ascending=False)['title'].head(1).item()

def streamlit ():
    pass

def graphs(data):

    # GRAPH 1:
    books_year = data.groupby(data['original_publish_year'])['title'].count()
    fig_1 = plt.figure(figsize=(10, 6))
    ax_1 = fig_1.add_subplot(1, 1, 1)
    # set x axis
    ax_1.set_xlabel("Year publication", fontsize=20)
    # set y axis
    ylabels = range(0, (int(books_year.max()/50)+1)*50, 50)
    ax_1.set_ylabel("Number of books", fontsize=20)
    ax_1.set_yticks(ylabels)
    ax_1.set_yticklabels(ylabels, fontsize=20)
    ax_1.set_title("Number of books per publication year", fontsize=30, pad=20)
    ax_1.bar(books_year.index.values, books_year, width=0.8)
    ax_1.grid(linestyle='--', linewidth=1)




    #GRAPH 2:
    #TODO think if we want to show only years with a minimum of books
    ratings_minmax_year = data.groupby(data['original_publish_year'])['minmax_norm_rating'].mean()
    fig_2 = plt.figure(figsize=(10, 6))
    ax_2 = fig_2.add_subplot(1, 1, 1)
    # set x axis
    ax_2.set_xlabel("Year publication", fontsize=20)
    # set y axis
    ylabels = range(1, 11, 1)
    ax_2.set_ylabel("Avg rating", fontsize=20)
    ax_2.set_yticks(ylabels)
    ax_2.set_yticklabels(ylabels, fontsize=20)
    ax_2.set_title("Avg rating per publication year", fontsize=30, pad=20)
    ax_2.plot(ratings_minmax_year.index.values, ratings_minmax_year)
    ax_2.grid(linestyle='--', linewidth=2)

    # GRAPH 3:
    #TODO number of authors as filter in streamlit
    books_author = data.groupby(data['author'])['title'].count().nlargest(5)
    minmax_rating_author = data.groupby(data['author'])['minmax_norm_rating'].mean()
    best_book_author_data = {label:best_author_book(label, data) for label in books_author.index.values}
    best_book_author = pd.Series(best_book_author_data,name='best_book')
    data_graph_3 = pd.concat([books_author, minmax_rating_author.reindex(books_author.index),best_book_author], axis=1).sort_index()
    fig_3 = px.treemap(data_graph_3,
                path=[data_graph_3.index.values],
                values=data_graph_3['title'],
                color=round(data_graph_3['minmax_norm_rating'],2),
                range_color=[data_graph_3['minmax_norm_rating'].min(),data_graph_3['minmax_norm_rating'].max()],
                title="Author by number of books and their rankings",
                width=1000,
                height=max(len(books_author)*20,600),
                template='presentation'
                       )
    fig_3.data[0].customdata = list(dict(sorted(best_book_author_data.items(), key=lambda x: x[0].lower())).values())
    fig_3.update_traces(hovertemplate='<b>Author:</b> %{label}<br><b>Nº books:</b> %{value}<br><b>Avg rating:</b> %{color}<br><b>Best book:</b> %{customdata}<extra></extra>')



    return fig_3,fig_1,fig_2

if __name__ == "__main__":
    #scraper()
    data = preprocessing('./book_database.csv')
    ratings_minmax_year = data.groupby(data['original_publish_year'])['minmax_norm_rating'].mean()
    graphs = graphs(data)

    #st.pyplot(graphs[1])
    st.plotly_chart(graphs[0])
    st.write(graphs[0].data[0].labels)