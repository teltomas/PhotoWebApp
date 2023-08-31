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

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db_connection():
    conn = sqlite3.connect('photowebapp.db')
    conn.row_factory = dict_factory
    return conn




####### FOR FRONTEND #######

# get necessary general info from db to store in global variables #
conn = get_db_connection()
page_info = conn.execute('SELECT page_name, person_name, small_descr, inst_link, face_link, yt_link FROM page_info WHERE id = 1;').fetchone()

conn.close()


print(page_info["page_name"])

# main page #

@app.route("/")
def main():

    # render main page #

    # get from db the index of the images to showcase in the main page #
    conn = get_db_connection()
    sc_img = conn.execute('SELECT * FROM gall_img_index WHERE gall_id = 1;').fetchall()
    conn.close()

    return render_template("/main.html", pageinfo = page_info, imgs = sc_img)



    




####### FOR USER APP MANAGEMENT #######
# Configure session to use filesystem (instead of signed cookies)
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'

# The maximum number of items the session stores 
# before it starts deleting some, default 500
app.config['SESSION_FILE_THRESHOLD'] = 10  

Session(app)