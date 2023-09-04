import sqlite3
from datetime import datetime
from flask import Flask, redirect, render_template, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

# from front import
# from back import

# configure app
app = Flask(__name__)


# configure database management

# arrange the data from the db in dictionaries #
# as documented in https://docs.python.org/3/library/sqlite3.html#sqlite3-howto-row-factory #
# and https://stackoverflow.com/questions/3300464/how-can-i-get-dict-from-sqlite-query #

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

# database in sqlite config as documented in #
# https://www.digitalocean.com/community/tutorials/how-to-use-an-sqlite-database-in-a-flask-application #

def get_db_connection():
    conn = sqlite3.connect('photowebapp.db')
    conn.row_factory = dict_factory
    return conn




####### FOR FRONTEND #######

# get the necessary general info from db to store in global variable #
conn = get_db_connection()
page_info = conn.execute('SELECT * FROM page_info WHERE id = 1;').fetchone()

conn.close()


# main page #

@app.route("/")
@app.route("/main")
def main():

    # render main page #

    # get from db the index of the images to showcase in the main page #
    conn = get_db_connection()
    sc_img = conn.execute('SELECT * FROM gall_img_index WHERE gall_id = 1;').fetchall()
    conn.close()

    return render_template("/main.html", pageinfo = page_info, imgs = sc_img)


@app.route("/journal")
def journal():

    # render journal page #

    # get from db the journal intros to disoplay in page #
    conn = get_db_connection()
    journals = conn.execute('SELECT * FROM articles WHERE type = "journal";').fetchall()
    conn.close()

    if len(journals) < 1:
        return render_template("/article.html", pageinfo = page_info, flash_message = "No journal intros to display.")

    return render_template("/article.html", pageinfo = page_info)



####### FOR USER APP MANAGEMENT #######
# Configure session to use filesystem (instead of signed cookies)
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'

# The maximum number of items the session stores 
# before it starts deleting some, default 500
app.config['SESSION_FILE_THRESHOLD'] = 10  

Session(app)