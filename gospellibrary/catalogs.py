from io import BytesIO
import requests
import os
import sqlite3

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

try:
    import lzma
except ImportError:
    from backports import lzma

DEFAULT_ISO639_3_CODE = 'eng'
DEFAULT_SCHEMA_VERSION = 'v4'
DEFAULT_BASE_URL = 'https://edge.ldscdn.org/mobile/GospelStudy/production/'
DEFAULT_CACHE_PATH = '/tmp/python-gospel-library'


def get_languages(schema_version=DEFAULT_SCHEMA_VERSION, base_url=DEFAULT_BASE_URL, session=requests.Session()):
    languages_url = urljoin(base_url, '{schema_version}/languages/languages.json'.format(schema_version=schema_version))
    r = session.get(languages_url)
    if r.status_code == 200:
        return r.json()


def current_catalog_version(iso639_3_code=DEFAULT_ISO639_3_CODE, schema_version=DEFAULT_SCHEMA_VERSION, base_url=DEFAULT_BASE_URL, session=requests.Session()):
    index_url = urljoin(base_url, '{schema_version}/languages/{iso639_3_code}/index.json'.format(schema_version=schema_version, iso639_3_code=iso639_3_code))
    r = session.get(index_url)
    if r.status_code == 200:
        return r.json().get('catalogVersion', None)


class CatalogDB:
    def __init__(self, iso639_3_code=DEFAULT_ISO639_3_CODE, catalog_version=None, schema_version=DEFAULT_SCHEMA_VERSION, base_url=DEFAULT_BASE_URL, session=requests.Session(), cache_path=DEFAULT_CACHE_PATH):
        self.iso639_3_code = iso639_3_code
        self.catalog_version = catalog_version if catalog_version else current_catalog_version(iso639_3_code=iso639_3_code, schema_version=schema_version, base_url=base_url, session=session)
        self.schema_version = schema_version
        self.base_url = base_url
        self.session = session
        self.cache_path = cache_path

    def exists(self):
        return self.__fetch_catalog() is not None

    def __fetch_catalog(self):
        catalog_path = os.path.join(self.cache_path, self.schema_version, 'languages', self.iso639_3_code, 'catalogs', str(self.catalog_version), 'Catalog.sqlite')
        if not os.path.isfile(catalog_path):
            catalog_xz_url = urljoin(self.base_url, '{schema_version}/languages/{iso639_3_code}/catalogs/{catalog_version}.xz'.format(schema_version=self.schema_version, iso639_3_code=self.iso639_3_code, catalog_version=self.catalog_version))
            r = self.session.get(catalog_xz_url)
            if r.status_code == 200:
                try:
                    os.makedirs(os.path.dirname(catalog_path))
                except OSError:
                    pass

                with lzma.open(BytesIO(r.content)) as catalog_xz_file:
                    with open(catalog_path, 'wb') as f:
                        f.write(catalog_xz_file.read())

        if os.path.isfile(catalog_path):
            return catalog_path

        return None

    def dict_factory(self, cursor, row):
        obj = {}
        for i, column in enumerate(cursor.description):
            name = column[0]
            value = row[i]
            if name not in obj:
                if name in ['version', 'latest_version'] and value is not None:
                    obj['version'] = value
                if name in ['cover_renditions', 'item_cover_renditions'] and value is not None:
                    base_url = urljoin(self.base_url, self.schema_version)

                    renditions = []
                    for rendition in value.splitlines():
                        size, url = rendition.split(',', 1)
                        width, height = size.split('x', 1)
                        renditions.append(dict(
                            width=width,
                            height=height,
                            url=urljoin(base_url, url),
                        ))
                    obj[name] = renditions
                    obj['raw_' + name] = value
                else:
                    obj[name] = value
        return obj

    def language_name(self, language_id):
        catalog_path = self.__fetch_catalog()
        if not catalog_path:
            return None

        with sqlite3.connect(catalog_path) as db:
            db.row_factory = self.dict_factory
            c = db.cursor()
            try:
                c.execute('''SELECT name FROM language_name WHERE language_id=?''', [language_id])
                row = c.fetchone()
                return row['name'] if row else None
            finally:
                c.close()

    def item_categories(self):
        catalog_path = self.__fetch_catalog()
        if not catalog_path:
            return None

        with sqlite3.connect(catalog_path) as db:
            db.row_factory = self.dict_factory
            c = db.cursor()
            try:
                c.execute('''SELECT * FROM item_category''')
                return c.fetchall()
            finally:
                c.close()

    def collection(self, collection_id):
        catalog_path = self.__fetch_catalog()
        if not catalog_path:
            return None

        with sqlite3.connect(catalog_path) as db:
            db.row_factory = self.dict_factory
            c = db.cursor()
            try:
                c.execute('''SELECT * FROM library_collection WHERE id=?''', [collection_id])
                return c.fetchone()
            finally:
                c.close()

    def sections(self, collection_id):
        catalog_path = self.__fetch_catalog()
        if not catalog_path:
            return None

        with sqlite3.connect(catalog_path) as db:
            db.row_factory = self.dict_factory
            c = db.cursor()
            try:
                c.execute('''SELECT * FROM library_section WHERE library_collection_id=? ORDER BY position''', [collection_id])
                return c.fetchall()
            finally:
                c.close()

    def collections(self, section_ids):
        catalog_path = self.__fetch_catalog()
        if not catalog_path:
            return None

        with sqlite3.connect(catalog_path) as db:
            db.row_factory = self.dict_factory
            c = db.cursor()
            try:
                c.execute('''SELECT * FROM library_collection WHERE library_section_id IN ({}) ORDER BY position'''.format(
                    ','.join('?' * len(section_ids))
                ), section_ids)
                return c.fetchall()
            finally:
                c.close()

    def items(self, section_ids=None):
        catalog_path = self.__fetch_catalog()
        if not catalog_path:
            return None

        with sqlite3.connect(catalog_path) as db:
            db.row_factory = self.dict_factory
            c = db.cursor()
            try:
                if section_ids is not None:
                    c.execute('''SELECT item.*, library_item.* FROM library_item INNER JOIN item ON library_item.item_id=item.id WHERE library_section_id IN ({}) ORDER BY position'''.format(
                        ','.join('?' * len(section_ids))
                    ), section_ids)
                else:
                    c.execute('''SELECT item.*, library_item.* FROM library_item INNER JOIN item ON library_item.item_id=item.id ORDER BY external_id''')
                return c.fetchall()
            finally:
                c.close()

    def nodes(self, section_ids):
        return sorted(self.collections(section_ids) + self.items(section_ids), key=lambda node: node['position'])

    def item(self, item_id=None, uri=None):
        catalog_path = self.__fetch_catalog()
        if not catalog_path:
            return None

        with sqlite3.connect(catalog_path) as db:
            db.row_factory = self.dict_factory
            c = db.cursor()
            try:
                if item_id:
                    c.execute('''SELECT * FROM item WHERE id=?''', [item_id])
                else:
                    c.execute('''SELECT * FROM item WHERE uri=?''', [uri])
                return c.fetchone()
            finally:
                c.close()
