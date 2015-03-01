from imdbpie import Imdb
try:
    import unittest2 as unittest  # for Python <= 2.6
except ImportError:
    import unittest

imdb = Imdb(anonymize=False)
movie = imdb.find_movie_by_id("tt0382932")


class TestPerson(unittest.TestCase):

    def test_name(self):
        self.assertIsNotNone(movie.credits)

    def test_director(self):
        self.assertEqual(movie.directors_summary[0].name, 'Brad Bird')

    def test_director_role(self):
        self.assertFalse(movie.directors_summary[0].role)

    def test_writers(self):
        self.assertEqual(movie.writers_summary[0].name, 'Brad Bird')

    def test_writers_role(self):
        self.assertFalse(movie.writers_summary[0].role)

    def test_search_person_lumet(self):
        self.results = imdb.find_person_by_name("Sidney Lumet")
        self.assertGreater(len(self.results), 1)

    def test_search_person_bad(self):
        self.results = imdb.find_person_by_name("afajshfd1kajhsdk3fjaskdj55a")
        self.assertEquals(len(self.results), 0)

    def test_search_person_by_id(self):
        person = imdb.find_person_by_id("nm0001486")
        self.assertEqual(person.name, 'Sidney Lumet')

if __name__ == '__main__':
    unittest.main()
