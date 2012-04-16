import urllib
from sqlite3 import dbapi2 as sqlite3
from BeautifulSoup import BeautifulSoup as bs
import urlparse
import re
import db_lib

DATABASE = 'recipe_search.db'
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
        db.execute('insert into word_index(word_id,url_id) values(?,?)',
                   [word_id, url_id])
    else:
        url_id = get_url_id(url, db)
        db.execute('insert into word_index(word_id,url_id) values(?,?)',
            [word_id, url_id])

    db.commit()


def connect_db():
    return sqlite3.connect(DATABASE)


def get_word_id(word, db):
    word_id = db_lib.query_db('select id from words where word = ?', db, [word], one=True)
    if word_id is not None:
        word_id = word_id['id']
    return word_id


def get_url_id(url, db):
    url_id = db_lib.query_db('select id from urls where url = ?', db,
                [url], one=True)
    if url_id is not None:
        url_id = url_id['id']
    return url_id


def insert_url(url, db):
    db.execute('insert into urls (url) values (?)',
                 [url])


def insert_word(word, db):
    db.execute('insert into words (word) values (?)',
                 [word])


def main():
    print 'crawling...'
    index, graph = crawl_web('http://www.foodnetwork.com/recipes-and-cooking/index.html')
    print 'complete'


if __name__ == "__main__":
    main()
