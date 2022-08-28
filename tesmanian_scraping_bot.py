#!/usr/bin/env python3
# Scrapping https://www.tesmanian.com/

import requests
import telebot
import sys
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from time import sleep
from threading import Thread
from threading import Event


class Bot:

    def __init__(self, token):
        self.token = token
        self.bot = telebot.TeleBot(token)
        self.channels = []

    def add_chanel(self, channel):
        self.channels.append(channel)

    def post_message_to_channel(self, message: str):
        for channel in self.channels:
            self.bot.send_message(chat_id=channel,
                                  text=message,
                                  parse_mode="markdown",
                                  disable_web_page_preview=True)
            sleep(1)


def content_update(request_session: requests.Session, url: str, event: Event, request_timeout: int):
    while True:
        global current_articles
        page = request_session.get(url, headers=headers)
        current_articles = page_parsing(page.text)
        event.set()
        sleep(request_timeout)


def page_parsing(page: str) -> dict:
    content = {}
    soup = BeautifulSoup(page, "html.parser")
    for article in soup.find_all("div", attrs={"class": "article clearfix"}):
        for h3 in article.find_all("h3", attrs={"class": "sub_title"}):
            for hyperlink in h3.find_all("a"):
                content.update({main_page_link + hyperlink.get("href"): hyperlink.text})
    return content


def articles_update(bot: Bot, event: Event):
    while True:
        global articles
        event.wait()
        message = "Get #new articles on the page:"
        for link, text in current_articles.items():
            if link not in articles.keys():
                articles.update({link: text})
                message += f"\n[{text}]({link})\n"
        if message != "Get #new articles on the page:":
            bot.post_message_to_channel(message)
        message = "Articles was #deleted from the page:"
        for link, text in articles.items():
            if link not in current_articles.keys():
                del articles[link]
                message += f"\n[{text}]({link})\n"
        if message != "Articles was #deleted from the page:":
            bot.post_message_to_channel(message)
        event.clear()


if __name__ == '__main__':
    articles = {}
    current_articles = {}
    session = requests.Session()
    main_page_link = "https://www.tesmanian.com/"
    user = UserAgent()
    headers = {'user-agent': user.random}
    data = {
        "form_sent": 1,
        "req_username": "login",
        "req_password": "password"
    }
    response = session.post(main_page_link, data=data, headers=headers)
    get_page_event = Event()
    timeout = 15
    get_page_thread = Thread(target=content_update,
                             args=(session, main_page_link, get_page_event, timeout),
                             daemon=True).start()
    bot = Bot("token")
    bot.add_chanel("@channel")
    articles_update_thread = Thread(target=articles_update,
                                    args=(bot, get_page_event))
    articles_update_thread.start()
    try:
        articles_update_thread.join()
    except KeyboardInterrupt:
        sys.exit(0)

