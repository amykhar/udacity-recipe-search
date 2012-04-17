#Created by Amy Anuszewski as part of the Udacity CS101 course 2012

#This script provides the crawer functionality.  It scans up to 10000 pages on foodnetwork.com and indexes items
#found in the ingredients section of recipe pages.  The index is stored in an sqlite database.  To make it easier
#to configure, the max number of pages to scan, the html tags that signify the start end end of the ingredients section
#and the name of the database are set in configuration variables at the top of the script.

#This work is licensed under the
#Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License.
#To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
#or send a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import urllib
from tornado.database import Connection
from BeautifulSoup import BeautifulSoup as bs
import urlparse
import re

DATABASE = 'recipe_search'
HOSTNAME = 'localhost'
USER = 'root'
PASSWORD = ''
MAX_PAGES_TO_CRAWL = 10000
START_TERM = 'kv-ingred'
END_TERM = 'instructions'


def get_page(url):
    if url.find('.com') == -1:
        url = urlparse.urljoin('http://foodnetwork.com/', url)
    try:
        return urllib.urlopen(url).read()
    except:
        return ""


def better_strip(string):
    string = ''.join(bs(string).findAll(text=True))
    string = re.sub(r'[^\w\s]', '', string)
    return string


def crawl_web(seed):
    tocrawl = [seed]
    crawled = []
    graph = {}
    index = connect_db()
    while tocrawl:
        page = tocrawl.pop()
        if page not in crawled:
            content = get_page(page)
            if content:
                outlinks = get_all_links(content)
                add_page_to_index(index, page, content)
                graph[page] = outlinks
                union(tocrawl, outlinks)
            crawled.append(page)
        if len(crawled) > MAX_PAGES_TO_CRAWL:
            return index, graph
    return index, graph


def get_next_target(page):
    start_link = page.find('<a href=')
    if start_link == -1:
        return None, 0
    start_quote = page.find('"', start_link)
    end_quote = page.find('"', start_quote + 1)
    url = page[start_quote + 1:end_quote]
    return url, end_quote


def get_all_links(page):
    links = []
    soup = bs(page)
    title = soup.html.head.title
    for link in soup.findAll('a'):
        url = link.get('href')
        if url is None:
            continue
        if url.find('.com') != -1 or url.find('.net') != -1:
            continue  # only looking for relative links to stay onsite
        links.append(url)
    return links


def union(a, b):
    for e in b:
        if e not in a:
            a.append(e)


def add_page_to_index(index, url, content):
    print url
    temp_content = content
    temp_content = get_ingredients(temp_content)
    if temp_content == '':
        return
    temp_content = better_strip(temp_content)
    print temp_content
    words = temp_content.split()
    for word in words:
        add_to_index(index, word, url)


def get_ingredients(content):
    start = content.find(START_TERM)
    if start == -1:
        return ''
    end = content.find(END_TERM)
    return content[start:end]


def add_to_index(db, keyword, url):
    word_id = get_word_id(keyword, db)
    url_id = get_url_id(url, db)
    if url_id is None:
        insert_url(url, db)
    if word_id is None:
        insert_word(keyword, db)
        word_id = get_word_id(keyword, db)
        url_id = get_url_id(url, db)
    else:
        url_id = get_url_id(url, db)
    db.execute('insert into word_index(word_id,url_id) values(' + word_id + ',' + url_id + ')')


def connect_db():
    db = Connection(HOSTNAME,
                      DATABASE,
                      USER,
                      PASSWORD)
    return db


def get_word_id(word, db):
    word_id = db.query('select id from words where word = "' + word + '"')
    if len(word_id) > 0:
        word_id = str(word_id[0]['id'])
    else:
        word_id = None
    return word_id


def get_url_id(url, db):
    url_id = db.query('select id from urls where url = "' + url + '"')
    if len(url_id) > 0:
        url_id = str(url_id[0]['id'])
    else:
        url_id = None
    return url_id


def insert_url(url, db):
    db.execute('insert into urls (url) values ("' + url + '")')


def insert_word(word, db):
    db.execute('insert into words (word) values ("' + word + '")')


def main():
    print 'crawling...'
    index, graph = crawl_web('http://www.foodnetwork.com/recipes-and-cooking/index.html')
    print 'complete'


if __name__ == "__main__":
    main()
