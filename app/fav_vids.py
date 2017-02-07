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

    sorted_pages = []
    for page in sorted(page_nums):
        sorted_pages.append(int(page))

    return sorted_pages


def get_video_url(page_nums):
    if not isinstance(page_nums, list):
        page_nums_list = [page_nums]
    else:
        page_nums_list = page_nums

    video_id = set()
    for n in page_nums_list:
        for a in BeautifulSoup(urllib2.urlopen('http://www.pinkbike.com/u/Btodhunter/channel/favorites/?page={}'.format(n)),
                               "html.parser").find_all('a'):
            if 'video' in a.get('href'):
                video = [s for s in str(a.get('href')).split('/') if s.isdigit()]
                for i in video:
                    video_id = i

    video_urls = set()
    for url in video_id:
        video_urls.add('http://www.pinkbike.com/v/embed/{}/?colors=000000'.format(url))

    return video_urls

