import requests
from cachecontrol import CacheControl
from cachecontrol.caches import FileCache
import logging
from StringIO import StringIO
from zipfile import ZipFile
from tempfile import mkdtemp
import os
from pysqlite2 import dbapi2 as sqlite3
import shutil
from contextlib import contextmanager

DEFAULT_BASE_URL = 'http://broadcast3.lds.org/crowdsource/mobile/gospelstudy/production'
SCHEMA_VERSION = '2.0.2'

logger = logging.getLogger('gospellibrary')
session = CacheControl(requests.session(), cache=FileCache('.gospellibrarycache'))


class Catalog:
    def __init__(self, base_url=DEFAULT_BASE_URL):
        self.base_url = base_url
        self.schema_version = SCHEMA_VERSION

    def __repr__(self):
        return 'Catalog()'

    def current_version(self):
        logger.info('Getting the current catalog version')

        index_url = '{base_url}/{schema_version}/index.json'.format(base_url=self.base_url,
                                                                    schema_version=self.schema_version)
        r = session.get(index_url)
        if r.status_code == 200:
            index = r.json()
            catalog_version = index.get('catalogVersion', 0)
            if catalog_version >= 1:
                return catalog_version

        raise ValueError('failed to get the current catalog version')

    def item(self, uri, lang):
        catalog_version = self.current_version()

        logger.info('Getting catalog {catalog_version}'.format(catalog_version=catalog_version))

        catalog_zip_url = '{base_url}/{schema_version}/catalogs/{catalog_version}.zip'.format(
            base_url=self.base_url,
            schema_version=self.schema_version,
            catalog_version=catalog_version)
        r = session.get(catalog_zip_url)
        if r.status_code == 200:
            catalog_path = os.path.join(mkdtemp(), 'Catalog.sqlite')
            try:
                try:
                    os.makedirs(os.path.dirname(catalog_path))
                except OSError:
                    pass

                with ZipFile(StringIO(r.content), 'r') as catalog_zip_file:
                    catalog_zip_file.extractall(os.path.dirname(catalog_path))

                with sqlite3.connect(catalog_path) as db:
                    c = db.cursor()
                    try:
                        c.execute('''
                                SELECT external_id, latest_version FROM item
                                    INNER JOIN language ON item.language_id=language._id
                                WHERE uri=? AND iso639_3=?''', (uri, lang))
                        item_external_id, item_version = c.fetchone()
                        return Item(base_url=self.base_url, item_external_id=item_external_id, version=item_version)
                    finally:
                        c.close()
            finally:
                shutil.rmtree(catalog_path, ignore_errors=True)

        raise ValueError('failed to get the item')


class Item:
    def __init__(self, base_url, item_external_id, version):
        self.base_url = base_url
        self.schema_version = SCHEMA_VERSION
        self.item_external_id = item_external_id
        self.version = version

    def __repr__(self):
        return 'Item(item_external_id="{item_external_id}", version="{version}")'.format(
            item_external_id=self.item_external_id,
            version=self.version)

    @contextmanager
    def package(self):
        logger.info('Getting version {item_version} of {item_external_id}'.format(
            item_version=self.version,
            item_external_id=self.item_external_id))

        item_package_zip_url = '{base_url}/{schema_version}/item-packages/{item_external_id}/{item_version}.zip'.format(
            base_url=self.base_url,
            schema_version=self.schema_version,
            item_external_id=self.item_external_id,
            item_version=self.version)
        r = session.get(item_package_zip_url)
        if r.status_code == 200:
            item_package_path = os.path.join(mkdtemp(), 'package.sqlite')

            try:
                os.makedirs(os.path.dirname(item_package_path))
            except OSError:
                pass

            with ZipFile(StringIO(r.content), 'r') as catalog_zip_file:
                catalog_zip_file.extractall(os.path.dirname(item_package_path))

            package = ItemPackage(path=item_package_path)
            try:
                yield package
            finally:
                package.close()
            return

        raise ValueError('failed to get the item package')


class ItemPackage:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.text_factory = str

    def close(self):
        self.db.close()

    def html(self, uri):
        c = self.db.cursor()
        try:
            c.execute('''
                    SELECT content, start_index, end_index FROM subitem_content_range
                        INNER JOIN subitem_content ON subitem_content_range.subitem_id=subitem_content.subitem_id
                    WHERE uri=?''', [uri])
            (html, start_index, end_index) = c.fetchone()

            return html[start_index:end_index]
        finally:
            c.close()
