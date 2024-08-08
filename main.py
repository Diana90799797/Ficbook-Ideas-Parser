import datetime
import smtplib
import time
from email.message import EmailMessage
from typing import Dict, List

import psycopg2
from psycopg2 import Error
from bs4 import BeautifulSoup
from selenium import webdriver as wd
from selenium.webdriver.common.by import By

from config import (DATABASE_CONFIG, MY_FANDOMS,
                    RECIEVERS_EMAIL_LIST, SENDER_EMAIL,
                    SENDER_EMAIL_PASSWORD)

FICBOOK_URL = 'https://ficbook.net/requests-346578/popular'
SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587
DATE = datetime.date.today()

# Opens ficbook page 'popular ideas' and copies html body(simple request method have not worked)
def get_ficbook_html(url: str) -> str:
    """ Fetches html content of the Ficbook page 'популярные заявки' """
    options = wd.ChromeOptions()
    options.page_load_strategy = 'eager'
    driver = wd.Chrome(options=options)
    driver.get(url)
    time.sleep(1)
    html = driver.find_element(By.TAG_NAME, 'body').get_attribute('outerHTML')
    driver.quit()
    return html

def parse_ideas(html: str) -> List[Dict]:
    """Parses ideas from HTML content"""

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

def update_database(ideas: List[Dict]) -> List[Dict]:
    """ Updates the database with new ideas and returns newly added ideas"""
    newly_added_ideas = []
    # Connects with a postgres database
    # If idea don't exist - saves it to db
    # If an idea already exists - updates like count for this idea in db
    try:
        with psycopg2.connect(**DATABASE_CONFIG) as connection:
            with connection.cursor() as cursor:

                # selects all links that exist in db
                cursor.execute("SELECT link FROM ideas")
                saved_links = [data_set[0] for data_set in cursor.fetchall()]

                for idea in sorted_ideas:

                    if idea['link'] not in saved_links:
                        cursor.execute(
                            "INSERT INTO ideas (link,title,likes,added_date,fandoms,genres) VALUES (%s,%s,%s,%s,%s,%s)",
                            (idea['link'], idea['title'], idea['likes'], DATE, idea['fandoms'], idea['genre'])
                        )
                        newly_added_ideas.append(idea)

                    else:
                        update_query = "UPDATE ideas SET likes = %s WHERE link = %s AND likes != %s"
                        cursor.execute(update_query, (idea['likes'], idea['link'], idea['likes']))

                connection.commit()

    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL: ", error)
    return newly_added_ideas

def send_new_ideas_email(new_ideas: List[Dict]):
    """ Sends an email with a list of newly added ideas."""
    if not new_ideas:
        return  # No new ideas to send

    msg = EmailMessage()
    msg['Subject'] = 'New Ficbook Ideas!'
    msg['From'] = SENDER_EMAIL
    msg['To'] = ', '.join(RECIEVERS_EMAIL_LIST)

    # Format email content
    mail_content = "Here are the newly added Ficbook ideas:\n\n"
    for idea in new_ideas:
        mail_content += f"- **{idea['title']}** ({', '.join(idea['fandoms'])})\n"
        mail_content += f" - Link: {idea['link']}\n"
        mail_content += f" - Likes: {idea['likes']}\n\n"
    msg.set_content(mail_content)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        s.login(SENDER_EMAIL, SENDER_EMAIL_PASSWORD)
        s.sendmail(SENDER_EMAIL, RECIEVERS_EMAIL_LIST, msg.as_string())

def main():
    html = get_ficbook_html(FICBOOK_URL)
    ideas = parse_ideas(html)
    newly_added_ideas = update_database(ideas)
    send_new_ideas_email(newly_added_ideas)

if name == '__main__':
    main()