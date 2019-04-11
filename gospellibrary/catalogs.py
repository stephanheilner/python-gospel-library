import requests
import os
import lzma
import sqlite3

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

try:
    from StringIO import StringIO
    Bytes = StringIO
except ImportError:
    from io import BytesIO
    Bytes = BytesIO

DEFAULT_BASE_URL = 'https://edge.ldscdn.org/mobile/GospelStudy/production/'
DEFAULT_SCHEMA_VERSION = 'v4'
DEFAULT_CACHE_PATH = '/tmp/python-gospel-library'
DEFAULT_ISO639_3_CODE = 'eng'

def current_catalog_version(iso639_3_code=None, schema_version=None, base_url=None, session=None):
    if not iso639_3_code:
        iso639_3_code = DEFAULT_ISO639_3_CODE
    if not schema_version:
        schema_version = DEFAULT_SCHEMA_VERSION
    if not base_url:
        base_url = DEFAULT_BASE_URL
    if not session:
        session = requests.Session()

    index_url = '{base_url}/{schema_version}/languages/{iso639_3_code}/index.json'.format(base_url=base_url, schema_version=schema_version)
    r = session.get(index_url)
    if r.status_code == 200:
        return r.json().get('catalogVersion', None)


class CatalogDB:
    def __init__(self, iso639_3_code=None, catalog_version=None, schema_version=None, base_url=None, session=None, cache_path=None):
        self.iso639_3_code = iso639_3_code if iso639_3_code else DEFAULT_ISO639_3_CODE
        self.catalog_version = catalog_version if catalog_version else current_catalog_version(iso639_3_code=iso639_3_code, schema_version=schema_version, base_url=base_url, session=session)
        self.schema_version = schema_version if schema_version else DEFAULT_SCHEMA_VERSION
        self.base_url = base_url if base_url else DEFAULT_BASE_URL
        self.session = session if session else requests.Session()
        self.cache_path = cache_path if cache_path else DEFAULT_CACHE_PATH

    def exists(self):
        return self.__fetch_catalog() is not None

    def __fetch_catalog(self):
        catalog_path = os.path.join(self.cache_path, '{schema_version}/languages/{iso639_3_code}/catalogs/{catalog_version}'.format(schema_version=self.schema_version, catalog_version=self.catalog_version), 'Catalog.sqlite')
        if not os.path.isfile(catalog_path):
            catalog_xz_url = '{base_url}/{schema_version}/languages/{iso639_3_code}/catalogs/{catalog_version}.xz'.format(base_url=self.base_url, schema_version=self.schema_version, catalog_version=self.catalog_version)
            r = self.session.get(catalog_xz_url)
            if r.status_code == 200:
                try:
                    os.makedirs(os.path.dirname(catalog_path))
                except OSError:
                    pass

                with lzma.open(r.content) as catalog_xz_file:
                    #TODO: save decompressed file to os.path.dirname(catalog_path)
                    # catalog_xz_file.extractall(os.path.dirname(catalog_path))

        if os.path.isfile(catalog_path):
            return catalog_path

        return None

    def dict_factory(self, cursor, row):
        obj = {}
        for i, column in enumerate(cursor.description):
            name = column[0] if column[0] != '_id' else 'id'
            value = row[i]
            if name not in obj:
                if name in ['version', 'latest_version'] and value is not None:
                    obj['version'] = value
                if name in ['cover_renditions', 'item_cover_renditions'] and value is not None:
                    base_url = '{base_url}/{schema_version}/'.format(base_url=self.base_url, schema_version=self.schema_version)

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

    def languages(self):
        catalog_path = self.__fetch_catalog()
        if not catalog_path:
            return None

        with sqlite3.connect(catalog_path) as db:
            db.row_factory = self.dict_factory
            c = db.cursor()
            try:
                c.execute('''SELECT language.*, language_name.* FROM language LEFT OUTER JOIN (SELECT * FROM language_name WHERE localization_language_id=1) language_name ON language._id=language_name.language_id ORDER BY lds_language_code''')
                return c.fetchall()
            finally:
                c.close()

    def language_name(self, language_id, localization_language_id):
        catalog_path = self.__fetch_catalog()
        if not catalog_path:
            return None

        with sqlite3.connect(catalog_path) as db:
            db.row_factory = self.dict_factory
            c = db.cursor()
            try:
                c.execute('''SELECT name FROM language_name WHERE language_id=? AND localization_language_id=?''', [language_id, localization_language_id])
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
                c.execute('''SELECT * FROM library_collection WHERE _id=?''', [collection_id])
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
                    c.execute('''SELECT item.*, library_item.* FROM library_item INNER JOIN item ON library_item.item_id=item._id WHERE library_section_id IN ({}) ORDER BY position'''.format(
                        ','.join('?' * len(section_ids))
                    ), section_ids)
                else:
                    c.execute('''SELECT item.*, library_item.* FROM library_item INNER JOIN item ON library_item.item_id=item._id ORDER BY external_id''')
                return c.fetchall()
            finally:
                c.close()

    def nodes(self, section_ids):
        return sorted(self.collections(section_ids) + self.items(section_ids), key=lambda node: node['position'])

    def item(self, item_id=None, uri=None, lang=None):
        catalog_path = self.__fetch_catalog()
        if not catalog_path:
            return None

        with sqlite3.connect(catalog_path) as db:
            db.row_factory = self.dict_factory
            c = db.cursor()
            try:
                if item_id:
                    c.execute('''SELECT * FROM item WHERE _id=?''', [item_id])
                else:
                    c.execute('''SELECT item.* FROM item INNER JOIN language ON item.language_id=language._id WHERE uri=? AND iso639_3=?''', [uri, lang])
                return c.fetchone()
            finally:
                c.close()
