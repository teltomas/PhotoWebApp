import imghdr

# determine ig images uploaded are indeed images as defined here: #
# https://blog.miguelgrinberg.com/post/handling-file-uploads-with-flask #

def validate_image(stream):
    header = stream.read(512)
    stream.seek(0) 
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')