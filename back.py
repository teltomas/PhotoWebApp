import os
import imghdr
import sqlite3
import PIL

from PIL import Image
from flask import redirect, session
from functools import wraps

# image resizing as the tutorial from https://www.holisticseo.digital/python-seo/resize-image/ #


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

# determine ig images uploaded are indeed images as defined here: #
# https://blog.miguelgrinberg.com/post/handling-file-uploads-with-flask #

def validate_image(stream):
    header = stream.read(512)
    stream.seek(0) 
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')

# resize images and create thumbnails to web use #
# as shown here: https://cloudinary.com/guides/bulk-image-resize/python-image-resize-with-pillow-and-opencv #

def image_resize(path, fixed_height):

    image = Image.open(path)
    height_percent = (fixed_height / float(image.size[1]))
    width_size = int((float(image.size[0]) * float(height_percent)))
    image = image.resize((width_size, fixed_height), PIL.Image.NEAREST)
    image.save(path)
    
    return


def createthumb(path, thumbpath, size):
    
    image = Image.open(path)
    image.thumbnail((size, size))
    image.save(thumbpath)

    return

# login required as implementation on CS50Finance #
def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


# image upload and save function #
# image: file uploaded; path: path to save the file including file name; #
# extensions: allowed file extentions in this upload; size: height of image size to order its resize #
# Return: false if upload failed, true if success #
# https://blog.miguelgrinberg.com/post/handling-file-uploads-with-flask #
def img_upload(image, path, extentions, size):

    filename = image.filename

    # validate image file and return error message in case of failed upload #
    if filename != '':

        file_ext = os.path.splitext(filename)[1]
        if file_ext not in extentions or \
            file_ext != validate_image(image.stream):
            
            return False
    
    # save file #
    image.save(path)

    # resize image if size determined #
    if size != None:

        image_resize(path, size)

    # return if success #
    return True