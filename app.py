import os
import sqlite3
from datetime import datetime
from flask import Flask, redirect, render_template, session, request, abort
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Mail, Message


from front import date, capital, dblink
from back import validate_image, get_db_connection, image_resize, createthumb

# configure app
app = Flask(__name__) 

# Custom filter
app.jinja_env.filters["date"] = date
app.jinja_env.filters["capital"] = capital
app.jinja_env.filters["http"] = dblink

# Config the app file upload handling: max size 10MB; file type restricted to *.jpg, *.jpeg and *.ico; file upload folder path 

app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 10
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg', '.png', '.ico']
app.config['UPLOAD_PATH'] = '/static/images/'


####### FOR FRONTEND #######

# get the necessary general info from db to store in global variables #

journal_exist = False
events_exist = False

conn = get_db_connection()
page_info = conn.execute('SELECT page_name, small_descr, about, inst_link, face_link, yt_link, tweet_link, px_link, bhnc_link, tumblr_link, flickr_link, about_img, prof_pic, legal, copyright, page_email FROM page_info WHERE id = 1;').fetchone() # for the general page info #
journals = conn.execute('SELECT * FROM articles WHERE type = "journal" AND archived = 0;').fetchone() # determine if there are journals in db to activate the journal nav item #
events = conn.execute('SELECT * FROM articles WHERE type = "event" AND archived = 0;').fetchone() # determine if there are events in db to activate the events nav item #
gall_nav = conn.execute('SELECT id, title FROM galleries WHERE id != 1;').fetchall() # get how many galleries exist in db to fill the galleries nav itens #
page_conf = conn.execute('SELECT email, page_email, page_email_hash FROM page_info WHERE id = 1;').fetchone() # for the general page info #

conn.close()

# Configuration of email sender

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = page_conf['page_email']
app.config['MAIL_PASSWORD'] = page_conf['page_email_hash']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

# Determine if there are journals or events articles to decide if the menu option is necessary #

if journals:
    journal_exist = True

if events:
    events_exist = True

# define global variables #

cwd = os.getcwd() # get main working directory #

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
                        galls = gall_nav,
                        )


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
            msg = Message(request.form.get("subject"), sender = page_info['page_email'], recipients = [page_conf['email']])
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

    # render main management page #
    return render_template("mngmt_main.html",
                           pageinfo = page_info, 
                           journal = journal_exist, 
                           events = events_exist,
                           galls = gall_nav)


@app.route("/ar_mngt", methods=["GET", "POST"])
def ar_mngmt():

    # management of the existing articles - both events and journal entries #

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
                            ar_type = ar_type,
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
                            ar_type = ar_type,
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
                                ar_type = ar_type,
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

                img.save(os.path.join((cwd+app.config['UPLOAD_PATH']), fname)) 

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

    # creation of new articles #

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
            return render_template("ar_new.html",
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            galls = gall_nav,
                            ar_type = ar_type,
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
                    
                    return render_template("ar_mngt.html",
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            galls = gall_nav,
                            ar_type = ar_type,
                            flash_message = "New article successfully posted to " + ar_type + " BUT invalid image discarded.")

            fname = "article" + str(ar_id) + ".jpg"
            dbname= "article" + str(ar_id)

            img.save(os.path.join((cwd+app.config['UPLOAD_PATH']), fname)) 

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
                
                os.remove(cwd+"/static/images/" + str(image['image']) + ".jpg") 

            # remove entry from db #
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('DELETE FROM articles WHERE id = ?;', (ar_id,))
            conn.commit()
            conn.close()

    return redirect("/archive")

@app.route("/pg_mngt", methods=["GET"])
def pg_mngt():

    # render page of aspect and base info management selection #
    return render_template("/pg_mngt.html",
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            galls = gall_nav,
                            )

@app.route("/profile_mngt", methods=["GET", "POST"])
def profile_mngt():

    # update info variables to fill forms #

    conn = get_db_connection()
    page_info = conn.execute('SELECT * FROM page_info WHERE id = 1;').fetchone() # for the general page info #
    conn.close()

    if request.method == "GET":

        # render page of profile info management #
        return render_template("/profile_mngt.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                )
    
    if request.method == "POST":

        # get which action was requested and proceed with change #
        action = request.args.get('action', '')

        if action == "name":

            if not request.form.get("pg_name"):

                return render_template("/profile_mngt.html",
                                        pageinfo = page_info, 
                                        journal = journal_exist, 
                                        events = events_exist,
                                        galls = gall_nav,
                                        flash_message = "Page name input required"
                                        )
            
            else:
                pg_name = request.form.get("pg_name")           

                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute('UPDATE page_info SET page_name = ? WHERE id = 1;', (pg_name,))
                conn.commit()
                conn.close() 

            return redirect("/profile_mngt")

        if action == "description":

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE page_info SET small_descr = ? WHERE id = 1;', (request.form.get("pg_descr"),))
            conn.commit()
            conn.close()

            return redirect("/profile_mngt")

        if action == "aboutcontent":

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE page_info SET about = ? WHERE id = 1;', (request.form.get("abttxt"),))
            conn.commit()
            conn.close()

            return redirect("/profile_mngt")

        if action == "aboutphoto":

            if request.files['abimg']:
            
                img = request.files['abimg']
                
                filename = img.filename 

                if filename != '':

                    file_ext = os.path.splitext(filename)[1]
                    if file_ext not in app.config['UPLOAD_EXTENSIONS'] or \
                        file_ext != validate_image(img.stream):
                        
                        return render_template("profile_mngt.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                flash_message = "Failed to upload image.")

                fname = "0.jpg"

                path = os.path.join((cwd+app.config['UPLOAD_PATH']), fname)

                img.save(path)

                image_resize(path, 1000) 

                if not page_info['about_img']:

                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute('UPDATE page_info SET about_img = ? WHERE id = 1;', (True,))
                    conn.commit()
                    conn.close() 

            return redirect("/profile_mngt") 
        
        if action == "delabtph":

            if os.path.exists(cwd + app.config['UPLOAD_PATH'] + "0.jpg"):

                os.remove(cwd + app.config['UPLOAD_PATH'] + "0.jpg")

                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute('UPDATE page_info SET about_img = ? WHERE id = 1;', (False,))
                conn.commit()
                conn.close()

            return redirect("/profile_mngt")

        if action == "profphoto":

            if request.files['profimg']:
            
                img = request.files['profimg']
                
                filename = img.filename 

                if filename != '':

                    file_ext = os.path.splitext(filename)[1]
                    if file_ext not in app.config['UPLOAD_EXTENSIONS'] or \
                        file_ext != validate_image(img.stream):
                        
                        return render_template("profile_mngt.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                flash_message = "Failed to upload image.")

                fname = "1" + os.path.splitext(filename)[1]

                path = os.path.join((cwd+app.config['UPLOAD_PATH']), fname)

                img.save(path)

                image_resize(path, 600) 

                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute('UPDATE page_info SET prof_pic = ? WHERE id = 1;', (fname,))
                conn.commit()
                conn.close() 

            return redirect("/profile_mngt") 

        if action == "insta":

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE page_info SET inst_link = ? WHERE id = 1;', (request.form.get("instalink"),))
            conn.commit()
            conn.close()

            return redirect("/profile_mngt")
        
        if action == "face":
                
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE page_info SET face_link = ? WHERE id = 1;', (request.form.get("facelink"),))
            conn.commit()
            conn.close()

            return redirect("/profile_mngt")

        if action == "ytb":

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE page_info SET yt_link = ? WHERE id = 1;', (request.form.get("ytblink"),))
            conn.commit()
            conn.close()

            return redirect("/profile_mngt")

        if action == "tweet":

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE page_info SET tweet_link = ? WHERE id = 1;', (request.form.get("tweetlink"),))
            conn.commit()
            conn.close()

            return redirect("/profile_mngt")

        if action == "px":

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE page_info SET px_link = ? WHERE id = 1;', (request.form.get("500pxlink"),))
            conn.commit()
            conn.close()

            return redirect("/profile_mngt")

        if action == "bhnc":
   
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE page_info SET bhnc_link = ? WHERE id = 1;', (request.form.get("bhnclink"),))
            conn.commit()
            conn.close()

            return redirect("/profile_mngt")

        if action == "flickr":

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE page_info SET flickr_link = ? WHERE id = 1;', (request.form.get("flickrlink"),))
            conn.commit()
            conn.close()

            return redirect("/profile_mngt")

        if action == "tumblr":

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE page_info SET tumblr_link = ? WHERE id = 1;', (request.form.get("tumblrlink"),))
            conn.commit()
            conn.close()

            return redirect("/profile_mngt")
        
        return redirect("/profile_mngt")
    
    return redirect("/profile_mngt")

@app.route("/base_mngt", methods=["GET", "POST"])
def base_mngt():

    # update info variables to fill forms #

    conn = get_db_connection()
    page_info = conn.execute('SELECT * FROM page_info WHERE id = 1;').fetchone() # for the general page info #
    conn.close()

    if request.method == "GET":

        # render page of profile info management #
        return render_template("/base_mngt.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                )
    
    if request.method == "POST":

        action = request.args.get('action', '')

        if action == "pgemail":

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE page_info SET email = ? WHERE id = 1;', (request.form.get("email"),))
            conn.commit()
            conn.close()

            return redirect("/base_mngt")
        
        if action == "confemail":

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE page_info SET page_email = ? WHERE id = 1;', (request.form.get("cfemail"),))
            conn.commit()
            conn.close()

            return redirect("/base_mngt")
        
        if action == "confemailkey":

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE page_info SET page_email_hash = ? WHERE id = 1;', (request.form.get("emailkey"),))
            conn.commit()
            conn.close()

            return render_template("/base_mngt.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                flash_message = "Email key updated"
                                )
        
        if action == "passchange":

            if not check_password_hash(page_info['hash'], request.form.get("cpass")):

                return render_template("/base_mngt.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                flash_message = "Wrong password"
                                )
            
            if request.form.get("npass") != request.form.get("repass"):

                return render_template("/base_mngt.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                flash_message = "New password fields don't match"
                                )
            
            # check if password meets the requirements - 8 letters or numbers with at least 1 number #
            nkey = request.form.get("npass")
            count_numb = 0
            for i in nkey:
                if i.isnumeric():
                    count_numb+=1
        
            if (len(nkey) < 8 or count_numb < 1 or count_numb == len(nkey)):

                return render_template("/base_mngt.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                flash_message = "New password does not meet the requirements"
                                )
            
            else:

                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute('UPDATE page_info SET hash = ? WHERE id = 1;', (generate_password_hash(nkey),))
                conn.commit()
                conn.close()

            return render_template("/base_mngt.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                flash_message = "Password updated"
                                )
        
        if action == "legal":

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE page_info SET legal = ? WHERE id = 1;', (request.form.get("pg_legal"),))
            conn.commit()
            conn.close()

            return redirect("/base_mngt")
        
        if action == "copy":

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE page_info SET copyright = ? WHERE id = 1;', (request.form.get("pg_copy"),))
            conn.commit()
            conn.close()

            return redirect("/base_mngt")

    return redirect("/base_mngt")

@app.route("/aspect_mngt", methods=["GET", "POST"])
def aspect_mngt():

    if request.method == "GET":

        return render_template("/aspect_mngt.html",
                               pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav)
    
    if request.method == "POST":

        action = request.args.get('action', '')

        if action == "banner":

            if request.files['heroimg']:
            
                img = request.files['heroimg']
                
                filename = img.filename 

                if filename != '':

                    file_ext = os.path.splitext(filename)[1]
                    if file_ext not in app.config['UPLOAD_EXTENSIONS'] or \
                        file_ext != validate_image(img.stream):
                        
                        return render_template("aspect_mngt.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                flash_message = "Failed to upload image.")

                fname = "2.jpg"

                path = os.path.join((cwd+app.config['UPLOAD_PATH']), fname)

                img.save(path)

            return render_template("/aspect_mngt.html",
                                pageinfo = page_info, 
                                    journal = journal_exist, 
                                    events = events_exist,
                                    galls = gall_nav)
    
        if action == "ico":

            if request.files['ico']:
            
                img = request.files['ico']
                
                filename = img.filename 

                if filename != '':

                    file_ext = os.path.splitext(filename)[1]
                    if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                        
                        return render_template("aspect_mngt.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                flash_message = "Failed to upload image.")

                fname = "favicon.ico"

                path = os.path.join((cwd+"static/icons/"), fname)

                img.save(path)

            return render_template("/aspect_mngt.html",
                                pageinfo = page_info, 
                                    journal = journal_exist, 
                                    events = events_exist,
                                    galls = gall_nav)
    
        return render_template("/aspect_mngt.html",
                                pageinfo = page_info, 
                                    journal = journal_exist, 
                                    events = events_exist,
                                    galls = gall_nav)
    
@app.route("/gall_mngt", methods=["GET", "POST"])
def gall_mngt():

    conn = get_db_connection()
    galleries = conn.execute('SELECT * FROM galleries ORDER BY id DESC;').fetchall()
    img_gall = conn.execute('SELECT * FROM gall_img_index;').fetchall()
    images = conn.execute('SELECT id, title FROM images WHERE id > 2 ORDER BY id DESC;').fetchall()
    conn.close()

    flash_message = None

    if not galleries:
        flash_message = "There are no galleries to display."

    for row in galleries:
        if len(row['description']) > 100:
            row['description'] = row['description'][:100] + "..."

    if request.method == "GET":

        return render_template("/gall_mngt.html",
                               pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                galleries = galleries,
                                img_gall = img_gall,
                                images = images,
                                flash_message = flash_message)
    
    return redirect("/gall_mngt")  

@app.route("/gall_new", methods=["GET", "POST"])
def gall_new():

    if request.method == "GET":

        return render_template("/gall_new.html",
                               pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                )
    
    if request.method == "POST":

        if not request.form.get("title"):
            return render_template("/gall_new.html",
                               pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                flash_message = "Title is required."
                                )
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO galleries (title, description) VALUES (?, ?);', (request.form.get("title"), request.form.get("galldescr"),))
        conn.commit()
        conn.close()


        return redirect("/gall_mngt")
        
    
    return redirect("/gall_mngt")

@app.route("/gall_edit", methods=["GET", "POST"])
def gall_edit():

    gall_id = request.args.get('id', '')

    if request.method == "GET":

        conn = get_db_connection()
        gallery = conn.execute('SELECT * FROM galleries WHERE id = ? ORDER BY id DESC;', (gall_id,)).fetchone()
        images = conn.execute('SELECT gall_id, img_id, title FROM gall_img_index JOIN images ON gall_img_index.img_id = images.id WHERE gall_id = ? ORDER BY img_id DESC;', (gall_id,)).fetchall()
        freeimgs = conn.execute('SELECT id FROM images WHERE id > 2 EXCEPT SELECT img_id FROM gall_img_index WHERE gall_id = ? ORDER BY id DESC;', (gall_id,)).fetchall()
        conn.close()

        for img in freeimgs:

            conn = get_db_connection()
            title = conn.execute('SELECT title FROM images WHERE id = ?;', (img['id'],)).fetchone()
            conn.close()

            img['title'] = title['title']
        
        return render_template("/gall_edit.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                gallery = gallery,
                                images = images,
                                freeimgs = freeimgs,
                                )
    
    if request.method == "POST":
            
        action = request.args.get('action', '')

        if action == "edit":

            if not request.form.get("title"):
                return render_template("/gall_new.html",
                                pageinfo = page_info, 
                                    journal = journal_exist, 
                                    events = events_exist,
                                    galls = gall_nav,
                                    flash_message = "Title is required."
                                    )
            
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE galleries SET title = ?, description = ? WHERE id = ?;', (request.form.get("title"), request.form.get("galldescr"), gall_id,))
            conn.commit()
            conn.close()

            return redirect("/gall_edit?id="+gall_id)
        
        if action == "rmv":

            img_id = request.args.get('imgid', '')

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('DELETE FROM gall_img_index WHERE gall_id = ? AND img_id = ?;', (gall_id, img_id,))
            conn.commit()
            conn.close()

            return redirect("/gall_edit?id="+gall_id)  
        
        if action == "add":

            img_id = request.args.get('imgid', '')

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('INSERT INTO gall_img_index (gall_id, img_id) VALUES (?, ?);', (gall_id, img_id,))
            conn.commit()
            conn.close()

            return redirect("/gall_edit?id="+gall_id)  
        
    return redirect("/gall_mngt")  


@app.route("/gall_del", methods=["POST"])
def gall_del():

    ## delete gallery entry ##

    gall_id = request.args.get('id', '')    # get the id of the gallery to remove

    if request.method == "POST":
       
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('DELETE FROM gall_img_index WHERE gall_id = ?;', (gall_id,)) # remove the gallery data from the gallery and photos index table
        cur.execute('DELETE FROM galleries WHERE id = ?;', (gall_id,)) # remove the gallery data from the gallery table
        conn.commit()
        conn.close()

        return redirect("/gall_mngt")   # return to the galls and photos management page      
    
    return redirect("/gall_mngt")  

@app.route("/img_edit", methods=["GET", "POST"])
def img_edit():

    if request.args.get('imgid', ''):
        img_id = request.args.get('imgid', '')

    conn = get_db_connection()
    img_info = conn.execute('SELECT * FROM images WHERE id =?;', (img_id,)).fetchone()
    img_galls = conn.execute('SELECT gall_id, title FROM gall_img_index JOIN galleries ON gall_img_index.gall_id = galleries.id WHERE img_id = ?;', (img_id,)).fetchall()
    conn.close()

    if request.method == "GET":        

        return render_template("/img_edit.html",
                                    pageinfo = page_info, 
                                    journal = journal_exist, 
                                    events = events_exist,
                                    galls = gall_nav,
                                    img_info = img_info,
                                    img_galls = img_galls,
                                    )
    
    if request.method == "POST":

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('UPDATE images SET title = ?, alt = ?, description = ? WHERE id = ?;', (request.form.get("title"), request.form.get("alt"), request.form.get("description"), img_id,))
        conn.commit()
        conn.close()

        return render_template("/img_edit.html",
                                    pageinfo = page_info, 
                                    journal = journal_exist, 
                                    events = events_exist,
                                    galls = gall_nav,
                                    img_info = img_info,
                                    img_galls = img_galls,
                                    img_id = img_id,
                                    flash_message = "Image info Saved",
                                    )
    
    return redirect("/gall_mngt")

@app.route("/img_del", methods=["POST"])
def img_del():

    ## delete image entry ##

    if not request.form.get("img_id"):
        return redirect("/gall_mngt")

    img_id = request.form.get("img_id")    # get the id of the image to remove

    print(img_id) 

    if request.method == "POST":
       
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('DELETE FROM gall_img_index WHERE img_id = ?;', (img_id,)) # remove the image data from the gallery and photos index table
        cur.execute('DELETE FROM images WHERE id = ?;', (img_id,)) # remove the image data from the images table
        conn.commit()
        conn.close()

        if os.path.exists(cwd + app.config['UPLOAD_PATH'] + img_id + ".jpg"):

                os.remove(cwd + app.config['UPLOAD_PATH'] + img_id + ".jpg")

        if os.path.exists(cwd + "/static/images/thumbs/" + img_id + ".jpg"):

                os.remove(cwd + "/static/images/thumbs/" + img_id + ".jpg")

        return redirect("/gall_mngt")   # return to the galls and photos management page      
    
    return redirect("/gall_mngt")

@app.route("/photos_upload", methods=["GET", "POST"])
def photos_upload():

    if request.method == "GET":

        return render_template("/photos_upload.html",
                                    pageinfo = page_info, 
                                    journal = journal_exist, 
                                    events = events_exist,
                                    galls = gall_nav,
                                    )
    
    if request.method == "POST":

        img = request.files['file']

        filename = img.filename 

        if filename != '':

            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS'] or \
                file_ext != validate_image(img.stream):
                
                return "Invalid image", 400
            
            
        # insert image into DB and get its id to be saved in files #
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO images (title) VALUES (?);', (("Untitled"),)) # insert image info in images db table 
        img_index = conn.execute('SELECT id FROM images ORDER BY id DESC;').fetchone()
        conn.commit()
        conn.close()
        
        fname = str(img_index['id'])+".jpg"

        path = os.path.join((cwd+app.config['UPLOAD_PATH']), fname)

        thumbpath = os.path.join((cwd+app.config['UPLOAD_PATH']+"thumbs"), fname)

        img.save(path) 

        image_resize(path, 1200) 

        createthumb(path, thumbpath, 600)

        return '', 204
    

@app.errorhandler(413)
def too_large(e):
    return "File is too large", 413

