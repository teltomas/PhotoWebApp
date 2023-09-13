import os
import sqlite3
from datetime import datetime
from flask import Flask, redirect, render_template, session, request, abort
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Mail, Message


from front import date, capital
from back import validate_image

# configure app
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["date"] = date
app.jinja_env.filters["capital"] = capital

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

@app.route("/article")
def articles():

    # render article page #

    # get from the request the type of article to render #
    ar_type = request.args.get('artp', '')

    # get from db the article intros to display in page #
    conn = get_db_connection()
    articles = conn.execute('SELECT * FROM articles WHERE type = ? AND archived = 0 ORDER BY date DESC;', (ar_type,)).fetchall()
    conn.close()

    # display message if there are no articles #
    if len(articles) < 1:
        return render_template("/article.html",
                                pageinfo = page_info,
                                journal = journal_exist, 
                                events = events_exist, 
                                galls = gall_nav,
                                page_type = ar_type, 
                                flash_message = "No " + ar_type + " intros to display.")
    
    # render page with articles #
    return render_template("/article.html", 
                           pageinfo = page_info, 
                           page_type = ar_type, 
                           journal = journal_exist, 
                           events = events_exist, 
                           galls = gall_nav,
                           articles = articles)


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

    # split the quantity of images in three diferent arrays to display in the page grid #
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

    # render the gallery page #
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

@app.route("/ar_mngt", methods=["GET", "POST"])
def ar_mngmt():

    if request.args.get('artp', ''):
        ar_type = request.args.get('artp', '')

    if request.method == "GET":
 
        conn = get_db_connection()
        entries = conn.execute('SELECT id, title, date, content FROM articles WHERE type = ? AND archived = 0 ORDER BY date DESC;', (ar_type,)).fetchall()
        conn.close()

        flash_message = None

        if not entries:
            flash_message = "No entries to display."

        for row in entries:
            if len(row['content'])>150:
                row['content'] = row['content'][:150]+"..."

        return render_template("ar_mngt.html",
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            galls = gall_nav,
                            entries = entries,
                            ar_type = ar_type,
                            flash_message = flash_message)
    
    
    if request.method == "POST":

        ar_id = request.form.get("id")

        action = int(request.args.get('action', ''))

        conn = get_db_connection()
        article = conn.execute('SELECT * FROM articles WHERE id = ?;', (ar_id,)).fetchone()
        conn.close()

        ar_type = article['type']

        if action == 1: # edit article entry #
  
            # render article edit template with article data #
            return render_template("edit_entry.html",
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            galls = gall_nav,
                            article = article)
        
        if action == 2: # archive article entry #

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE articles SET archived = ? WHERE id = ?;', (True, ar_id,))
            conn.commit()
            conn.close()
        
        if action == 3: # save edited article entry #

            # get and confirm title contents #
            if request.form.get("title"):
                title = request.form.get("title")
            else:
                return render_template("edit_entry.html",
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            galls = gall_nav,
                            article = article,
                            flash_message = "Title required!")

            # get and confirm main contents #
            if request.form.get("content"):
                content = request.form.get("content")
            else:
                return render_template("edit_entry.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                article = article,
                                flash_message = "Content text required!")

            # get and confirm link contents - set null if empty #
            if request.form.get("link"):
                link = request.form.get("link")
            else:
                link = None

            # update info in the DB #

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE articles SET title = ?, content = ?, link = ? WHERE id = ?;', (title, content, link, ar_id,))
            conn.commit()
            conn.close()

            # img file upload handling implemented as shown here https://blog.miguelgrinberg.com/post/handling-file-uploads-with-flask #

            if request.files['img']:
                
                img = request.files['img']
                
                filename = img.filename

                if filename != '':

                    file_ext = os.path.splitext(filename)[1]
                    if file_ext not in app.config['UPLOAD_EXTENSIONS'] or \
                        file_ext != validate_image(img.stream):
                        
                        return render_template("ar_mngt.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                ar_type = ar_type,
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

        print(ar_type)
        return redirect("ar_mngt?artp=" + ar_type)
    

@app.route("/ar_new", methods=["GET", "POST"])
def ar_new():

    if not request.args.get('artp', '') and not request.form.get("ar_type"):
        return redirect("management")

    ar_type = request.args.get('artp', '')

    if request.method == "GET":

        return render_template("ar_new.html",
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            ar_type = ar_type,
                            galls = gall_nav)
    
    if request.method == "POST":

        ar_type = request.form.get("ar_type")

        if request.form.get("title"):
            title = request.form.get("title")
        else:
            return render_template("ar_new.html",
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            galls = gall_nav,
                            ar_type = ar_type,
                            flash_message = "Title required!")
        
        if request.form.get("content"):
            content = request.form.get("content")
        else:
            return render_template("ar_new.html?artp=" + ar_type,
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
        cur.execute('INSERT INTO articles (type, title, content, archived, link) VALUES (?, ?, ?, ?, ?);', (ar_type, title, content, False, link,))
        conn.commit()
        ar_id = conn.execute('SELECT id FROM articles ORDER BY id DESC;').fetchone()
        conn.close()

        ar_id = ar_id['id']


        # img file upload handling as shown here https://blog.miguelgrinberg.com/post/handling-file-uploads-with-flask #

        if request.files['img']:
            
            img = request.files['img']
            
            filename = img.filename

            if filename != '':

                file_ext = os.path.splitext(filename)[1]
                if file_ext not in app.config['UPLOAD_EXTENSIONS'] or \
                    file_ext != validate_image(img.stream):
                    
                    return render_template("ar_mngt.html?artp=" + ar_type,
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            galls = gall_nav,
                            flash_message = "New article successfully posted to " + ar_type + " BUT invalid image discarded.")

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

        return redirect("ar_mngt?artp=" + ar_type)
    
@app.route("/archive", methods=["GET", "POST"])
def archive():

    # get from db the archived articles #
    conn = get_db_connection()
    archived_ar = conn.execute('SELECT * FROM articles WHERE archived = 1 ORDER BY id DESC;', ).fetchall()
    conn.close()

    if request.method == "GET":

        if not archived_ar:

            return render_template("/archive.html",
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            galls = gall_nav,
                            flash_message = "Archive is empty.")
        
        for row in archived_ar:
            if len(row['content'])>150:
                row['content'] = row['content'][:150]+"..."
            
        return render_template("/archive.html",
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            galls = gall_nav,
                            entries = archived_ar)
    
    if request.method == "POST":

        action = request.args.get('action', '')
        ar_id = request.form.get("id")

        if action == "repub":

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE articles SET archived = ? WHERE id = ?;', (False, ar_id,))
            conn.commit()
            conn.close()


        if action == "del": # delete article entry #

            # get the info from the db to check if article has an image #
            conn = get_db_connection()
            image = conn.execute('SELECT image FROM articles WHERE id = ?;', (ar_id,) ).fetchone()
            conn.close()

            # delete article image if exists #
            if image['image']:
                cwd = os.getcwd()
                os.remove(cwd+"/static/images/" + str(image['image']) + ".jpg") 

            # remove entry from db #
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('DELETE FROM articles WHERE id = ?;', (ar_id,))
            conn.commit()
            conn.close()

    return redirect("/archive")