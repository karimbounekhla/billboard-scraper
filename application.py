from bs4 import BeautifulSoup
import requests
import numpy as np
import pandas as pd
# hide HTTPS warning
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_billboard_top_albums_dataframe(date: str='2001-06-02', count: int=5) -> pd.DataFrame:
    url = "https://www.billboard.com/charts/billboard-200/" + date
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

dfb = get_billboard_top_albums_dataframe()

print(dfb)
