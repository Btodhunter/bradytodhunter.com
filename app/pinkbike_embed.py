import urllib2
from bs4 import BeautifulSoup


def get_embed_page(favorite_url):
    embed_page = urllib2.urlopen(favorite_url)

    embed_html = BeautifulSoup(embed_page, "html.parser")
    print embed_html

get_embed_page('http://www.pinkbike.com/v/embed/303941/?colors=000000')