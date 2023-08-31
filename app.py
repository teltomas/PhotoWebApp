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
def get_db_connection():
    conn = sqlite3.connect('photowebapp.db')
    conn.row_factory = sqlite3.Row
    return conn


####### FOR FRONTEND #######

# get necessary general info from db to store in global variables #
conn = get_db_connection()
page_info = conn.execute('SELECT name, page_name, person_name, small_descr, inst_link, face_link, yt_link FROM page_info;').fetchall()
conn.close()

# main page #

@app.route("/")
def main():

    # render main page #



    




####### FOR USER APP MANAGEMENT #######
# Configure session to use filesystem (instead of signed cookies)
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=5)

# The maximum number of items the session stores 
# before it starts deleting some, default 500
app.config['SESSION_FILE_THRESHOLD'] = 10  

Session(app)