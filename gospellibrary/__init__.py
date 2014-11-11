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


class Catalog:
    def __init__(self, base_url=DEFAULT_BASE_URL, cache_dir='.gospellibrarycache'):
        self.base_url = base_url
        self.schema_version = SCHEMA_VERSION
        self.session = CacheControl(requests.session(), cache=FileCache(cache_dir))

    def __repr__(self):
        return 'Catalog()'

    def current_version(self):
        logger.info('Getting the current catalog version')

        index_url = '{base_url}/{schema_version}/index.json'.format(base_url=self.base_url,
                                                                    schema_version=self.schema_version)
        r = self.session.get(index_url)
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
        r = self.session.get(catalog_zip_url)
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
                                SELECT external_id, latest_version, title FROM item
                                    INNER JOIN language ON item.language_id=language._id
                                WHERE uri=? AND iso639_3=?''', (uri, lang))
                        item_external_id, item_version, item_title = c.fetchone()
                        return Item(base_url=self.base_url,
                                    session=self.session,
                                    item_external_id=item_external_id,
                                    version=item_version,
                                    title=item_title)
                    finally:
                        c.close()
            finally:
                shutil.rmtree(catalog_path, ignore_errors=True)

        raise ValueError('failed to get the item')


class Item:
    def __init__(self, base_url, session, item_external_id, version, title):
        self.base_url = base_url
        self.schema_version = SCHEMA_VERSION
        self.item_external_id = item_external_id
        self.version = version
        self.title = title
        self.session = session

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
        r = self.session.get(item_package_zip_url)
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

    def subitems(self):
        c = self.db.cursor()
        try:
            return [Subitem(id=row[0], uri=row[1]) for row in c.execute('''SELECT _id, uri FROM subitem ORDER BY position''')]
        finally:
            c.close()

    def related_audio_items(self, subitem_id):
        c = self.db.cursor()
        try:
            return [RelatedAudioItem(
                id=row[0],
                subitem_id=row[1],
                media_url=row[2]) for row in
                    c.execute('''SELECT _id, subitem_id, media_url FROM related_audio_item WHERE subitem_id=?''', [subitem_id])]
        finally:
            c.close()

    def related_video_items(self, subitem_id):
        c = self.db.cursor()
        try:
            return [RelatedVideoItem(
                id=row[0],
                subitem_id=row[1],
                media_url=row[2],
                container_type=row[3]) for row in
                    c.execute('''SELECT _id, subitem_id, media_url, container_type FROM related_video_item WHERE subitem_id=?''', [subitem_id])]
        finally:
            c.close()


class Subitem:
    def __init__(self, id, uri):
        self.id = id
        self.uri = uri

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return not self.__eq__(other)
        return NotImplemented

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))

    def __repr__(self):
        return 'Subitem(id="{id}", uri="{uri}")'.format(
            id=self.id,
            uri=self.uri)


class RelatedAudioItem:
    def __init__(self, id, subitem_id, media_url):
        self.id = id
        self.subitem_id = subitem_id
        self.media_url = media_url

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return not self.__eq__(other)
        return NotImplemented

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))

    def __repr__(self):
        return 'RelatedAudioItem(id="{id}", subitem_id="{subitem_id}", media_url="{media_url}")'.format(
            id=self.id,
            subitem_id=self.subitem_id,
            media_url=self.media_url)


class RelatedVideoItem:
    def __init__(self, id, subitem_id, media_url, container_type):
        self.id = id
        self.subitem_id = subitem_id
        self.media_url = media_url
        self.container_type = container_type

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return not self.__eq__(other)
        return NotImplemented

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))

    def __repr__(self):
        return 'RelatedVideoItem(id="{id}", subitem_id="{subitem_id}", media_url="{media_url}", container_type="{container_type}")'.format(
            id=self.id,
            subitem_id=self.subitem_id,
            media_url=self.media_url,
            container_type=self.container_type)
