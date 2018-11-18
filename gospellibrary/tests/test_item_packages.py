import unittest
from gospellibrary.catalogs import CatalogDB
from gospellibrary.item_packages import ItemPackage
import bs4
import requests
from cachecontrol import CacheControl
from cachecontrol.caches import FileCache

session = CacheControl(requests.session(), cache=FileCache('.gospellibrarycache'))


class Test(unittest.TestCase):
    def test_para_html(self):
        item = CatalogDB(session=session).item(uri='/scriptures/bofm', lang='eng')
        item_package = ItemPackage(item_external_id=item['external_id'], item_version=item['version'], session=session)
        p = bs4.BeautifulSoup(item_package.html(subitem_uri='/scriptures/bofm/1-ne/11', paragraph_id='p17'), 'lxml').p
        del p['data-aid']
        actual = str(p)

        expected = '<p class="verse" id="p17"><span class="verse-number">17 </span>And I said unto him: I know that he loveth his children; nevertheless, I do not know the meaning of all things.</p>'

        self.assertEqual(actual, expected)

    def test_subitem_html(self):
        item = CatalogDB(session=session).item(uri='/scriptures/ot', lang='eng')
        item_package = ItemPackage(item_external_id=item['external_id'], item_version=item['version'], session=session)
        doc = bs4.BeautifulSoup(item_package.html(subitem_uri='/scriptures/ot/ps/117'), 'lxml')

        self.assertEqual('<p class="title-number" data-aid="128444354" id="title_number1">Psalm 117</p>', str(doc.find(id='title_number1')))
        self.assertEqual('<p class="verse" data-aid="128444356" id="p1"><span class="verse-number">1 </span>O praise the <span class="deity-name"><span class="small-caps">Lord</span></span>, all ye nations: praise him, all ye people.</p>', str(doc.find(id='p1')))

    def test_subitems(self):
        item = CatalogDB(session=session).item(uri='/manual/family-finances', lang='eng')
        item_package = ItemPackage(item_external_id=item['external_id'], item_version=item['version'], session=session)
        subitems = item_package.subitems()

        self.assertEqual(len(subitems), 1)
        self.assertEqual(subitems[0]['id'], 1)
        self.assertEqual(subitems[0]['uri'], '/manual/family-finances/family-finances')
        self.assertEqual(subitems[0]['title'], 'Prepare Every Needful Thing: Family Finances')

    def test_subitem(self):
        item = CatalogDB(session=session).item(uri='/manual/family-finances', lang='eng')
        item_package = ItemPackage(item_external_id=item['external_id'], item_version=item['version'], session=session)

        subitem = item_package.subitem(uri='/manual/family-finances/family-finances')

        self.assertEqual(subitem['id'], 1)
        self.assertEqual(subitem['uri'], '/manual/family-finances/family-finances')
        self.assertEqual(subitem['title'], 'Prepare Every Needful Thing: Family Finances')

    def test_related_audio_items(self):
        item = CatalogDB(session=session).item(uri='/manual/new-testament-stories', lang='eng')
        item_package = ItemPackage(item_external_id=item['external_id'], item_version=item['version'], session=session)

        subitem = item_package.subitem(uri='/manual/new-testament-stories/chapter-36-jesus-tells-three-parables')
        subitem_id = subitem['id']

        related_audio_items = item_package.related_audio_items(subitem_id)

        self.assertEqual(len(related_audio_items), 1)
        self.assertEqual(related_audio_items[0]['id'], 37)
        self.assertEqual(related_audio_items[0]['subitem_id'], subitem_id)
        self.assertEqual(related_audio_items[0]['media_url'], 'https://media2.ldscdn.org/assets/scripture-and-lesson-support/new-testament-stories/2010-11-370-chapter-36-jesus-tells-three-parables-complete-256k-eng.mp3')

    def test_related_video_items(self):
        item = CatalogDB(session=session).item(uri='/manual/new-testament-stories', lang='eng')
        item_package = ItemPackage(item_external_id=item['external_id'], item_version=item['version'], session=session)

        subitem_id = 38

        related_video_items = item_package.related_video_items(subitem_id)

        self.assertEqual(len(related_video_items), 1)
        self.assertEqual(related_video_items[0]['id'], 35)
        self.assertEqual(related_video_items[0]['subitem_id'], subitem_id)
        self.assertEqual(related_video_items[0]['video_id'], '760176381001')
        self.assertEqual(related_video_items[0]['poster_url'], 'https://mediasrv.lds.org/media-services/CM/videoStill/760176381001')
        self.assertEqual(related_video_items[0]['title'], 'Chapter 35: The Good Samaritan')

    def test_package_related_content_items(self):
        item = CatalogDB(session=session).item(uri='/scriptures/ot', lang='eng')
        item_package = ItemPackage(item_external_id=item['external_id'], item_version=item['version'], session=session)

        subitem = item_package.subitem(uri='/scriptures/ot/ps/117')
        subitem_id = subitem['id']

        related_content_items = item_package.related_content_items(subitem_id)

        self.assertEqual(len(related_content_items), 1)
        self.assertEqual(related_content_items[0]['id'], 11429)
        self.assertEqual(related_content_items[0]['subitem_id'], subitem_id)
        self.assertEqual(related_content_items[0]['word_offset'], 11)
        self.assertEqual(related_content_items[0]['byte_location'], 2646)
        self.assertEqual(related_content_items[0]['origin_id'], 'p2')
        self.assertEqual(related_content_items[0]['ref_id'], 'note2a')
        self.assertEqual(related_content_items[0]['label_html'], '2<em>a</em>')
        self.assertEqual(related_content_items[0]['content_html'], '<p data-aid="128444358" id="note2a_p1"><a class="scripture-ref" href="gospellibrary://content/scriptures/dc-testament/dc/84?verse=45#p45">D&amp;C 84:45</a>; <a class="scripture-ref" href="gospellibrary://content/scriptures/dc-testament/dc/93?verse=24#p24">93:24</a>.</p>')
