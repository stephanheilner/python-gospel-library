# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import unittest
from gospellibrary.catalogs import current_catalog_version, CatalogDB
import requests
from cachecontrol import CacheControl
from cachecontrol.caches import FileCache

session = CacheControl(requests.session(), cache=FileCache('.gospellibrarycache'))


class Test(unittest.TestCase):
    def test_current_catalog_version(self):
        self.assertGreaterEqual(current_catalog_version(session=session), 1)

    def test_language_names(self):
        self.assertEqual(CatalogDB(iso639_3_code='eng', session=session).language_name(language_id=1), 'English')
        self.assertEqual(CatalogDB(iso639_3_code='eng', session=session).language_name(language_id=3), 'Spanish')
        self.assertEqual(CatalogDB(iso639_3_code='spa', session=session).language_name(language_id=1), 'Inglés')
        self.assertEqual(CatalogDB(iso639_3_code='spa', session=session).language_name(language_id=3), 'Español')

    def test_item_by_id(self):
        item = CatalogDB(session=session).item(128350135)
        self.assertEqual(item['external_id'], '_scriptures_bofm_000')
        self.assertGreaterEqual(item['version'], 1)

    def test_item_by_uri_and_lang(self):
        item = CatalogDB(session=session).item(uri='/scriptures/bofm')
        self.assertEqual(item['external_id'], '_scriptures_bofm_000')
        self.assertGreaterEqual(item['version'], 1)

    def test_items(self):
        items = CatalogDB(iso639_3_code='eng', session=session).items()
        next(item for item in items if item['uri'] == '/scriptures/bofm' and item['language_id'] == 1)
        next(item for item in items if item['uri'] == '/general-conference/2014/10' and item['language_id'] == 1)

        items = CatalogDB(iso639_3_code='spa', session=session).items()
        next(item for item in items if item['uri'] == '/scriptures/bofm' and item['language_id'] == 3)
        next(item for item in items if item['uri'] == '/general-conference/2014/10' and item['language_id'] == 3)
