#Created by Amy Anuszewski as part of the Udacity CS101 course 2012

#This script provides the web interface for the recipe search engine.  It uses Flask and Sqlite as a front end.

#This work is licensed under the
#Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License.
#To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
#or send a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

from sqlite3 import dbapi2 as sqlite3
from contextlib import closing
import db_lib
from flask import Flask, request, g, redirect, \
     render_template, flash


# configuration
DATABASE = 'recipe_search.db'
DEBUG = True
USERNAME = 'admin'
PASSWORD = 'default'
SECRET_KEY = 'udacious'


app = Flask("__main__")
app.config.from_object(__name__)


@app.route("/")
def search():
    return render_template('search.html')



def connect_db():
    return sqlite3.connect(DATABASE)


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()


def search_database(query_terms):
    word_list = ",".join(query_terms)
    word_id_list = db_lib.query_db("select id from words where word in(" + word_list + ")", g.db, [])
    list_of_url_lists = []
    for word_id in word_id_list:
        url_query = "SELECT url from urls left join word_index on word_index.url_id = urls.id where word_index.word_id = " + str(word_id['id'])
        url_list = db_lib.query_db(url_query, g.db, [])
        list_of_url_lists.append(url_list)
    results = find_conjunction(list_of_url_lists)
    return results


def find_conjunction(list_of_url_lists):
    results_list = []
    number_of_lists = len(list_of_url_lists)
    for url in list_of_url_lists[0]:
        i = 1
        found = True
        while i < number_of_lists:
            if url not in list_of_url_lists[i]:
                found = False
            i += 1
        if found == True:
            if url['url'].find('http://') == -1:
                url = 'http://www.foodnetwork.com/' + url['url']
                results_list.append(url)
        found = True
    return results_list



@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()


@app.route('/search', methods=['POST'])
def lookup():
    query = request.form["query"]
    if query == '':
        flash('Please enter a search term')
        return redirect('/')
    query_terms = query.split()
    word_list = []
    for word in query_terms:
        word = "'" + word + "'"
        word_list.append(word)
    results = search_database(word_list)

    flash(query)
    return render_template('results.html', results=results)

if __name__ == "__main__":
    app.debug = True
    app.run()
