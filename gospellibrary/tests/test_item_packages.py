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
        item = CatalogDB(session=session).item(uri='/scriptures/bofm', lang='eng')
        item_package = ItemPackage(item_external_id=item['external_id'], item_version=item['version'], session=session)
        p = bs4.BeautifulSoup(item_package.html(uri='/scriptures/bofm/1-ne/11.17'), 'lxml').p
        del p['pid']
        del p['hash']
        actual = str(p)

        expected = '<p class="verse" uri="/scriptures/bofm/1-ne/11.17"><span class="verseNumber">17</span>And I said unto him: I know that he loveth his children; nevertheless, I do not know the meaning of all things.</p>'

        self.assertEqual(actual, expected)

    def test_subitems(self):
        item = CatalogDB(session=session).item(uri='/manual/all-is-safely-gathered-in-family-finances', lang='eng')
        item_package = ItemPackage(item_external_id=item['external_id'], item_version=item['version'], session=session)
        subitems = item_package.subitems()

        self.assertEqual(len(subitems), 1)
        self.assertEqual(subitems[0]['id'], 1)
        self.assertEqual(subitems[0]['uri'], '/manual/all-is-safely-gathered-in-family-finances/all-is-safely-gathered-in-family-finances')
        self.assertEqual(subitems[0]['title'], 'All Is Safely Gathered In: Family Finances')

    def test_subitem(self):
        item = CatalogDB(session=session).item(uri='/manual/all-is-safely-gathered-in-family-finances', lang='eng')
        item_package = ItemPackage(item_external_id=item['external_id'], item_version=item['version'], session=session)

        subitem = item_package.subitem(uri='/manual/all-is-safely-gathered-in-family-finances/all-is-safely-gathered-in-family-finances')

        self.assertEqual(subitem['id'], 1)
        self.assertEqual(subitem['uri'], '/manual/all-is-safely-gathered-in-family-finances/all-is-safely-gathered-in-family-finances')
        self.assertEqual(subitem['title'], 'All Is Safely Gathered In: Family Finances')

    def test_related_audio_items(self):
        item = CatalogDB(session=session).item(uri='/manual/new-testament-stories', lang='eng')
        item_package = ItemPackage(item_external_id=item['external_id'], item_version=item['version'], session=session)

        subitem_id = 38

        related_audio_items = item_package.related_audio_items(subitem_id)

        self.assertEqual(len(related_audio_items), 1)
        self.assertEqual(related_audio_items[0]['id'], 34)
        self.assertEqual(related_audio_items[0]['subitem_id'], subitem_id)
        self.assertEqual(related_audio_items[0]['media_url'], 'http://media2.ldscdn.org/assets/scripture-and-lesson-support/new-testament-stories/2010-11-370-chapter-36-jesus-tells-three-parables-complete-256k-eng.mp3')

    def test_related_video_items(self):
        item = CatalogDB(session=session).item(uri='/manual/new-testament-stories', lang='eng')
        item_package = ItemPackage(item_external_id=item['external_id'], item_version=item['version'], session=session)

        subitem_id = 38

        related_video_items = [related_video_item for related_video_item in item_package.related_video_items(subitem_id) if related_video_item['container_type'] == 1]

        self.assertEqual(len(related_video_items), 1)
        self.assertEqual(related_video_items[0]['id'], 430)
        self.assertEqual(related_video_items[0]['subitem_id'], subitem_id)
        self.assertEqual(related_video_items[0]['media_url'], 'http://c.brightcove.com/services/mobile/streaming/index/master.m3u8?videoId=1288200371001')
        self.assertEqual(related_video_items[0]['container_type'], 1)

    def test_package_related_content_items(self):
        item = CatalogDB(session=session).item(uri='/scriptures/ot', lang='eng')
        item_package = ItemPackage(item_external_id=item['external_id'], item_version=item['version'], session=session)

        # Psalms 117
        subitem_id = 596

        related_content_items = item_package.related_content_items(subitem_id)

        self.assertEqual(len(related_content_items), 1)
        self.assertEqual(related_content_items[0]['id'], 11429)
        self.assertEqual(related_content_items[0]['subitem_id'], subitem_id)
        self.assertEqual(related_content_items[0]['position'], 0)
        self.assertEqual(related_content_items[0]['name'], 'f_2a')
        self.assertEqual(related_content_items[0]['label'], '2a')
        self.assertEqual(related_content_items[0]['label_content'], 'truth')
        self.assertEqual(related_content_items[0]['origin_uri'], '/scriptures/ot/ps/117.2')
        self.assertEqual(related_content_items[0]['content'], '<a href="/scriptures/dc-testament/dc/84.45" class="scriptureRef">D&amp;C 84:45</a>; <a href="/scriptures/dc-testament/dc/93.24" class="scriptureRef">93:24</a>.')
