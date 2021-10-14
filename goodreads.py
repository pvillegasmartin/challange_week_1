from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import math
from time import sleep
import matplotlib.pyplot as plt
import plotly.express as px
import streamlit as st
from streamlit_metrics import metric, metric_row
from wordcloud import WordCloud, STOPWORDS
from PIL import Image

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

    #checking the Author column containing the numerice values count
    authors_must_string = [not(str(author).isnumeric()) for author in data['author']]
    data = data[authors_must_string]
    #checking the Author column containing the numerice data and applying the simple indexing method
    data.author.str.contains(r'[0-9]').value_counts()



    # MinMax Normilization on avg_rating and scaling from 0 to 10 and saving it into the minmax_norm_rating
    data['minmax_norm_rating'] = 1 + (data['avg_rating'] - data['avg_rating'].min()) / (\
                data['avg_rating'].max() - data['avg_rating'].min()) * 9
    # Mean normilization
    data['mean_norm_rating'] = 1 + (data['avg_rating'] - data['avg_rating'].mean()) / (\
                data['avg_rating'].max() - data['avg_rating'].min()) * 9

    data['awards'] = data['awards'].str.split(';').str.len()
    data = data.rename(columns={'title': 'Title', 'original_publish_year': 'Publication year', 'minmax_norm_rating': 'Rating', 'awards':'Awards', 'num_pages':'Nº pages', 'series':'Series'})
    return data

def best_author_book(author, data):
    return data[data['author']==author].sort_values("Rating", ascending=False)['Title'].head(1).item()

def streamlit_template (graphs, data):
    st.set_page_config(layout="wide")
    analysis_type = st.sidebar.radio("SELECT TYPE OF ANALYSIS",('General', 'Author'))
    st.markdown("<h1 style=' color: #948888;'>Best Dystopian and Post-Apocalyptic Fiction</h1>", unsafe_allow_html=True)
    if analysis_type == 'General':
        #FILTERS
        year_publication = st.sidebar.slider('Publication year', min_value=int(min(data['Publication year'])), max_value=int(max(data['Publication year'])), step=1)
        number_authors = st.sidebar.slider('Number authors', min_value=1, max_value=15, step=1)
        data = data[data['Publication year'] >= year_publication]
        graphs_charts = graphs(data,top_authors=number_authors)
        col1, col2, col3 = st.beta_columns(3)
        col2.pyplot(graphs_charts[6])
        col1, col2 = st.beta_columns(2)
        col1.pyplot(graphs_charts[5])
        col2.pyplot(graphs_charts[9])
        col1, col2 = st.beta_columns(2)
        col1.pyplot(graphs_charts[8])
        col2.pyplot(graphs_charts[7])
        col1, col2, col3 = st.beta_columns((1, 6, 1))
        col2.plotly_chart(graphs_charts[3])

    elif analysis_type == 'Author':
        authors = st.sidebar.selectbox("Authors", data['author'])
        data = data[data['author'] == authors]
        graphs_charts = graphs(data)
        st.markdown(f"<h1 style=' color: #948888;'>{authors}</h1>", unsafe_allow_html=True)
        metric_row(
            {
                "Nº Books": data['Title'].count(),
                "Series books": data[data['Series'] == 1]['Title'].count(),
                "Nº rewards": int(data['num_reviews'].sum()),
                "Average rating books": round(data['Rating'].mean(),1),
                "Nº awards": int(data['Awards'].sum())
            }
        )

        st.markdown(f"<h2 style=' color: #948888;'>List of {authors}'s books</h2>", unsafe_allow_html=True)
        st.markdown(
            f"<p style=' color: #948888;'>In this table you can find all {authors}'s books with some relevant information sorted by rating value.</p>",
            unsafe_allow_html=True)

        col1, col2, col3 = st.beta_columns((1, 4, 1))
        col2.table(data.loc[:, ['Title', 'Series', 'Publication year', 'Rating', 'Awards', 'Nº pages']].set_index(
            'Title').sort_values('Rating', ascending=False))


        st.markdown(f"<h2 style=' color: #948888;'>Cloud of genres</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style=' color: #948888;'>Fast view of the most important type of genres present in {authors}'s books.</p>", unsafe_allow_html=True)
        fig = plt.figure(figsize=(5, 2))
        ax = fig.add_subplot(1, 1, 1)
        ax.imshow(graphs_charts[0], interpolation='bilinear')
        ax.axis("off")
        col1, col2, col3 = st.beta_columns((1,2,1))
        col2.pyplot(fig)

def transform_format(val):
    if val == 0:
        return 255
    else:
        return val

def graphs(data,transform_format=transform_format,top_authors=5):

    # GRAPH 1:
    books_year = data.groupby(data['Publication year'])['Title'].count()
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

    table_1 = books_year.sort_values(ascending=False)


    #GRAPH 2:
    #TODO think if we want to show only years with a minimum of books
    ratings_minmax_year = data.groupby(data['Publication year'])['Rating'].mean()
    fig_2 = plt.figure(figsize=(10, 6))
    ax_2 = fig_2.add_subplot(1, 1, 1)
    # set x axis
    ax_2.set_xlabel("Year publication", fontsize=20)
    # set y axis
    ylabels = range(1, 11, 1)
    ax_2.set_ylabel("Minmax Norm Rating", fontsize=20)
    ax_2.set_yticks(ylabels)
    ax_2.set_yticklabels(ylabels, fontsize=20)
    ax_2.set_title("Avg rating per publication year", fontsize=30, pad=20)
    ax_2.plot(ratings_minmax_year.index.values, ratings_minmax_year)
    ax_2.grid(linestyle='--', linewidth=1)

    # GRAPH 3:
    books_author = data.groupby(data['author'])['Title'].count().nlargest(top_authors)
    minmax_rating_author = data.groupby(data['author'])['Rating'].mean()
    best_book_author_data = {label:best_author_book(label, data) for label in books_author.index.values}
    best_book_author = pd.Series(best_book_author_data,name='best_book')
    #data_graph_3 = pd.concat([books_author, minmax_rating_author.reindex(books_author.index),best_book_author], axis=1).sort_index()
    boolean_top_authors = data.author.isin(books_author.index.values)
    data_graph_3 = data[boolean_top_authors]
    data_graph_3['all'] = f'Top {top_authors} authors'
    fig_3 = px.treemap(data_graph_3,
                       path=[data_graph_3['all'], data_graph_3['author'],data_graph_3['Title']],
                       values=data_graph_3['Rating'],
                       color=data_graph_3['Rating'],
                       range_color=[math.floor(data_graph_3['Rating'].min()),math.ceil(data_graph_3['Rating'].max())],
                       title="Author by rankings and their number of books",
                       width=1200,
                       height=max(len(books_author) * 70, 600),
                       template='presentation'
                       )
    fig_3.data[0].textinfo = 'label+value'
    #fig_3.data[0].customdata = list(dict(sorted(best_book_author_data.items(), key=lambda x: x[0].lower())).values())
    fig_3.update_traces(hovertemplate='<b>Author:</b> %{label}<br><b>Avg rating:</b> %{value}<br><extra></extra>')

    # GRAPH 4
    list_genres = {}
    for element in data['genres']:
        try:
            for genre in element.split(';'):#[:3]:

                if genre in list_genres.keys():
                    list_genres[genre] += 1
                else:
                    list_genres[genre] = 1
        except:
            pass
    top_genres = {key: list_genres[key] for key in sorted(list_genres, key=list_genres.get, reverse=True)[:5]}
    fig_4 = plt.figure(figsize=(15, 10))
    ax_4 = fig_4.add_subplot(1, 1, 1)
    ax_4.set_title("Genres", fontsize=20)
    ax_4.pie(top_genres.values(), normalize=True, labels=top_genres.keys(), autopct=lambda p: '{:.1f}%'.format(p), textprops={'fontsize': 18})
    #ax_4.legend(loc='lower right', prop={'size': 20})

    #mask = np.array(Image.open("libro.png"))
    #transformed_mask = np.ndarray((mask.shape[0], mask.shape[1]), np.int32)
    #for i in range(len(mask)):
    #    transformed_mask[i] = list(map(transform_format, mask[i]))

    word_cloud = WordCloud(width=1600, height=800, background_color="white").generate_from_frequencies(list_genres)

    #GRAPH 5: explain we need a minimum of reviews
    fig_5 = plt.figure(figsize=(10, 6))
    ax_5 = fig_5.add_subplot(1, 1, 1)
    # set x axis
    ax_5.set_xlabel("Number of reviews", fontsize=20)
    # set y axis
    ax_5.set_ylabel("Rating", fontsize=20)
    ax_5.set_ylim(1, 10)
    ax_5.set_title("Rating by number of reviews", fontsize=30, pad=20)
    ax_5.scatter(data['num_reviews'], data['Rating'])
    ax_5.grid(linestyle='--', linewidth=1)

    # GRAPH 6: explain we need a minimum of reviews
    Q1 = data['num_reviews'].quantile(0.25)
    fig_6 = plt.figure()
    ax_6 = fig_6.add_subplot(1, 1, 1)
    ax_6.set_title("Number of reviews", fontsize=30, pad=20)
    ax_6.set_xlabel("All books", fontsize=20)
    ax_6.boxplot(data['num_reviews'], showfliers=False, showmeans=True)
    ax_6.text(1.02, int(data['num_reviews'].mean()), 'mean: ' + str(int(data['num_reviews'].mean())), color='green')
    ax_6.text(0.95, int(data['num_reviews'].median())+15, 'median: ' + str(int(data['num_reviews'].median())), color='orange')

    # GRAPH 7: explain relation of reviews and authors
    reviews_author_mean = data.groupby(data['author'])['num_reviews'].mean()
    reviews_author_sum = data.groupby(data['author'])['num_reviews'].sum()
    colors = {'both':'green', 'one':'red'}

    fig_7 = plt.figure(figsize=(10, 6))
    ax_7 = fig_7.add_subplot(1, 1, 1)
    # set x axis
    ax_7.set_xlabel("Authors", fontsize=20)
    ax_7.set_xticklabels(reviews_author_mean.nlargest(top_authors).index.values, rotation=30, ha='right')
    # set y axis
    ax_7.set_ylabel("Average reviews", fontsize=20)
    ax_7.set_title(f"Top {top_authors} authors by average reviews", fontsize=30, pad=20)
    c = []
    for el in reviews_author_mean.nlargest(top_authors).index.values:
        if el in reviews_author_sum.nlargest(top_authors).index.values:
            c.append(colors['both'])
        else:
            c.append(colors['one'])
    ax_7.bar(reviews_author_mean.nlargest(top_authors).index.values, reviews_author_mean.nlargest(top_authors).values, color=c)
    ax_7.axhline(reviews_author_mean.mean(), color='green', linewidth=1)
    ax_7.text(-0.40, int(reviews_author_mean.mean())+5000, 'mean: ' + str(int(reviews_author_mean.mean())), color='green', backgroundcolor='white')
    ax_7.grid(linestyle='--', axis='y', linewidth=1)
    fig_8 = plt.figure(figsize=(10, 6))
    ax_8 = fig_8.add_subplot(1, 1, 1)
    # set x axis
    ax_8.set_xlabel("Authors", fontsize=20)
    ax_8.set_xticklabels(reviews_author_sum.nlargest(top_authors).index.values, rotation=30, ha='right')
    # set y axis
    ax_8.set_ylabel("Total reviews", fontsize=20)
    ax_8.set_title(f"Top {top_authors} authors by total reviews", fontsize=30, pad=20)
    c = []
    for el in reviews_author_sum.nlargest(top_authors).index.values:
        if el in reviews_author_mean.nlargest(top_authors).index.values:
            c.append(colors['both'])
        else:
            c.append(colors['one'])
    ax_8.bar(reviews_author_sum.nlargest(top_authors).index.values, reviews_author_sum.nlargest(top_authors).values, color=c)
    ax_8.axhline(reviews_author_sum.mean(), color='green', linewidth=1)
    ax_8.text(-0.4, int(reviews_author_sum.mean())+8000, 'mean: ' + str(int(reviews_author_sum.mean())), color='green', backgroundcolor='white')
    ax_8.grid(linestyle='--', axis='y', linewidth=1)

    # GRAPH 9: explain we need a minimum of reviews
    books_author_sum = pd.concat([data.groupby(data['author'])['Title'].count(),data.groupby(data['author'])['Rating'].mean()],axis=1)
    fig_9 = plt.figure(figsize=(10, 6))
    ax_9 = fig_9.add_subplot(1, 1, 1)
    # set x axis
    ax_9.set_xlabel("Number of books", fontsize=20)
    ax_9.set_xlim(int(min(books_author_sum['Title']))-1, int(max(books_author_sum['Title']))+1)
    ax_9.set_xticks(range(int(min(books_author_sum['Title']))-1, int(max(books_author_sum['Title']))+1,1))
    # set y axis
    ax_9.set_ylabel("Rating", fontsize=20)
    ax_9.set_title("Rating by number of books", fontsize=30, pad=20)
    ax_9.scatter(books_author_sum['Title'], books_author_sum['Rating'])
    ax_9.grid(linestyle='--', linewidth=1)

    return word_cloud,fig_1,fig_2,fig_3,fig_4,fig_5,fig_6,fig_7,fig_8,fig_9


if __name__ == "__main__":
    #scraper()
    data = preprocessing('./book_database.csv')
    streamlit_template(graphs,data)
