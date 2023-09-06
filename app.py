import sqlite3
from datetime import datetime
from flask import Flask, redirect, render_template, session, request
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Mail, Message


from front import date
# from back import

# configure app
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["date"] = date


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

# get the necessary general info from db to store in global variables #

journal_exist = False
events_exist = False

conn = get_db_connection()
page_info = conn.execute('SELECT * FROM page_info WHERE id = 1;').fetchone()
journals = conn.execute('SELECT * FROM articles WHERE type = "journal";').fetchone()
events = conn.execute('SELECT * FROM articles WHERE type = "event";').fetchone()

conn.close()


# Configuration of email sender

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = page_info['page_email']
app.config['MAIL_PASSWORD'] = ''
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

# Determine if there are journals or events articles to decide if the menu option is necessary #

if journals:
    journal_exist = True

if events:
    events_exist = True


# main page #

@app.route("/")
@app.route("/main")
def main():

    # render main page #

    # get from db the index of the images to showcase in the main page #
    conn = get_db_connection()
    sc_img = conn.execute('SELECT * FROM gall_img_index WHERE gall_id = 1;').fetchall()
    conn.close()

    return render_template("/main.html", pageinfo = page_info, journal = journal_exist, events = events_exist, imgs = sc_img)


@app.route("/journal")
def journal():

    # render journal page #

    # get from db the journal intros to display in page #
    conn = get_db_connection()
    journals = conn.execute('SELECT * FROM articles WHERE type = "journal" AND archived = False ORDER BY date DESC;').fetchall()
    conn.close()

    if len(journals) < 1:
        return render_template("/article.html", pageinfo = page_info, journal = journal_exist, events = events_exist, page_type = "Journal", flash_message = "No journal intros to display.")

    return render_template("/article.html", pageinfo = page_info, page_type = "Journal", journal = journal_exist, events = events_exist, articles = journals)


@app.route("/events")
def events():

    # render events page #

    # get from db the events intros to display in page #
    conn = get_db_connection()
    events = conn.execute('SELECT * FROM articles WHERE type = "event" AND archived = False ORDER BY date DESC;').fetchall()
    conn.close()

    if not events:
        return render_template("/article.html", pageinfo = page_info, page_type = "Events", journal = journal_exist, events = events_exist, flash_message = "No events to display yet.")

    return render_template("/article.html", pageinfo = page_info, journal = journal_exist, page_type = "Events", events = events_exist, articles = events)



@app.route("/about")
def about():

    # render about page with info already fetched from db in the page_info content #

     return render_template("/about.html", pageinfo = page_info, journal = journal_exist, events = events_exist)


@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "GET":
    # render contact page in case of get method #

        return render_template("/contact.html", pageinfo = page_info, journal = journal_exist, events = events_exist)
    
    if request.method == "POST":

        # fetch the info sent by the user #
        # sending the email requested by the user, config per demonstration in https://pythonbasics.org/flask-mail/ #

        try:        
            msg = Message(request.form.get("subject"), sender = page_info['page_email'], recipients = ['t_elt@hotmail.com'])
            msg.body = (request.form.get("message") + "\n\nSender email: \n" + request.form.get("email"))
            mail.send(msg)
        except:
            return render_template("/contact.html", pageinfo = page_info, journal = journal_exist, events = events_exist, flash_message = "Sorry! There was an error sending the message...")
        
        return render_template("/contact.html", pageinfo = page_info, journal = journal_exist, events = events_exist, flash_message = "Message sent. Thank you!")


@app.route("/galleries")
def gallery():

    return render_template("/gallery.html", pageinfo = page_info, journal = journal_exist, events = events_exist)



####### FOR USER APP MANAGEMENT #######
# Configure session to use filesystem (instead of signed cookies)
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'

# The maximum number of items the session stores 
# before it starts deleting some, default 500
app.config['SESSION_FILE_THRESHOLD'] = 10  

Session(app)