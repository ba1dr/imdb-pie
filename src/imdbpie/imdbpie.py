from __future__ import absolute_import

import datetime
import hashlib
import json
import logging
import os
import random
import re
import time
# handle python 2 and python 3 imports
try:
    from urllib.parse import urlencode
    import html.parser as htmlparser
except ImportError:
    from urllib import urlencode
    import HTMLParser as htmlparser
import requests

logger = logging.getLogger(__name__)

BASE_URI = 'app.imdb.com'
API_KEY = '2wex6aeu6a8q9e49k7sfvufd6rhh0n'
SHA1_KEY = hashlib.sha1(API_KEY.encode('utf8')).hexdigest()
USER_AGENTS = (
    'Mozilla/5.0 (iPhone; CPU iPhone OS 5_0_1 like Mac OS X) '
    'AppleWebKit/534.46 (KHTML, like Gecko) Mobile/9A405',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 5_0_1 like Mac OS X) '
    'AppleWebKit/534.46 (KHTML, like Gecko) Mobile/9A406',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 5_0_1 like Mac OS X) '
    'AppleWebKit/534.46 (KHTML, like Gecko) Ver sion/5.1 Mobile/9A405 '
    'Safari/7534.48.3',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 5_0_1 like Mac OS X) '
    'AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9A405 '
    'Safari/7534.48.3',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 5_0_1 like Mac OS X) '
    'AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9A406 '
    'Safari/7534.48.3',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 5_0 like Mac OS X) '
    'AppleWebKit/534.46 (KHTML, like Gecko) Mobile/9A334',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 5_0 like Mac OS X) '
    'AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9A334 '
    'Safari/7534.48.3',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 5_1 like Mac OS X) '
    'AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9B179 '
    'Safari/7534.48.3',
    'Mozilla/5.0(iPhone; U; CPU iPhone OS 4_1 like Mac OS X; en-us)'
    'AppleWebKit/532.9 (KHTML, like Gecko) Version/4.0.5 Mobile/8B5097d '
    'Safari/6531.22.7',
)


class Imdb(object):

    def __init__(self, **options):
        if options.get('debug') is True:
            logger.level = logging.DEBUG
        self.locale = 'en_US'
        self.base_uri = BASE_URI
        self.timestamp = time.mktime(datetime.date.today().timetuple())
        self.user_agent = random.choice(USER_AGENTS)

        self.options = options
        if options.get('anonymize') is True:
            self.base_uri = (
                'aniscartujo.com/webproxy/default.aspx?prx=https://{0}'
            ).format(self.base_uri)

        if options.get('exclude_episodes') is True:
            self.exclude_episodes = True
        else:
            self.exclude_episodes = False

        if options.get('locale'):
            self.locale = options['locale']

        self.caching_enabled = True if options.get('cache') is True else False
        self.cache_dir = options.get('cache_dir') or '/tmp/imdbpiecache'

    def build_url(self, path, params):
        default_params = {
            "api": "v1",
            "appid": "iphone1_1",
            "apiPolicy": "app1_1",
            "apiKey": SHA1_KEY,
            "locale": self.locale,
            "timestamp": self.timestamp
        }

        query_params = dict(
            list(default_params.items()) + list(params.items())
        )
        query_params = urlencode(query_params)
        url = 'https://{0}{1}?{2}'.format(self.base_uri, path, query_params)
        return url

    def find_movie_by_id(self, imdb_id, json=False, credits=True):
        imdb_id = self.validate_id(imdb_id)
        url = self.build_url('/title/maindetails', {'tconst': imdb_id})
        result = self.get(url)
        if 'error' in result:
            return False
        # if the result is a re-dir, see imdb id tt0000021 for e.g...
        if (
            result["data"].get('tconst') !=
            result["data"].get('news', {}).get('channel')
        ):
            return False

        # get the full cast information, add key if not present
        result["data"][str("credits")] = \
            self.get_credits(imdb_id) if credits else {}

        if (
            self.exclude_episodes is True and
            result["data"].get('type') == 'tv_episode'
        ):
            return False
        elif json is True:
            return result["data"]
        else:
            title = Title(**result["data"])
            return title

    def find_person_by_id(self, imdb_id, json=False):
        imdb_id = self.validate_id(imdb_id, itemtype='person')
        url = self.build_url('/name/maindetails', {'nconst': imdb_id})
        result = self.get(url)
        if 'error' in result:
            return False
        # if the result is a re-dir, see imdb id tt0000021 for e.g...
        if (
            result["data"].get('nconst') !=
            result["data"].get('news', {}).get('channel')
        ):
            return False
        if json is True:
            return result["data"]
        else:
            person = Person(**result["data"])
            return person

    def get_credits(self, imdb_id):
        imdb_id = self.validate_id(imdb_id)
        url = self.build_url('/title/fullcredits', {'tconst': imdb_id})
        result = self.get(url)
        return result.get('data').get('credits')

    def filter_out(self, string):
        return string not in ('id', 'title')

    def movie_exists(self, imdb_id):
        """
        Check with imdb, does a movie exist
        """
        imdb_id = self.validate_id(imdb_id, itemtype='title')
        if imdb_id:
            results = self.find_movie_by_id(imdb_id)
            return True if results else False
        return False

    def validate_id(self, imdb_id, itemtype='title'):
        """
        Check imdb id is a 7 digit number
        """
        prefixes = {'title': 'tt', 'person': 'nm',
                    'company': 'co', 'character': 'ch'}
        prefix = prefixes.get(itemtype, 'tt')
        match = re.findall(r'^(?:tt|nm|co|ch)?(\d{1,7})$',
                           str(imdb_id), re.IGNORECASE)
        if match:
            id_num = match[0]
            if len(id_num) < 7:
                # pad id to 7 digits
                id_num = id_num.zfill(7)
            return prefix + id_num
        else:
            return False

    def find_by_title(self, title, production_year=None, kind='any',
                      exact_title=False, episode_for=None, aka_titles=None):
        html_unescaped = htmlparser.HTMLParser().unescape
        # lowercasing all aka_titles to compare:
        aka_titles = [html_unescaped(t).lower() for t in (aka_titles or [])]
        tkind = 'tt'
        movie_kinds = {  # extended search
            'tt': ['any'],
            'ft': ['title', 'movie'],
            'tv': ['tv movie', 'TV mini-series', 'tv series'],
            'ep': ['episode', 'tv episode'],
            'vg': ['video game', 'game'],
        }
        kind = (kind or 'any').lower()  # normalize
        for k in movie_kinds:
            if k == kind or kind in movie_kinds[k]:
                tkind = k
                break
        compare_title = search_title = html_unescaped(title)
        exact_search = exact_title
        if aka_titles:
            # will be filtered by results
            exact_search = False
        if tkind == 'ep' and episode_for:  # episodes
            # search_title = "Episode #%s" % episode_num
            compare_title = html_unescaped(episode_for)
            exact_search = True  # search by exact episode's number
        default_find_by_title_params = {
            'json': '1',
            'nr': 1,
            'tt': 1,
            'ttype': tkind,
            'ex': 1 if exact_search else 0,  # test
            'q': search_title
        }
        query_params = urlencode(default_find_by_title_params)
        results = self.get(
            ('http://akas.imdb.com/xml/find?{0}').format(query_params)
        )

        keys = (
            'title_popular',
            'title_exact',
            'title_approx',
            'title_substring'
        )
        title_results = []

        desc_rex = re.compile(
            ur'^(\d{4})(?:\s*([^,]+)?(,\s*\<a href[^\>]+\>[^\>]+)?)?',
            re.I | re.U)
        ep_rex = re.compile(ur'^(.+):\s*' + search_title, re.I | re.U)
        # Loop through all results and build a list with popular matches first
        for key in keys:
            if key in results:
                for r in results[key]:
                    year = None
                    mkind = ''
                    mtitle = html_unescaped(r['title'])
                    episode_title = html_unescaped(r['episode_title'])
                    title_description = html_unescaped(r['title_description'])
                    if episode_title:
                        m = ep_rex.search(episode_title)
                        if m:
                            mtitle = html_unescaped(m.group(1))
                    if exact_title or exact_search:
                        if mtitle.lower() not in \
                                aka_titles + [compare_title.lower()]:
                            continue
                    m = desc_rex.search(title_description)
                    if m:
                        year = m.group(1)
                        mkind = m.group(2) or ''

                    title_match = {
                        'title': mtitle,
                        'year': year,
                        'kind': mkind,
                        'imdb_id': r['id']
                    }
                    if mkind.lower().find('episode') >= 0:  # if episode
                        title_match['episode_title'] = search_title
                    if production_year and year:
                        if str(production_year) != str(year):
                            continue
                    title_results.append(title_match)

        return title_results

    def find_episode_by_title(self, title, episode_for, year, aka_titles=None):
        pass  # TODO

    def find_person_by_name(self, name):
        html_unescaped = htmlparser.HTMLParser().unescape
        default_find_by_name_params = {
            'json': '1',
            'nr': 1,
            'nm': 'on',
            'q': html_unescaped(name)
        }
        query_params = urlencode(default_find_by_name_params)
        results = self.get(
            ('http://www.imdb.com/xml/find?{0}').format(query_params)
        )

        keys = (
            'name_popular',
            'name_exact',
            'name_approx',
            'name_substring'
        )
        name_results = []

        # Loop through all results and build a list with popular matches first
        for key in keys:
            if key in results:
                for r in results[key]:
                    name_match = {
                        'name': html_unescaped(r['name']),
                        'description': html_unescaped(r['description']),
                        'imdb_id': r['id']
                    }
                    name_results.append(name_match)

        return name_results

    def find_company_by_name(self, name):
        """
            There is likely a bug in IMDb API - it returns empty fields in
            json request. But works in XML.
        """
        html_unescaped = htmlparser.HTMLParser().unescape
        default_find_by_name_params = {
            'json': '0',
            'nr': 1,
            'ex': 1,
            'co': 'on',
            'q': html_unescaped(name)
        }
        query_params = urlencode(default_find_by_name_params)
        url = ('http://www.imdb.com/xml/find?{0}').format(query_params)
        logger.debug("Sending request to {url}".format(url=url))
        result = requests.get(url, headers={'User-Agent': self.user_agent})
        if not result.ok:
            return None
        data = result.content.decode('utf-8')
        name_results = []

        # we will use regex instead on XML parser like lxml:
        # to avoid dependency and to fasten the processing
        xrex = re.compile(
            ur'\<ImdbEntity id=\"((?:tt|nm|co|ch)[\d]+)\"\>([^\<]*)' +
            '\<Description\>([^\<]*)\<\/Description\>\<\/ImdbEntity\>', re.I)
        results = xrex.findall(data)
        for imdb_id, company_name, description in results:
            if company_name != html_unescaped(name):
                continue  # 'ex=1' does the same
            name_match = {
                'name': html_unescaped(name),
                'description': html_unescaped(description),
                'imdb_id': imdb_id
            }
            name_results.append(name_match)

        return name_results

    def top_250(self):
        url = self.build_url('/chart/top', {})
        result = self.get(url)
        return result["data"]["list"]["list"]

    def popular_shows(self):
        url = self.build_url('/chart/tv', {})
        result = self.get(url)
        return result["data"]["list"]

    def get_images(self, result):
        if 'error' in result:
            return False

        results = []
        if 'photos' in result.get('data'):
            for image in result.get('data').get('photos'):
                results.append(Image(**image))
        return results

    def title_images(self, imdb_id):
        url = self.build_url('/title/photos', {'tconst': imdb_id})
        result = self.get(url)
        return self.get_images(result)

    def title_reviews(self, imdb_id, limit=10):
        """
        Retrieves reviews for a title ordered by 'Best' descending
        """
        url = self.build_url(
            '/title/usercomments',
            {'tconst': imdb_id, 'limit': limit}
        )
        result = self.get(url)
        if 'error' in result:
            return None

        title_reviews = []
        user_comments = result.get('data').get('user_comments')

        if not user_comments:
            return None

        for review_data in result['data']['user_comments']:
            title_reviews.append(Review(review_data))
        return title_reviews

    def person_images(self, imdb_id):
        url = self.build_url('/name/photos', {'nconst': imdb_id})
        result = self.get(url)
        return self.get_images(result)

    def _get_cache_item_path(self, url):
        """
        Generates a cache location for a given api call.
        Returns a file path
        """
        cache_dir = self.cache_dir
        m = hashlib.md5()
        m.update(url.encode('utf-8'))
        cache_key = m.hexdigest()

        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        return os.path.join(cache_dir, cache_key + '.cache')

    def _get_cached_response(self, file_path):
        """ Retrieves response from cache """
        if os.path.exists(file_path):
            logger.info('retrieving from cache: %s', file_path)

            with open(file_path, 'r+') as resp_data:
                cached_resp = json.load(resp_data)

            if cached_resp.get('exp') > self.timestamp:
                return cached_resp

            logger.info('cached expired, removing: %s', file_path)
            os.remove(file_path)
        return None

    @staticmethod
    def _cache_response(file_path, resp):
        with open(file_path, 'w+') as f:
            json.dump(resp, f)

    def get(self, url):
        logger.debug("Sending request to {url}".format(url=url))
        if self.caching_enabled:
            cached_item_path = self._get_cache_item_path(url)
            cached_resp = self._get_cached_response(cached_item_path)
            if cached_resp:
                return cached_resp

        r = requests.get(url, headers={'User-Agent': self.user_agent})
        response = json.loads(htmlparser.HTMLParser().unescape(r.text))

        if self.caching_enabled:
            self._cache_response(cached_item_path, response)

        return response


class Person(object):

    def __init__(self, **person):
        self.data = person
        p = person.get('name')
        # token and label are the persons categorisation
        # e.g token: writers label: Series writing credits
        self.token = person.get('token')
        self.label = person.get('label')

        # attr is a note about this persons work
        # e.g. (1990 - 1992 20 episodes)
        self.attr = person.get('attr')

        # other primary information about their part
        if isinstance(p, dict):  # if passed as credit's part
            self.name = p.get('name')
            self.imdb_id = p.get('nconst')
            self.role = (
                person.get('char').split('/') if person.get('char') else None
            )
            self.job = person.get('job')
        else:
            self.name = p
            self.imdb_id = person.get('nconst')

    def __repr__(self):
        repr = '<Person: {0} ({1})>'
        return repr.format(self.name.encode('utf-8'), self.imdb_id)


class Title(object):

    def __init__(self, **kwargs):
        self.data = kwargs

        self.imdb_id = self.data.get('tconst')
        self.title = self.data.get('title')
        self.type = self.data.get('type')
        self.year = self._extract_year(self.data)
        self.tagline = self.data.get('tagline')
        self.plot = self.data.get('plot')
        self.runtime = self.data.get('runtime')
        self.rating = self.data.get('rating')
        self.genres = self.data.get('genres')
        self.votes = self.data.get('num_votes')

        self.plot_outline = None
        if 'plot' in self.data and 'outline' in self.data['plot']:
            self.plot_outline = self.data['plot']['outline']

        self.runtime = None
        if 'runtime' in self.data:
            # mins
            self.runtime = str(int((self.data['runtime']['time'] / 60)))

        self.poster_url = None
        if 'image' in self.data and 'url' in self.data['image']:
            self.poster_url = self.data['image']['url']

        self.cover_url = None
        if 'image' in self.data and 'url' in self.data['image']:
            self.cover_url = '{0}_SX214_.jpg'.format(
                self.data['image']['url'].replace('.jpg', '')
            )

        self.release_date = None
        if (
            'release_date' in self.data and
            'normal' in self.data['release_date']
        ):
            self.release_date = self.data['release_date']['normal']

        self.certification = None
        if (
            'certificate' in self.data and
            'certificate' in self.data['certificate']
        ):
            self.certification = self.data['certificate']['certificate']

        self.trailer_img_url = None
        if (
            'trailer' in self.data and
            'slates' in self.data['trailer'] and
            self.data['trailer']['slates']
        ):
            self.trailer_img_url = self.data['trailer']['slates'][0]['url']

        # Directors summary
        self.directors_summary = []
        if self.data.get('directors_summary'):
            for director in self.data['directors_summary']:
                self.directors_summary.append(Person(**director))

        # Creators
        self.creators = []
        if self.data.get('creators'):
            for creator in self.data['creators']:
                self.creators.append(Person(**creator))

        # Cast summary
        self.cast_summary = []
        if self.data.get('cast_summary'):
            for cast in self.data['cast_summary']:
                self.cast_summary.append(Person(**cast))

        # Writers summary
        self.writers_summary = []
        if self.data.get('writers_summary'):
            for writer in self.data['writers_summary']:
                self.writers_summary.append(Person(**writer))

        # Credits
        self.credits = []
        if self.data.get('credits'):
            for credit in self.data['credits']:
                """
                Possible tokens: directors, cast, writers,
                producers and others
                """
                for person in credit['list']:
                    person_extra = {
                        'token': credit.get('token'),
                        'label': credit.get('label'),
                        'job': person.get('job'),
                        'attr': person.get('attr')
                    }
                    person = dict(
                        list(person_extra.items()) + list(person.items())
                    )
                    if 'name' in person:
                        # some 'special' credits such as script
                        # rewrites have different formatting
                        # check for 'name' is a temporary fix for this,
                        # we lose a minimal amount of data from this
                        self.credits.append(Person(**person))

        # Trailers
        self.trailers = {}
        if 'trailer' in self.data and 'encodings' in self.data['trailer']:
            for k, v in list(self.data['trailer']['encodings'].items()):
                self.trailers[v['format']] = v['url']

    @staticmethod
    def _extract_year(data):
        year = data.get('year')
        if year == '????':  # if there's no year the API returns this...
            return None
        return int(year)


class Image(object):

    def __init__(self, **image):
        self.caption = image.get('caption')
        self.url = image.get('image').get('url')
        self.width = image.get('image').get('width')
        self.height = image.get('image').get('height')

    def __repr__(self):
        return '<Image: {0}>'.format(self.caption.encode('utf-8'))


class Review(object):

    def __init__(self, review):
        self.username = review.get('user_name')
        self.text = review.get('text')
        self.date = review.get('date')
        self.rating = review.get('user_rating')
        self.summary = review.get('summary')
        self.status = review.get('status')
        self.user_location = review.get('user_location')
        self.user_score = review.get('user_score')
        self.user_score_count = review.get('user_score_count')

    def __repr__(self):
        return '<Review: {0}>'.format(self.text[:20])
