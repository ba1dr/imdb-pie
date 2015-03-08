from imdbpie import Imdb
try:
    import unittest2 as unittest  # for Python <= 2.6
except ImportError:
    import unittest

imdb = Imdb(anonymize=False)


class TestSearch(unittest.TestCase):

    def test_batman(self):
        self.results = imdb.find_by_title("batman")
        self.assertGreater(len(self.results), 15)

    def test_batman_1996(self):
        self.results = imdb.find_by_title("batman forever", 1996)
        self.assertEquals(len(self.results), 1)

    def test_title_kind(self):
        ttitle = "Batman: Arkham Knight"
        # more than 1 result by 'tt' search,
        # but 1 exact result for 'video game'
        self.results = imdb.find_by_title(ttitle)
        reslen1 = len(self.results)
        self.results = imdb.find_by_title(ttitle, kind='video game')
        reslen2 = len(self.results)
        self.assertGreater(reslen1, reslen2)  # second returns less results

    def test_title_aka(self):
        # simple search does not work
        # because of the movie returned by its primary name 'American Sniper'
        self.results = imdb.find_by_title(title='Francotirador',
                                          production_year=2014,
                                          exact_title=True)
        self.assertEquals(len(self.results), 0)  # no results

        # extended search by aka
        self.results = imdb.find_by_title(title='Francotirador',
                                          production_year=2014,
                                          aka_titles=['American Sniper'],
                                          kind='movie',
                                          exact_title=True)
        self.assertEquals(len(self.results), 1)
        self.assertEquals(self.results[0]['imdb_id'], u'tt2179136')

    def test_episode1(self):
        self.results = imdb.find_by_title(title='Episode (#2.49)',
                                          production_year=1973,
                                          episode_for='The New Price Is Right',
                                          kind='tv episode',
                                          aka_titles=['the price is right'])
        self.assertEquals(len(self.results), 1)
        self.assertEquals(self.results[0]['imdb_id'], u'tt1187172')
        self.assertEquals(self.results[0]['kind'], u'TV episode')
        self.assertEquals(self.results[0]['episode_title'], u'Episode (#2.49)')

    def test_company(self):
        self.results = imdb.find_company_by_name("MTS")
        self.assertEquals(len(self.results), 1)

    def test_truman(self):
        self.results = imdb.find_by_title("the truman show")
        self.assertGreater(len(self.results), 1)

    def test_bad_search(self):
        self.results = imdb.find_by_title("fdlfj494llsidjg49hkdg")
        self.assertEquals(len(self.results), 0)

    def test_top_250(self):
        self.movies = imdb.top_250()
        self.assertTrue(isinstance(self.movies[0], dict))

    def test_popular_shows(self):
        self.shows = imdb.popular_shows()
        self.assertTrue(isinstance(self.shows[0], dict))


if __name__ == '__main__':
    unittest.main()
