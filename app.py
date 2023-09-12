import os
import sqlite3
from datetime import datetime
from flask import Flask, redirect, render_template, session, request, abort
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Mail, Message


from front import date
from back import validate_image

# configure app
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["date"] = date

# Config the app file upload handling: max size 10MB; file type restricted to *.jpg, *.jpeg and *.ico; file upload folder path 

app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 10
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg', '.ico']
app.config['UPLOAD_PATH'] = '/static/images/'


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
page_info = conn.execute('SELECT * FROM page_info WHERE id = 1;').fetchone() # for the general page info #
journals = conn.execute('SELECT * FROM articles WHERE type = "journal" AND archived = 0;').fetchone() # determine if there are journals in db to activate the journal nav item #
events = conn.execute('SELECT * FROM articles WHERE type = "event" AND archived = 0;').fetchone() # determine if there are events in db to activate the events nav item #
gall_nav = conn.execute('SELECT id, title FROM galleries WHERE id != 1;').fetchall() # get how many galleries exist in db to fill the galleries nav itens #

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

    return render_template("/main.html",
                            pageinfo = page_info,
                            journal = journal_exist,
                            events = events_exist,
                            galls = gall_nav,
                            imgs = sc_img)


@app.route("/journal")
def journal():

    # render journal page #

    # get from db the journal intros to display in page #
    conn = get_db_connection()
    journals = conn.execute('SELECT * FROM articles WHERE type = "journal" AND archived = False ORDER BY date DESC;').fetchall()
    conn.close()

    if len(journals) < 1:
        return render_template("/article.html",
                                pageinfo = page_info,
                                journal = journal_exist, 
                                events = events_exist, 
                                galls = gall_nav,
                                page_type = "Journal", 
                                flash_message = "No journal intros to display.")

    return render_template("/article.html", 
                           pageinfo = page_info, 
                           page_type = "Journal", 
                           journal = journal_exist, 
                           events = events_exist, 
                           galls = gall_nav,
                           articles = journals)


@app.route("/events")
def events():

    # render events page #

    # get from db the events intros to display in page #
    conn = get_db_connection()
    events = conn.execute('SELECT * FROM articles WHERE type = "event" AND archived = False ORDER BY date DESC;').fetchall()
    conn.close()

    if not events:
        return render_template("/article.html", 
                               pageinfo = page_info, 
                               page_type = "Events", 
                               journal = journal_exist, 
                               events = events_exist, 
                               galls = gall_nav,
                               flash_message = "No events to display yet.")

    return render_template("/article.html", 
                           pageinfo = page_info, 
                           journal = journal_exist, 
                           page_type = "Events", 
                           events = events_exist, 
                           galls = gall_nav,
                           articles = events)



@app.route("/about")
def about():

    # render about page with info already fetched from db in the page_info content #

     return render_template("/about.html", 
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            galls = gall_nav)


@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "GET":
    # render contact page in case of get method #

        return render_template("/contact.html", 
                               pageinfo = page_info, 
                               journal = journal_exist, 
                               galls = gall_nav,
                               events = events_exist)
    
    if request.method == "POST":

        # fetch the info sent by the user #
        # sending the email requested by the user, config per demonstration in https://pythonbasics.org/flask-mail/ #

        try:        
            msg = Message(request.form.get("subject"), sender = page_info['page_email'], recipients = ['t_elt@hotmail.com'])
            msg.body = (request.form.get("message") + "\n\nSender email: \n" + request.form.get("email"))
            mail.send(msg)
        except:
            return render_template("/contact.html", 
                                   pageinfo = page_info, 
                                   journal = journal_exist, 
                                   events = events_exist, 
                                   galls = gall_nav,
                                   flash_message = "Sorry! There was an error sending the message...")
        
        return render_template("/contact.html", 
                               pageinfo = page_info, 
                               journal = journal_exist, 
                               events = events_exist, 
                               galls = gall_nav,
                               flash_message = "Message sent. Thank you!")


@app.route("/galleries")
def gallery():

    # fetch from address input the gallery id and get from the db the photos from the gallery requested #
    gall_id = request.args.get('id', '')

    conn = get_db_connection()
    gall_info = conn.execute('SELECT * FROM galleries WHERE id = ?', (gall_id,)).fetchone()
    imgs_info = conn.execute('SELECT * FROM gall_img_index JOIN images ON gall_img_index.img_id = images.id WHERE gall_id = ? ORDER BY img_id DESC', (gall_id,)).fetchall()
    conn.close()

    imgs_col1 = []
    imgs_col2 = []
    imgs_col3 = []

    if imgs_info:
        i = 0
        while i < len(imgs_info):
            imgs_col1.append(imgs_info[i])
            if i+1 < len(imgs_info): 
                imgs_col2.append(imgs_info[i+1])
            if i+2 < len(imgs_info): 
                imgs_col3.append(imgs_info[i+2])
            i = i + 3


    return render_template("/gallery.html", 
                           pageinfo = page_info, 
                           journal = journal_exist, 
                           events = events_exist,
                           galls = gall_nav,
                           gall_info = gall_info,
                           imgs_info = imgs_info,
                           imgs_col1 = imgs_col1,
                           imgs_col2 = imgs_col2,
                           imgs_col3 = imgs_col3)



####### FOR USER APP MANAGEMENT #######
# Configure session to use filesystem (instead of signed cookies)
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'

# The maximum number of items the session stores 
# before it starts deleting some, default 500
app.config['SESSION_FILE_THRESHOLD'] = 10  

Session(app)

@app.route("/management")
def mngmt():

    return render_template("mngmt_main.html",
                           pageinfo = page_info, 
                           journal = journal_exist, 
                           events = events_exist,
                           galls = gall_nav)

@app.route("/jnl_mngt")
def jn_mngmt():

    return render_template("jnl_mngt.html",
                           pageinfo = page_info, 
                           journal = journal_exist, 
                           events = events_exist,
                           galls = gall_nav)

@app.route("/jn_new", methods=["GET", "POST"])
def jn_new():

    if request.method == "GET":

        return render_template("jn_new.html",
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            galls = gall_nav)
    
    if request.method == "POST":

        if request.form.get("title"):
            title = request.form.get("title")
        else:
            return render_template("jn_new.html",
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            galls = gall_nav,
                            flash_message = "Title required!")
        
        if request.form.get("content"):
            content = request.form.get("content")
        else:
            return render_template("jn_new.html",
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            galls = gall_nav,
                            flash_message = "Content text required!")
        
        if request.form.get("link"):
            link = request.form.get("link")
        else:
            link = None

        # add journal info to the DB and get the article ID #

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO articles (type, title, content, archived, link) VALUES (?, ?, ?, ?, ?);', ("journal", title, content, 0, link,))
        conn.commit()
        ar_id = conn.execute('SELECT id FROM articles ORDER BY id DESC;').fetchone()
        conn.close()

        ar_id = ar_id['id']


        # img file upload handling implemented as shown here https://blog.miguelgrinberg.com/post/handling-file-uploads-with-flask #

        if request.files['img']:
            
            img = request.files['img']
            
            filename = img.filename

            if filename != '':

                file_ext = os.path.splitext(filename)[1]
                if file_ext not in app.config['UPLOAD_EXTENSIONS'] or \
                    file_ext != validate_image(img.stream):
                    
                    return render_template("jn_new.html",
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            galls = gall_nav,
                            flash_message = "New article successfully posted to Journal BUT invalid image discarded.")

        fname = "article" + str(ar_id) + ".jpg"
        dbname= "article" + str(ar_id)

        # change path with -- app.config['UPLOAD_PATH'] -- #

        cwd = os.getcwd()

        img.save(os.path.join((cwd+"/static/images/"), fname)) 

        # update article in db with image name #

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('UPDATE articles SET image = ? WHERE id = ?;', (dbname, ar_id,))
        conn.commit()
        conn.close()

        return render_template("jn_new.html",
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            galls = gall_nav,
                            flash_message = "New article successfully posted to Journal")


@app.route("/ev_mngt")
def ev_mngmt():

    return render_template("ev_mngt.html",
                           pageinfo = page_info, 
                           journal = journal_exist, 
                           events = events_exist,
                           galls = gall_nav)

@app.route("/ev_new", methods=["GET", "POST"])
def ev_new():

    if request.method == "GET":

        return render_template("ev_new.html",
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            galls = gall_nav)
    
    if request.method == "POST":

        if request.form.get("title"):
            title = request.form.get("title")
        else:
            return render_template("ev_new.html",
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            galls = gall_nav,
                            flash_message = "Title required!")
        
        if request.form.get("content"):
            content = request.form.get("content")
        else:
            return render_template("ev_new.html",
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            galls = gall_nav,
                            flash_message = "Content text required!")
        
        if request.form.get("link"):
            link = request.form.get("link")
        else:
            link = None

        # add event info to the DB and get the article ID #

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO articles (type, title, content, archived, link) VALUES (?, ?, ?, ?, ?);', ("event", title, content, 0, link,))
        conn.commit()
        ar_id = conn.execute('SELECT id FROM articles ORDER BY id DESC;').fetchone()
        conn.close()

        ar_id = ar_id['id']


        # img file upload handling implemented as shown here https://blog.miguelgrinberg.com/post/handling-file-uploads-with-flask #

        if request.files['img']:
            
            img = request.files['img']
            
            filename = img.filename

            if filename != '':

                file_ext = os.path.splitext(filename)[1]
                if file_ext not in app.config['UPLOAD_EXTENSIONS'] or \
                    file_ext != validate_image(img.stream):
                    
                    return render_template("ev_new.html",
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            galls = gall_nav,
                            flash_message = "New article successfully posted to Events BUT invalid image discarded.")

        fname = "article" + str(ar_id) + ".jpg"
        dbname= "article" + str(ar_id)

        # change path with -- app.config['UPLOAD_PATH'] -- #

        cwd = os.getcwd()

        img.save(os.path.join((cwd+"/static/images/"), fname)) 

        # update article in db with image name #

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('UPDATE articles SET image = ? WHERE id = ?;', (dbname, ar_id,))
        conn.commit()
        conn.close()

        return render_template("ev_new.html",
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            galls = gall_nav,
                            flash_message = "New article successfully posted to Events")