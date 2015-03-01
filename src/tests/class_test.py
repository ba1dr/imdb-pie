from imdbpie import Imdb
try:
    import unittest2 as unittest  # for Python <= 2.6
except ImportError:
    import unittest

imdb = Imdb(anonymize=False)


class TestPieClass(unittest.TestCase):

    def test_validate_id(self):
        testdata = (
            # positive
            ('tt0382932', 'tt0382932', -1),
            ('382932', 'tt0382932', -1),
            ('382932', 'tt0382932', None),
            ('382932', 'tt0382932', 'title'),
            ('0382932', 'tt0382932', 'title'),
            ('tt382932', 'tt0382932', 'title'),
            (382932, 'tt0382932', 'title'),
            ('382932', 'tt0382932', 'blablabla'),
            ('nm0001486', 'nm0001486', 'person'),
            ('1486', 'nm0001486', 'person'),
            ('nm1486', 'nm0001486', 'person'),
            ('01486', 'nm0001486', 'person'),
            ('1486', 'ch0001486', 'character'),
            ('1486', 'co0001486', 'company'),
            # negative
            ('test me', False, -1),
            (None, False, -1),
            ([], False, -1),
            ('xx0382932', False, -1),
            ('123456789', False, -1),
            ('tt382932 asdfg', False, -1),
            ('bbbtt382932', False, -1),
            ('xx0382932', False, 'title'),
        )
        for id_input, expected, itemtype in testdata:
            if itemtype == -1:  # to use default
                imdb_id = imdb.validate_id(id_input)
            else:
                imdb_id = imdb.validate_id(id_input, itemtype=itemtype)
            self.assertEqual(imdb_id, expected)

if __name__ == '__main__':
    unittest.main()
