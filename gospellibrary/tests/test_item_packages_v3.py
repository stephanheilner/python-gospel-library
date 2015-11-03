import unittest
from gospellibrary.catalogs import CatalogDB
from gospellibrary.item_packages import ItemPackage
import bs4
import requests
from cachecontrol import CacheControl
from cachecontrol.caches import FileCache

session = CacheControl(requests.session(), cache=FileCache('.gospellibrarycache'))


class Test(unittest.TestCase):
    def test_html(self):
        item = CatalogDB(schema_version='v3', session=session).item(uri='/scriptures/bofm', lang='eng')
        item_package = ItemPackage(item_external_id=item['external_id'], item_version=item['latest_version'], schema_version='v3', session=session)
        p = bs4.BeautifulSoup(item_package.html(subitem_uri='/scriptures/bofm/1-ne/11', paragraph_id='p17')).p
        del p['data-aid']
        actual = str(p)

        expected = '<p class="verse" id="p17"><span class="verse-number">17 </span>And I said unto him: I know that he loveth his children; nevertheless, I do not know the meaning of all things.</p>'

        self.assertEqual(actual, expected)
