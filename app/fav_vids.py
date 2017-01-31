import urllib2
from bs4 import BeautifulSoup


def get_page_numbers():
    pb_favorites_url = 'http://www.pinkbike.com/u/Btodhunter/channel/favorites'
    pb_favorite_videos = urllib2.urlopen(pb_favorites_url)

    pb_favs_parsed = BeautifulSoup(pb_favorite_videos, "html.parser")

    page_links = (pb_favs_parsed.find('table', class_='paging-container')).find_all('a')

    page_nums = set()

    for link in page_links:
        page_nums.add(link.get('href').split('=')[-1])

    return sorted(page_nums)


def get_video_id(page_num):
    video_id = set()

    for n in page_num:
        for a in BeautifulSoup(urllib2.urlopen('http://www.pinkbike.com/u/Btodhunter/channel/favorites/?page={}'.format(n)),
                               "html.parser").find_all('a'):
            if 'video' in a.get('href'):
                video = [s for s in str(a.get('href')).split('/') if s.isdigit()]
                for x in video:
                    video_id.add(x)

    return video_id