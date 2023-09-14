import imghdr
import sqlite3


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

