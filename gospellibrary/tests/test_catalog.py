import unittest
from gospellibrary import Catalog
import logging
import bs4

logger = logging.getLogger('gospellibrary')


class Test(unittest.TestCase):
    def test_current_version(self):
        self.assertGreaterEqual(Catalog().current_version(), 1)

    def test_item(self):
        item = Catalog().item(uri='/scriptures/bofm', lang='eng')
        self.assertEqual(item.item_external_id, '_scriptures_bofm_000')
        self.assertGreaterEqual(item.version, 1)

    def test_package_html(self):
        with Catalog().item(uri='/scriptures/bofm', lang='eng').package() as package:
            p = bs4.BeautifulSoup(package.html(uri='/scriptures/bofm/1-ne/11.17')).p
            del p['pid']
            del p['hash']
            actual = str(p)

            expected = '<p class="verse" uri="/scriptures/bofm/1-ne/11.17"><span class="verseNumber">17</span>And I said unto him: I know that he loveth his children; nevertheless, I do not know the meaning of all things.</p>'

            self.assertEqual(actual, expected)
