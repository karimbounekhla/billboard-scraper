from bs4 import BeautifulSoup
import requests
import numpy as np
import pandas as pd
import itertools
import unicodedata
import re
import json
# hide HTTPS warning
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_billboard_top_albums_dataframe(date: str='2019-11-11', count: int=5) -> pd.DataFrame:
    """
    Scraps the Billboard website and returns a dataframe containing the top albums from a given week
    :param date: week in the format YYYY-MM-DD (default -> 2019-11-11
    :param count: number of albums from the top (default -> 5)
    :return: Pandas Dataframe with album, artist, rank and # of weeks on chart
    """
    url = "https://www.billboard.com/charts/billboard-200/" + str(date)
    html=requests.get(url, verify=False).text
    soup = BeautifulSoup(html, 'lxml')
    
    results = soup.find_all('li', class_='chart-list__element')
    
    df_billboard = pd.DataFrame(columns=["title", "artist", "rank", "weeks_on_charts"])
    
    # Album Name: chart-element__information__song text--truncate color--primary
    # Artist Name: chart-element__information__artist text--truncate color--secondary
    # Rank: chart-element__rank__number
    # Week on Charts: chart-element__meta text--center color--secondary text--week
    
    for result in results:
        title = result.find('span', class_="chart-element__information__song text--truncate color--primary").text
        artist = result.find('span', class_="chart-element__information__artist text--truncate color--secondary").text
        rank = result.find('span', class_="chart-element__rank__number").text
        weeks = result.find('span', class_="chart-element__meta text--center color--secondary text--week").text

        df_billboard = df_billboard.append({'title':title, 'artist':artist,'rank':rank,'weeks_on_charts':weeks}, ignore_index=True)

    return df_billboard[:count]

# String manipulation / cleaning method
_remove_accents = lambda input_str: ''.join(
    (c for c in unicodedata.normalize('NFKD', input_str) if not unicodedata.combining(c)))
_clean_string = lambda s: set(re.sub(r'[^\w\s]', '', _remove_accents(s)).lower().split())
_jaccard = lambda set1, set2: float(len(set1 & set2)) / float(len(set1 | set2))


def search(entity_type: str, query: str):
    """
    Use the musicbrainz API to retrieve a JSON file containing album information
    :param entity_type: 'release' (as per API documentation)
    :param query: search query
    :return: JSON file
    """
    return requests.get(
        'http://musicbrainz.org/ws/2/{entity}/'.format(entity=entity_type),
        params={
            'fmt': 'json',
            'query': query
        }
    ).json()


def get_release_url(artist: str, title: str):
    """
    Gets the release url for a particular artist and album in the musibrainz database
    :param artist: artist name
    :param title: album title
    :return: release url (to scrap JSON from) or None if not found
    """
    type_ = 'release'
    search_results = search(type_, '%s AND artist:%s' % (title, artist))

    artist = _clean_string(artist)
    title = _clean_string(title)

    #     print("title = " + str(title) +' artist=' + str(artist))
    for item in search_results.get(type_ + 's', []):
        names = list()
        for artists in item['artist-credit']:
            if 'artist' in artists:
                names.append(_clean_string(artists['artist']['name']))
                for alias in artists['artist'].get('aliases', {}):
                    names.append(_clean_string(alias.get('name', '')))
        # print('  title=' + str(_clean_string(item['title'])) + ' names=' + ', '.join(itertools.chain(*names)))

        if _jaccard(_clean_string(item['title']), title) > 0.5 and \
                (any(_jaccard(artist, name) > 0.3 for name in names) or len(names) == 0):
            return 'http://musicbrainz.org/ws/2/{type}/{id}/'.format(id=item['id'], type=type_)

    return None

def getCountsData(artist: str, title: str):
        # Get url for album, if none do nothing
        url = get_release_url(artist, title)
        if url is None:
            return
        # discids contains the required information
        return requests.get(url,
                            params={
                                'inc': 'discids',
                                'fmt': 'json'
                            }
                            ).json()


def updateBillboardDf(dataframe: pd.DataFrame):
    dataframe['track_count'] = ''

    # Iterate through dataframe, getting JSON for each album
    for index, row in dataframe.iterrows():
        a = row['artist']
        t = row['title']

        raw_data = getCountsData(a, t)
        if raw_data is None:
            continue

        # Get track count from JSON
        if ('media' in raw_data):
            track_count = raw_data['media'][0]['track-count']
            row['track_count'] = track_count

        # Add Any Other data as needed (See API Documentation)


if __name__ == "__main__":
    # TODO - add input validation
    week = input("\nEnter the week in the format YYYY-MM-DD : ")
    count = int(input("Enter the number of top albums to show (max 200) : "))

    top_5_albums = get_billboard_top_albums_dataframe(week, count)
    # Allow display to show
    pd.set_option('display.width', 1000)
    pd.set_option('display.max_columns',1000)
    updateBillboardDf(top_5_albums)
    print("\nBillboard Top", str(count), "for the week", week, ":\n")
    print(top_5_albums)

