import time

from bs4 import BeautifulSoup
from selenium import webdriver as wd
from selenium.webdriver.common.by import By

from config import MY_FANDOMS

# Opens ficbook page 'popular ideas' and copies html body(simple request method have not worked)
options = wd.ChromeOptions()
options.page_load_strategy = 'eager'
driver = wd.Chrome(options=options)
driver.get('https://ficbook.net/requests-346578/popular')
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
