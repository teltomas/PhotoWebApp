import os
import sqlite3
import re
from datetime import datetime
from flask import Flask, redirect, render_template, session, request, flash
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Mail, Message


from front import date, capital
from back import validate_image, get_db_connection, image_resize, createthumb, login_required, img_upload, dblink

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
page_info = conn.execute('SELECT page_name, small_descr, about, inst_link, face_link, \
                         yt_link, tweet_link, px_link, bhnc_link, tumblr_link, flickr_link, \
                         about_img, prof_pic, legal, copyright, page_email, meta \
                         FROM page_info WHERE id = 1;').fetchone() # for the general page info #
journals = conn.execute('SELECT * FROM articles WHERE type = "journal" \
                        AND archived = 0;').fetchone() # determine if there are journals in db to activate the journal nav item #
events = conn.execute('SELECT * FROM articles WHERE type = "event" \
                      AND archived = 0;').fetchone() # determine if there are events in db to activate the events nav item #
gall_nav = conn.execute('SELECT id, title FROM galleries WHERE id != 1;').fetchall() # get how many galleries exist in db to fill the galleries nav itens #
page_conf = conn.execute('SELECT email, page_email, page_email_hash \
                         FROM page_info WHERE id = 1;').fetchone() # for the general page info #

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

    sc_img.reverse()

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
    articles = conn.execute('SELECT * FROM articles WHERE type = ? \
                            AND archived = 0 \
                            ORDER BY date DESC;', (ar_type,)).fetchall()
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

        # email address input validation before sending #
        # as shown here https://stackabuse.com/python-validate-email-address-with-regular-expressions-regex/ #

        regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
        
        if not request.form.get("email") or not re.fullmatch(regex, request.form.get("email")) :

            return render_template("/contact.html", 
                                   pageinfo = page_info, 
                                   journal = journal_exist, 
                                   events = events_exist, 
                                   galls = gall_nav,
                                   flash_message = "Invalid email address..."), 400
        
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
                                   flash_message = "Sorry! There was an error sending the message..."), 500
        
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
    imgs_info = conn.execute('SELECT * FROM gall_img_index JOIN images \
                             ON gall_img_index.img_id = images.id \
                             WHERE gall_id = ?', (gall_id,)).fetchall()
    conn.close()

    # check if gallery exists, if not redirect to main page #

    if gall_info:

        # split the quantity of images in three diferent arrays to distribute in the page grid #
        imgs_col1 = []
        imgs_col2 = []
        imgs_col3 = []

        if imgs_info:

            imgs_info.reverse()
        
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

    return redirect("/"), 404

@app.route("/<inftype>")
def disclaimer(inftype):

    # to display legal or copyright infos, if requested. Return main page if undefined path or no content to display #

    if not page_info['legal'] or not page_info['copyright']:

        return redirect("/")

    if inftype == "legal" or inftype == "copyright":

        return render_template("/disclaimer.html", 
                        pageinfo = page_info, 
                        journal = journal_exist, 
                        events = events_exist,
                        galls = gall_nav,
                        inftype = inftype,
                        )
    
    else:

        return redirect("/")



####### FOR USER APP MANAGEMENT #######
# Configure session to use filesystem (instead of signed cookies)
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'

# The maximum number of items the session stores 
# before it starts deleting some, default 500
app.config['SESSION_FILE_THRESHOLD'] = 10  

Session(app)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash('Must provide username')
            return redirect('/login'), 400

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash('Must provide password')
            return redirect('/login'), 400

        # Query database for username
       
        conn = get_db_connection()
        user = conn.execute('SELECT id, username, hash \
                            FROM page_info \
                            WHERE username = ?', (request.form.get("username"),)).fetchone()
        conn.close()

        # Ensure username exists and password is correct
        if not user or not check_password_hash(user["hash"], request.form.get("password")):
            flash('Invalid username or password')
            return redirect('/login'), 400

        # Remember which user has logged in
        session["user_id"] = user["id"]

        # Redirect user to home page
        return redirect("/management")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html",                                
                               pageinfo = page_info, 
                               journal = journal_exist, 
                               events = events_exist, 
                               galls = gall_nav,)


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/management")
@login_required
def mngmt():

    # render main management page #
    return render_template("mngmt_main.html",
                           pageinfo = page_info, 
                           journal = journal_exist, 
                           events = events_exist,
                           galls = gall_nav)


@app.route("/ar_mngt", methods=["GET", "POST"])
@login_required
def ar_mngmt():

    # management of the existing articles - both events and journal entries #

    # fetch from the address arguments the kind of article to manage: journal or event #

    if request.args.get('artp', ''):
        ar_type = request.args.get('artp', '')
                
        # get from the db the articles from the type requested #
        conn = get_db_connection()
        entries = conn.execute('SELECT id, title, date, content \
                               FROM articles \
                               WHERE type = ? AND archived = 0 \
                               ORDER BY date DESC;', (ar_type,)).fetchall()
        conn.close()
    else:
        ar_type: None
        entries: None

    if request.method == "GET":
        
        if ar_type not in ['journal', 'event']:
            flash('Error - Undefined article type')
            return redirect('/mngmt_main'), 400
            
        # limit the length of the text to display in the for each article #
        if entries:
            for row in entries:
                if len(row['content'])>150:
                    row['content'] = row['content'][:150]+"..."

        return render_template("ar_mngt.html",
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            galls = gall_nav,
                            entries = entries,
                            ar_type = ar_type)
    
    
    if request.method == "POST":

        if not request.form.get("id") or not request.args.get('action', ''):

            flash('Error - Undefined request')
            return redirect('/ar_mngt'), 400

        # fetch the Id from the article to edit #
        ar_id = request.form.get("id")

        # fetch the action to do with the article selected #
        action = int(request.args.get('action', ''))

        # get article info from DB #
        conn = get_db_connection()
        article = conn.execute('SELECT * FROM articles WHERE id = ?;', (ar_id,)).fetchone()
        conn.close()

        # define article type #
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

            # change article archive status in DB # 
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE articles SET archived = ? WHERE id = ?;', (True, ar_id,))
            conn.commit()
            conn.close()

            flash('Article successfully archived')
            return redirect("/ar_mngt?artp="+ar_type)
        
        if action == 3: # save edited article entry #

            # get and confirm title and content input #
            if request.form.get("title") and request.form.get("content"):
                article['title'] = request.form.get("title")
                article['content'] = request.form.get("content")
            else:
                # Return error nessage in case of no input #
                flash('Update failed - Title and content text required')
                return redirect('/ar_mngt?artp='+ar_type), 400

            # get link input - set null if empty #
            if request.form.get("link"):
                article['link'] = dblink(request.form.get("link"))
            else:
                article['link'] = None

            # update info in the DB #
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE articles \
                        SET title = ?, content = ?, link = ? \
                        WHERE id = ?;', (article['title'], article['content'], article['link'], ar_id,))
            conn.commit()
            conn.close()

            # img file upload handling implemented as shown here https://blog.miguelgrinberg.com/post/handling-file-uploads-with-flask #

            if request.files['img']:

                # set info to save img in files and DB #
                article['image'] = "article" + str(ar_id)

                # get the path to save, and save img file #
                path = os.path.join((cwd+app.config['UPLOAD_PATH']), article['image']+".jpg")
                
                # get image file from input and process it, loaded == True if success, False if not #
                                
                if not img_upload(request.files['img'], path, ['.jpg', 'jpeg'], 800):  
                    
                    flash('Article successfully updated BUT invalid image discarded.')
                    return render_template("edit_entry.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                article = article,
                                ar_type = ar_type)

                else:

                    # update article in db with image name #
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute('UPDATE articles SET image = ? WHERE id = ?;', (article['image'], ar_id,))
                    conn.commit()
                    conn.close()

            flash('Article successfully updated')
            return render_template("edit_entry.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                article = article,
                                ar_type = ar_type)
                    
        if action == 4: # remove photo from article #

            # get image name from the db to proceed with file deletion #

            conn = get_db_connection()
            image = conn.execute('SELECT * FROM articles WHERE id = ?;', (ar_id,)).fetchone()
            conn.close()

            if image['image']:
                
                os.remove(cwd+"/static/images/" + str(image['image']) + ".jpg") 

            # update article in db with Null image #
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE articles SET image = ? WHERE id = ?;', (None, ar_id,))
            conn.commit()
            conn.close()

            # update the image info from the article content so it does not try to load # 
            article['image'] = None

            flash('Photo successfully removed')
            return render_template("edit_entry.html",
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            galls = gall_nav,
                            article = article,
                            ar_type = ar_type
                            )
                    
        # return error in case of undefined action #
        flash('Error - Undefined request')
        return redirect('mngmt_main'), 400
    

@app.route("/ar_new", methods=["GET", "POST"])
@login_required
def ar_new():

    # creation of new articles #

    # redirect in case of invalid argument or no type input #
    if not request.args.get('artp', '') and not request.form.get("ar_type"):
        return redirect("management"), 400

    # get the article type to create #
    ar_type = request.args.get('artp', '')

    # render new article page #
    if request.method == "GET":

        return render_template("ar_new.html",
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            ar_type = ar_type,
                            galls = gall_nav)
    
    
    if request.method == "POST":

        # article type validation and return error in case of undefined #
        if request.form.get("ar_type"):
            ar_type = request.form.get("ar_type")
        else:
            return render_template("mngmt_main.html",
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            galls = gall_nav,
                            flash_message = "Error - Undefined request"), 400

        # article title and content text validation and return error if undefined #
        if request.form.get("title") and request.form.get("content"):
            title = request.form.get("title")
            content = request.form.get("content")
        else:
            return render_template("ar_new.html",
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            galls = gall_nav,
                            ar_type = ar_type,
                            flash_message = "Title and content text required!"), 400
        
        # detect link input and store it, set null in case of no input #
        if request.form.get("link"):
            link = dblink(request.form.get("link"))
        else:
            link = None

        # add article to the DB and get the article ID #
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO articles (type, title, content, archived, link) \
                    VALUES (?, ?, ?, ?, ?);', (ar_type, title, content, False, link,))
        conn.commit()
        ar_id = conn.execute('SELECT id \
                             FROM articles \
                             ORDER BY id DESC;').fetchone()
        conn.close()

        # store article id to be used in case of image upload #
        ar_id = ar_id['id']

        # img file upload handling as shown here https://blog.miguelgrinberg.com/post/handling-file-uploads-with-flask #

        if request.files['img']:
            
            # create image name and path #
            dbname= "article" + str(ar_id)

            path = os.path.join((cwd+app.config['UPLOAD_PATH']), dbname+".jpg")

            # get image from input and process it #
            if not img_upload(request.files['img'], path, ['.jpg', 'jpeg'], 800): 
                    
                return render_template("ar_mngt.html",
                        pageinfo = page_info, 
                        journal = journal_exist, 
                        events = events_exist,
                        galls = gall_nav,
                        ar_type = ar_type,
                        flash_message = "New article successfully posted to " + ar_type + " BUT invalid image discarded.")

            # update article in db with image name #
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE articles SET image = ? WHERE id = ?;', (dbname, ar_id,))
            conn.commit()
            conn.close()

        return redirect("ar_mngt?artp=" + ar_type)
    
@app.route("/archive", methods=["GET", "POST"])
@login_required
def archive():

    # get from db the archived articles #
    conn = get_db_connection()
    archived_ar = conn.execute('SELECT * FROM articles \
                               WHERE archived = 1 ORDER BY id DESC;', ).fetchall()
    conn.close()

    if request.method == "GET":

        # render archived articles page with message in case of non existing archived articles #
        if not archived_ar:

            return render_template("/archive.html",
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            galls = gall_nav,
                            flash_message = "Archive is empty.")
        
        # resize content text to be posted and render page #
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

        # return error message in case of undefined request #
        if not request.args.get('action', '') or not request.form.get("id"):
            flash('Error - Undefined request.')
            return redirect('/archive'), 400

        # store requested info #
        action = request.args.get('action', '')
        ar_id = request.form.get("id")


        if action == "repub":

            # update article archived status in case of republish request #
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE articles SET archived = ? WHERE id = ?;', (False, ar_id,))
            conn.commit()
            conn.close()

            flash('Article successfully republished.')
            return redirect('/archive')


        if action == "del": # delete article entry #

            # get the info from the db to check if article has an image #
            conn = get_db_connection()
            image = conn.execute('SELECT image FROM articles \
                                 WHERE id = ?;', (ar_id,) ).fetchone()
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

            flash('Article deleted.')
            return redirect('/archive')

        # return error in case of undefined action #
        flash('Error - Undefined request.')
        return redirect('/archive'), 400

    return redirect("/archive")


@app.route("/pg_mngt", methods=["GET"])
@login_required
def pg_mngt():

    # render page of aspect and base info management selection #
    return render_template("/pg_mngt.html",
                            pageinfo = page_info, 
                            journal = journal_exist, 
                            events = events_exist,
                            galls = gall_nav,
                            )


@app.route("/profile_mngt", methods=["GET", "POST"])
@login_required
def profile_mngt():

    # update info data to fill forms #
    conn = get_db_connection()
    page_info = conn.execute('SELECT * FROM page_info \
                             WHERE id = 1;').fetchone() # for the general page info #
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

        # get which action was requested and proceed with change, return error in case of no argument #        
        if not request.args.get('action', ''):
            return render_template("/profile_mngt.html",
                                        pageinfo = page_info, 
                                        journal = journal_exist, 
                                        events = events_exist,
                                        galls = gall_nav,
                                        flash_message = "Error - request undefined"
                                        ), 400
        
        action = request.args.get('action', '')

        # in case of name update request, get new input and update db. Return error in case of empty input # 
        if action == "name":

            if not request.form.get("pg_name"):

                return render_template("/profile_mngt.html",
                                        pageinfo = page_info, 
                                        journal = journal_exist, 
                                        events = events_exist,
                                        galls = gall_nav,
                                        flash_message = "Page name input required"
                                        ), 400
            
            else:
                
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute('UPDATE page_info SET page_name = ? \
                            WHERE id = 1;', (request.form.get("pg_name"),))
                conn.commit()
                conn.close() 

            return redirect("/profile_mngt")

        # update description #
        if action == "description":

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE page_info SET small_descr = ? \
                        WHERE id = 1;', (request.form.get("pg_descr"),))
            conn.commit()
            conn.close()

            return redirect("/profile_mngt")

        # update about section info #
        if action == "aboutcontent":

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE page_info SET about = ? \
                        WHERE id = 1;', (request.form.get("abttxt"),))
            conn.commit()
            conn.close()

            return redirect("/profile_mngt")

        # update about section photo - same upload process as above #
        # about img should always be stored as 0.jpg # 
        if action == "aboutphoto":

            if request.files['abimg']:

                # if file uploaded: set path to save file and process it. About section image is always 0.jpg#
                path = os.path.join((cwd+app.config['UPLOAD_PATH']), "0.jpg")

                if not img_upload(request.files['abimg'], path, ['.jpg', 'jpeg'], 1000): 

                    return render_template("profile_mngt.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                flash_message = "Failed to upload image.")
            
                # In case DB had the "about image" deactivated, activate it # 

                if not page_info['about_img']:

                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute('UPDATE page_info SET about_img = ? \
                                WHERE id = 1;', (True,))
                    conn.commit()
                    conn.close() 

            return redirect("/profile_mngt") 
        
        # delete about section photo from files and update db on case of photo removal request #
        if action == "delabtph":

            # check if exist #
            if os.path.exists(cwd + app.config['UPLOAD_PATH'] + "0.jpg"):

                # remove if exist #
                os.remove(cwd + app.config['UPLOAD_PATH'] + "0.jpg")

                # update db - deactivate "about image" #
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute('UPDATE page_info SET about_img = ? \
                            WHERE id = 1;', (False,))
                conn.commit()
                conn.close()

            return redirect("/profile_mngt")

        # profile image upload - same process as above, but in this case also .png files accepted in case of logo upload #
        # profile image saved as "1" + file extension #
        if action == "profphoto":

            if request.files['profimg']:

                file_ext = os.path.splitext(request.files['profimg'].filename)[1]

                fname = "1" + file_ext

                path = os.path.join((cwd+app.config['UPLOAD_PATH']), fname)

                if not img_upload(request.files['profimg'], path, ['.jpg', 'jpeg', '.png'], 600): 
            
                    return render_template("profile_mngt.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                flash_message = "Failed to upload image."), 400
                
                # db needs to be updated regarding the possibility of different file extensions #
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute('UPDATE page_info SET prof_pic = ? WHERE id = 1;', (fname,))
                conn.commit()
                conn.close() 

            return redirect("/profile_mngt") 

        # section of update social networks links #
        # # direct aproach to fill db with link in case of input, and Null in case of no input # 
        if action == "insta":

            conn = get_db_connection()
            cur = conn.cursor()
            if request.form.get("instalink"):
                cur.execute('UPDATE page_info SET inst_link = ? \
                            WHERE id = 1;', (dblink(request.form.get("instalink")),))
            else:
                cur.execute('UPDATE page_info SET inst_link = ? WHERE id = 1;', (None,))
            conn.commit()
            conn.close()

            return redirect("/profile_mngt")
        
        if action == "face":
                
            conn = get_db_connection()
            cur = conn.cursor()
            if request.form.get("facelink"):
                cur.execute('UPDATE page_info SET face_link = ? \
                            WHERE id = 1;', (dblink(request.form.get("facelink")),))
            else:
                cur.execute('UPDATE page_info SET face_link = ? WHERE id = 1;', (None,))
            conn.commit()
            conn.close()

            return redirect("/profile_mngt")

        if action == "ytb":

            conn = get_db_connection()
            cur = conn.cursor()
            if request.form.get("ytblink"):
                cur.execute('UPDATE page_info SET yt_link = ? \
                            WHERE id = 1;', (dblink(request.form.get("ytblink")),))
            else:
                cur.execute('UPDATE page_info SET yt_link = ? WHERE id = 1;', (None,))
            conn.commit()
            conn.close()

            return redirect("/profile_mngt")

        if action == "tweet":

            conn = get_db_connection()
            cur = conn.cursor()
            if request.form.get("tweetlink"):
                cur.execute('UPDATE page_info SET tweet_link = ? \
                            WHERE id = 1;', (dblink(request.form.get("tweetlink")),))
            else:
                cur.execute('UPDATE page_info SET tweet_link = ? WHERE id = 1;', (None,))
            conn.commit()
            conn.close()

            return redirect("/profile_mngt")

        if action == "px":

            conn = get_db_connection()
            cur = conn.cursor()
            if request.form.get("500pxlink"):
                cur.execute('UPDATE page_info SET px_link = ? \
                            WHERE id = 1;', (dblink(request.form.get("500pxlink")),))
            else:
                cur.execute('UPDATE page_info SET px_link = ? WHERE id = 1;', (None,))
            conn.commit()
            conn.close()

            return redirect("/profile_mngt")

        if action == "bhnc":
   
            conn = get_db_connection()
            cur = conn.cursor()
            if request.form.get("bhnclink"):
                cur.execute('UPDATE page_info SET bhnc_link = ? \
                            WHERE id = 1;', (dblink(request.form.get("bhnclink")),))
            else:
                cur.execute('UPDATE page_info SET bhnc_link = ? WHERE id = 1;', (None,))
            conn.commit()
            conn.close()

            return redirect("/profile_mngt")

        if action == "flickr":

            conn = get_db_connection()
            cur = conn.cursor()
            if request.form.get("flickrlink"):
                cur.execute('UPDATE page_info SET flickr_link = ? \
                            WHERE id = 1;', (dblink(request.form.get("flickrlink")),))
            else:
                cur.execute('UPDATE page_info SET flickr_link = ? WHERE id = 1;', (None,))
            conn.commit()
            conn.close()

            return redirect("/profile_mngt")

        if action == "tumblr":

            conn = get_db_connection()
            cur = conn.cursor()
            if request.form.get("tumblrlink"):
                cur.execute('UPDATE page_info SET tumblr_link = ? \
                            WHERE id = 1;', (dblink(request.form.get("tumblrlink")),))
            else:
                cur.execute('UPDATE page_info SET tumblr_link = ? WHERE id = 1;', (None,))
            conn.commit()
            conn.close()

            return redirect("/profile_mngt")
        
        # in case of undefined action request, return error #
        return render_template("/profile_mngt.html",
                                        pageinfo = page_info, 
                                        journal = journal_exist, 
                                        events = events_exist,
                                        galls = gall_nav,
                                        flash_message = "Error - request undefined"
                                        ), 400
    
    return redirect("/profile_mngt")

@app.route("/base_mngt", methods=["GET", "POST"])
@login_required
def base_mngt():

    # update info variables to fill forms #

    conn = get_db_connection()
    page_info = conn.execute('SELECT * FROM page_info \
                             WHERE id = 1;').fetchone() # for the general page info #
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

        # update the page info considering the users request as "action" #

        action = request.args.get('action', '')

        if action == "pgemail":

            # set the users email address, to where the page messages will be sent - required #
            if request.form.get("email"):
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute('UPDATE page_info SET email = ? \
                            WHERE id = 1;', (request.form.get("email"),))
                conn.commit()
                conn.close()

                return redirect("/base_mngt")

            else: 

                return render_template("/base_mngt.html",
                                    pageinfo = page_info, 
                                    journal = journal_exist, 
                                    events = events_exist,
                                    galls = gall_nav,
                                    flash_message = "User email required."
                                    )
        
        # update the page configuration email - from where the page messages will be sent #
        if action == "confemail":

            conn = get_db_connection()
            cur = conn.cursor()
            if request.form.get("cfemail"):
                cur.execute('UPDATE page_info SET page_email = ? \
                            WHERE id = 1;', (request.form.get("cfemail"),))
            else:
                cur.execute('UPDATE page_info SET page_email = ? \
                            WHERE id = 1;', (None,))
            conn.commit()
            conn.close()

            return redirect("/base_mngt")
        
        # update the page configuration email access token #
        if action == "confemailkey":

            conn = get_db_connection()
            cur = conn.cursor()
            if request.form.get("emailkey"):
                cur.execute('UPDATE page_info SET page_email_hash = ? \
                            WHERE id = 1;', (request.form.get("emailkey"),))
            else:
                cur.execute('UPDATE page_info SET page_email_hash = ? \
                            WHERE id = 1;', (None,))
            conn.commit()
            conn.close()

            return render_template("/base_mngt.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                flash_message = "Email token updated"
                                )
        
        # change the management section access password #
        if action == "passchange":

            # require input of all fields #

            if not request.form.get("cpass") or not request.form.get("npass") \
                or not request.form.get("repass"):

                return render_template("/base_mngt.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                flash_message = "All password fields required"
                                )

            # check if current password matches #
            if not check_password_hash(page_info['hash'], request.form.get("cpass")):

                return render_template("/base_mngt.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                flash_message = "Wrong password"
                                )
            
            # require matching new passwords #
            if request.form.get("npass") != request.form.get("repass"):

                return render_template("/base_mngt.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                flash_message = "New password fields don't match"
                                )
            
            # check if password meets the requirements - 8 chars and numbers, allow special chars #
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
            
            # if password meets requirements, proceed wish hash generator and store it #
            else:

                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute('UPDATE page_info SET hash = ? \
                            WHERE id = 1;', (generate_password_hash(nkey),))
                conn.commit()
                conn.close()

            return render_template("/base_mngt.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                flash_message = "Password updated"
                                )
        
        # update legal info #
        if action == "legal":

            conn = get_db_connection()
            cur = conn.cursor()
            if request.form.get("pg_legal"):
                cur.execute('UPDATE page_info SET legal = ? WHERE id = 1;', (request.form.get("pg_legal"),))
            else: 
                cur.execute('UPDATE page_info SET legal = ? WHERE id = 1;', (None,))    
            conn.commit()
            conn.close()

            return redirect("/base_mngt")
        
        # update copyright info #
        if action == "copy":

            conn = get_db_connection()
            cur = conn.cursor()
            if request.form.get("pg_copy"):
                cur.execute('UPDATE page_info SET copyright = ? WHERE id = 1;', (request.form.get("pg_copy"),))
            else:
                cur.execute('UPDATE page_info SET copyright = ? WHERE id = 1;', (None,))
            conn.commit()
            conn.close()

            return redirect("/base_mngt")
        
        # update meta tags data #
        if action == "metatags":

            conn = get_db_connection()
            cur = conn.cursor()
            if request.form.get("meta"):
                cur.execute('UPDATE page_info SET meta = ? WHERE id = 1;', (request.form.get("meta"),))
            else:
                cur.execute('UPDATE page_info SET meta = ? WHERE id = 1;', (None,))
            conn.commit()
            conn.close()

            return redirect("/base_mngt")
        
        # return error if undefined action #
        return render_template("/base_mngt.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                flash_message = "Error - bad request"
                                ), 400

    return redirect("/base_mngt")

@app.route("/aspect_mngt", methods=["GET", "POST"])
@login_required
def aspect_mngt():

    # render the aspect management page #
    if request.method == "GET":

        return render_template("/aspect_mngt.html",
                               pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav)
    
    if request.method == "POST":

        # fecth action requested #
        action = request.args.get('action', '')

        # upload and update banner / hero image #
        if action == "banner":

            if request.files['heroimg']:

                path = os.path.join((cwd+app.config['UPLOAD_PATH']), "2.jpg")

                if not img_upload(request.files['heroimg'], path, ['.jpg', 'jpeg'], None): 
            
                    return render_template("aspect_mngt.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                flash_message = "Failed to upload image - invalid file."), 400

            else:
                # return error message in case of submit with no file #
                return render_template("/aspect_mngt.html",
                                pageinfo = page_info, 
                                    journal = journal_exist, 
                                    events = events_exist,
                                    galls = gall_nav,
                                    flash_messsage = "No file selected"), 400

            return redirect("/aspect_mngt")
    
        # upload and update image favicon #
        if action == "ico":

            if request.files['ico']:
            
                # no image_upload function call because of no compatibility with ico in image stream validation #
                img = request.files['ico']
                
                # get filname to check extension #
                filename = img.filename 

                if filename != '':
                    
                    # if filename got, check if extension is valid #
                    file_ext = os.path.splitext(filename)[1]
                    if file_ext not in ['.ico']:
                        
                        # return error if invalid file #
                        return render_template("aspect_mngt.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                flash_message = "Failed to upload icon - invalid file."), 400

                path = os.path.join((cwd+"static/icons/"), "favicon.ico")

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
                                    galls = gall_nav,
                                    flash_message = "Error - undefined request"), 400
    
@app.route("/gall_mngt", methods=["GET", "POST"])
@login_required
def gall_mngt():

    # gallery management page #

    # get galleries and images info, and their match, from DB #
    conn = get_db_connection()
    galleries = conn.execute('SELECT * FROM galleries ORDER BY id DESC;').fetchall()
    img_gall = conn.execute('SELECT * FROM gall_img_index;').fetchall()
    images = conn.execute('SELECT id, title FROM images WHERE id > 2 ORDER BY id DESC;').fetchall()
    conn.close()

    flash_message = None

    # determine message to return in case of no gallery data #
    if not galleries:
        flash_message = "There are no galleries to display."

    # limit galleries info shown text if exist # 
    for row in galleries:
        if row['description'] and len(row['description']) > 100:
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
@login_required
def gall_new():

    # to create a new gallery #

    if request.method == "GET":

        return render_template("/gall_new.html",
                               pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                )
    
    if request.method == "POST":

        # guarantee a title input #
        if not request.form.get("title"):
            return render_template("/gall_new.html",
                               pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                flash_message = "Title is required."
                                ), 400
        
        # set the gallery description to bd input, set Null if it has no content #
        if request.form.get("galldescr"):
            galldescr = request.form.get("galldescr")
        else:
            galldescr = None
        
        # insert gallery info into DB #
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO galleries (title, description) VALUES (?, ?);', (request.form.get("title"), galldescr,))
        conn.commit()
        conn.close()

        return redirect("/gall_mngt")        
    
    return redirect("/gall_mngt")


@app.route("/gall_edit", methods=["GET", "POST"])
@login_required
def gall_edit():

    # Gallery info change #

    # get the id of the gallery requested, return error if no id #
    if request.args.get('id', ''):
        gall_id = request.args.get('id', '')
    else:
        return redirect("/gall_mngt"), 400
    
    # in case of get method get gallery info, its photos and also the photos that are not in the gallery, to render the edit page #
    conn = get_db_connection()
    gallery = conn.execute('SELECT * FROM galleries WHERE id = ? ORDER BY id DESC;', (gall_id,)).fetchone()
    images = conn.execute('SELECT gall_id, img_id, title FROM gall_img_index JOIN images ON gall_img_index.img_id = images.id WHERE gall_id = ?;', (gall_id,)).fetchall()
    freeimgs = conn.execute('SELECT id FROM images WHERE id > 2 EXCEPT SELECT img_id FROM gall_img_index WHERE gall_id = ? ORDER BY id DESC;', (gall_id,)).fetchall()
    conn.close()

    images.reverse() # to render the photos in the gallery edit page the same order and way they are presented in the gallery presentantion page #

    # split the quantity of images in three diferent arrays to display in the page grid #
    imgs_col1 = []
    imgs_col2 = []
    imgs_col3 = []

    i = 0
    while i < len(images):
        imgs_col1.append(images[i])
        if i+1 < len(images): 
            imgs_col2.append(images[i+1])
        if i+2 < len(images): 
            imgs_col3.append(images[i+2])
        i = i + 3

    for img in freeimgs:

        # add image title to the photos array #
        conn = get_db_connection()
        title = conn.execute('SELECT title FROM images WHERE id = ?;', (img['id'],)).fetchone()
        conn.close()

        img['title'] = title['title']

    if request.method == "GET":        
        
        # render the page #
        return render_template("/gall_edit.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                gallery = gallery,
                                images = images,
                                imgs_col1 = imgs_col1,
                                imgs_col2 = imgs_col2,
                                imgs_col3 = imgs_col3,
                                freeimgs = freeimgs,
                                )
    
    if request.method == "POST":
        
        # in case of post method, get the requested action. Return error in case of no argument #
        if request.args.get('action', ''):    
            action = request.args.get('action', '')
        else:
            return render_template("/gall_edit.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                gallery = gallery,
                                images = images,
                                imgs_col1 = imgs_col1,
                                imgs_col2 = imgs_col2,
                                imgs_col3 = imgs_col3,
                                freeimgs = freeimgs,
                                flash_message = "Error - Undefined request"
                                ), 400

        if action == "edit": # if the change is in the gallery title or description #

            # gallery title is a must - return error otherwise #
            if not request.form.get("title"):
                return render_template("/gall_edit.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                gallery = gallery,
                                images = images,
                                imgs_col1 = imgs_col1,
                                imgs_col2 = imgs_col2,
                                imgs_col3 = imgs_col3,
                                freeimgs = freeimgs,
                                flash_message = "Title is required"
                                ), 400
            
            # get description input info, set Null in no input #
            if request.form.get("galldescr"):
                galldescr = request.form.get("galldescr")
            else:
                galldescr = None

            # Update db and reload edit page #
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE galleries SET title = ?, description = ? WHERE id = ?;', (request.form.get("title"), galldescr, gall_id,))
            conn.commit()
            conn.close()

            return redirect("/gall_edit?id="+gall_id)
        

        if action == "rmv": # remove image from the gallery #

            # fetch the id of the image requested in the action, return error if none #
            if request.args.get('imgid',''):
                img_id = request.args.get('imgid', '')
            else:
                return render_template("/gall_edit.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                gallery = gallery,
                                images = images,
                                imgs_col1 = imgs_col1,
                                imgs_col2 = imgs_col2,
                                imgs_col3 = imgs_col3,
                                freeimgs = freeimgs,
                                flash_message = "Error - Image Id undefined to proceed with request."
                                ), 400

            # remove from the photo to gallery index table the record where the image is attached to the gallery #
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('DELETE FROM gall_img_index WHERE gall_id = ? AND img_id = ?;', (gall_id, img_id,))
            conn.commit()
            conn.close()

            return redirect("/gall_edit?id="+gall_id)  
        
        if action == "add":

            # fetch the id of the image requested in the action, return error if none #
            if request.args.get('imgid',''):
                img_id = request.args.get('imgid', '')
            else:
                return render_template("/gall_edit.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                gallery = gallery,
                                images = images,
                                imgs_col1 = imgs_col1,
                                imgs_col2 = imgs_col2,
                                imgs_col3 = imgs_col3,
                                freeimgs = freeimgs,
                                flash_message = "Error - Image Id undefined to proceed with request."
                                ), 400

            # add to the image to gallery index table the image to gallery match #
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('INSERT INTO gall_img_index (gall_id, img_id) VALUES (?, ?);', (gall_id, img_id,))
            conn.commit()
            conn.close()

            return redirect("/gall_edit?id="+gall_id)  
        
        # return error message in case of undefined action request #
        return render_template("/gall_edit.html",
                                pageinfo = page_info, 
                                journal = journal_exist, 
                                events = events_exist,
                                galls = gall_nav,
                                gallery = gallery,
                                images = images,
                                imgs_col1 = imgs_col1,
                                imgs_col2 = imgs_col2,
                                imgs_col3 = imgs_col3,
                                freeimgs = freeimgs,
                                flash_message = "Error - Undefined request."
                                ), 400
        
    return redirect("/gall_mngt")  


@app.route("/gall_del", methods=["POST"])
@login_required
def gall_del():

    ## delete gallery entry ##

    if request.method == "POST":
        
        # get the id of the gallery to delete, return error if no id #
        if request.args.get('id', ''):
            gall_id = request.args.get('id', '')
        else:
            return redirect("/gall_mngt"), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('DELETE FROM gall_img_index WHERE gall_id = ?;', (gall_id,)) # remove all listings of the gallery from the gallery and photos index table #
        cur.execute('DELETE FROM galleries WHERE id = ?;', (gall_id,)) # remove the gallery data from the gallery table #
        conn.commit()
        conn.close()

        return redirect("/gall_mngt")   # return to the galls and photos management page #
    
    return redirect("/gall_mngt")  


@app.route("/img_edit", methods=["GET", "POST"])
@login_required
def img_edit():

    ## image info edit page ##

    # fetch id from image to edit, retunr error if none #
    if request.args.get('imgid', ''):
        img_id = request.args.get('imgid', '')
    else:
        return redirect("/gall_mngt"), 400

    # fetch from the DB the image data to fill the image edit page #
    conn = get_db_connection()
    img_info = conn.execute('SELECT * FROM images WHERE id =?;', (img_id,)).fetchone() # image data #
    img_galls = conn.execute('SELECT gall_id, title \
                             FROM gall_img_index \
                             JOIN galleries \
                             ON gall_img_index.gall_id = galleries.id \
                             WHERE img_id = ?;', (img_id,)).fetchall() # list of the galleries where the image is present #
    conn.close()

    if request.method == "GET":        

        # render image edit page #
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

        return redirect("/gall_mngt")
    
    return redirect("/gall_mngt")

@app.route("/img_del", methods=["POST"])
@login_required
def img_del():

    ## delete image entry ##

    # fetch id of image to remove, return error if undefined #
    if not request.form.get("img_id"):
        return redirect("/gall_mngt"), 400

    img_id = request.form.get("img_id")

    if request.method == "POST":
       
        # remove the image info from all the DB tables #
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('DELETE FROM gall_img_index WHERE img_id = ?;', (img_id,)) # remove the image data from the gallery and photos index table
        cur.execute('DELETE FROM images WHERE id = ?;', (img_id,)) # remove the image data from the images table
        conn.commit()
        conn.close()

        # delete the image files if found, both from the main folder as with the thumbnails folder #
        if os.path.exists(cwd + app.config['UPLOAD_PATH'] + img_id + ".jpg"):

                os.remove(cwd + app.config['UPLOAD_PATH'] + img_id + ".jpg")

        if os.path.exists(cwd + "/static/images/thumbs/" + img_id + ".jpg"):

                os.remove(cwd + "/static/images/thumbs/" + img_id + ".jpg")

        return redirect("/gall_mngt")   # return to the galls and photos management page      
    
    return redirect("/gall_mngt")

@app.route("/multimagesdel", methods=["POST"])
@login_required
def multi_img_del():

    ## delete multi image entry ##

    if request.form.get("imgsarray"):

        # imgs Id are delivered in a string of ids seperated by comma, split to get the ids from the string and store them in the array #
        ids = request.form.get("imgsarray").split(",") # get image ids and split them in an array #

        conn = get_db_connection()
        cur = conn.cursor()

        # proceed with removal for each image id in the array #
        for id in ids:  

            cur.execute('DELETE FROM gall_img_index WHERE img_id = ?;', (id,)) # remove the image data from the gallery and photos index table #
            cur.execute('DELETE FROM images WHERE id = ?;', (id,)) # remove the image data from the images table #

            # delete the image files if found, both from the main folder as with the thumbnails folder #
            if os.path.exists(cwd + app.config['UPLOAD_PATH'] + id + ".jpg"):

                os.remove(cwd + app.config['UPLOAD_PATH'] + id + ".jpg")

            if os.path.exists(cwd + "/static/images/thumbs/" + id + ".jpg"):

                os.remove(cwd + "/static/images/thumbs/" + id + ".jpg")

        conn.commit()
        conn.close()

    else:
        return redirect("/gall_mngt"), 400
    
    return redirect("/gall_mngt")

@app.route("/photos_upload", methods=["GET", "POST"])
@login_required
def photos_upload():

    ## upload photo ##

    # render upload page on GET request #
    if request.method == "GET":

        return render_template("/photos_upload.html",
                                    pageinfo = page_info, 
                                    journal = journal_exist, 
                                    events = events_exist,
                                    galls = gall_nav,
                                    )
    

    if request.method == "POST":

        # if file detected, proceed with upload and validation #
        # no standard image_upload function used because the DB image id is necessary to save file path #
        # and the DB update is only made after the image file validation #
        if request.files['file']:

            img = request.files['file']

            # image file validation #
            filename = img.filename 

            if filename != '':

                file_ext = os.path.splitext(filename)[1]
                if file_ext not in ['.jpg', '.jpeg'] or \
                    file_ext != validate_image(img.stream):
                    
                    return "Invalid image", 400
                
                
            # if valid insert image into DB and get its id to be saved in files #
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('INSERT INTO images (title) VALUES (?);', (("Untitled"),)) # insert image info in images db table #
            img_index = conn.execute('SELECT id FROM images ORDER BY id DESC;').fetchone()
            conn.commit()
            conn.close()
            
            # create file paths and store file #
            fname = str(img_index['id'])+".jpg"

            path = os.path.join((cwd+app.config['UPLOAD_PATH']), fname)

            thumbpath = os.path.join((cwd+app.config['UPLOAD_PATH']+"thumbs"), fname)

            img.save(path) 

            # resize the image file and create its thumbnail #
            image_resize(path, 1200) 

            createthumb(path, thumbpath, 600)

            return '', 204
        
        else:
            return redirect("/gall_mngt"), 400
    

@app.errorhandler(413)
def too_large(e):

    # error handler for file bigger than 10MB upload attempt #
    return "File is too large", 413


@app.route("/imgsrmv", methods=["POST"])
@login_required
def imgsrmv():    

    ## multi imgs gallery removal ##

    # return error if no Id's #
    if not request.form.get("gall_id") or not request.form.get("imgrmvid"):
        return redirect ("/gall_mngt"), 400

    gall_id = request.form.get("gall_id")

    # imgs Id are delivered in a string of ids seperated by comma, split to get the ids from the string and store them in the array #
    imgsIds = request.form.get("imgrmvid").split(",") 
    
    # update image to gallery index table removing all images from this Id table #
    conn = get_db_connection()
    cur = conn.cursor()

    for id in imgsIds:  

        cur.execute('DELETE FROM gall_img_index WHERE gall_id = ? AND img_id = ?;', (gall_id, id,)) # remove the image registry from gallery in the image to gall index table 
        
    conn.commit()
    conn.close() 

    return redirect("/gall_edit?id="+gall_id)  

@app.route("/imgsadd", methods=["POST"])
@login_required
def imgsadd():    

    ## add multi images to gallery ##
    ## same process as the remove multi images, but in this case data is added to the DB table, instead of removed ##

    if not request.form.get("gall_id") or not request.form.get("imgaddid"):
        return redirect ("/gall_mngt")

    gall_id = request.form.get("gall_id")

    imgsIds = request.form.get("imgaddid").split(",")
    
    conn = get_db_connection()
    cur = conn.cursor()

    for id in imgsIds:  

        cur.execute('INSERT INTO gall_img_index (gall_id, img_id) VALUES (?, ?);', (gall_id, id,)) # add image to gallery registry into the image to gall index table 
        
    conn.commit()
    conn.close() 

    return redirect("/gall_edit?id="+gall_id)  