import datetime
import time

from bs4 import BeautifulSoup
import psycopg2
from psycopg2 import Error
from selenium import webdriver as wd
from selenium.webdriver.common.by import By

from config import MY_FANDOMS, DATABASE_CONFIG

FICBOOK_URL = 'https://ficbook.net/requests-346578/popular'
DATE = datetime.date.today()

# Opens ficbook page 'popular ideas' and copies html body(simple request method have not worked)
options = wd.ChromeOptions()
options.page_load_strategy = 'eager'
driver = wd.Chrome(options=options)
driver.get(FICBOOK_URL)
time.sleep(1)
html = driver.find_element(By.TAG_NAME, 'body').get_attribute('outerHTML')
driver.quit()


soup = BeautifulSoup(html, 'html.parser')
divs_ideas = soup.find_all('div', class_='top-item-row')

sorted_ideas = []

# Sorts ideas by needed genres and fandoms
# Parses data from divs and structures it in dictionaries
for div in divs_ideas:

    if div.select('.ic_gen') or div.select('.ic_het'):
        idea_fandoms = [fandom.text for fandom in div.select('strong.title a span.text')]

        for my_fandom in MY_FANDOMS:

            if my_fandom in idea_fandoms:
                title = div.select('.visit-link')[0].text.replace("\n", "").strip()
                link = f"https://ficbook.net{div.select('.visit-link')[0]['href']}"
                likes = div.select('.request-likes-counter')[0].text
                genre = div.select('section.request-description div')[0].text.replace("\n", "").replace(" ", "")[15:].split(',')
                div_dict = {"title": title,
                            "link": link,
                            "likes": int(likes),
                            "fandoms": idea_fandoms,
                            "genre": genre,
                            }
                sorted_ideas.append(div_dict)
                break

newly_added_ideas = []
# Connects with a postgres database
# If idea don't exist - saves it to db
# If an idea already exists - updates like count for this idea in db
try:
    connection = psycopg2.connect(**DATABASE_CONFIG)
    cursor = connection.cursor()

    # selects all links that exist in db
    cursor.execute("SELECT link FROM ideas")
    saved_links = [data_set[0] for data_set in cursor.fetchall()]

    for idea in sorted_ideas:

        if idea['link'] not in saved_links:
            insert_query = "INSERT INTO ideas (link,title,likes,added_date,fandoms,genres) VALUES (%s,%s,%s,%s,%s,%s)"
            cursor.execute(
                insert_query,
                (idea['link'], idea['title'], idea['likes'], DATE, idea['fandoms'], idea['genre'])
            )
            newly_added_ideas.append(idea)

        else:
            update_query = "UPDATE ideas SET likes = %s WHERE link = %s AND likes != %s"
            cursor.execute(update_query, (idea['likes'], idea['link'], idea['likes']))

    connection.commit()

    # cursor.execute("SELECT * from ideas")
    # record = cursor.fetchall()
    # print("Результат", record)
except (Exception, Error) as error:
    print("Ошибка при работе с PostgreSQL: ", error)
finally:
    if connection:
        cursor.close()
        connection.close()