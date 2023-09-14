
# Jinja style : data show format #

def date(value):
    
    return value[:10]

# Jinja style : Capitalize sentences #

def capital(text):

    return text.capitalize()

# Jinja style : link http mngement #

def dblink(link):

    if link and link[:6] != "http://":

        link = "http://" + str(link)

    return link