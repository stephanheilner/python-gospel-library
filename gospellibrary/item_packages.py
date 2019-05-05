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


class ItemPackage:
    def __init__(self, item_id, item_version, iso639_3_code=DEFAULT_ISO639_3_CODE, schema_version=DEFAULT_SCHEMA_VERSION, base_url=DEFAULT_BASE_URL, session=requests.Session(), cache_path=DEFAULT_CACHE_PATH):
        self.item_id = item_id
        self.item_version = item_version
        self.iso639_3_code = iso639_3_code
        self.schema_version = schema_version
        self.base_url = base_url
        self.session = session
        self.cache_path = cache_path

    def exists(self):
        return self.__fetch_item_package() is not None

    def __fetch_item_package(self):
        item_package_path = os.path.join(self.cache_path, self.schema_version, 'languages', self.iso639_3_code, 'item_packages', self.item_id, str(self.item_version), 'Package.sqlite')
        if not os.path.isfile(item_package_path):
            item_package_xz_url = urljoin(self.base_url, '{schema_version}/languages/{iso639_3_code}/item-packages/{item_id}/{item_version}.xz'.format(schema_version=self.schema_version, iso639_3_code=self.iso639_3_code, item_id=self.item_id, item_version=self.item_version))
            r = self.session.get(item_package_xz_url)
            if r.status_code == 200:
                try:
                    os.makedirs(os.path.dirname(item_package_path))
                except OSError:
                    pass

                with lzma.open(BytesIO(r.content)) as item_package_xz_url:
                    with open(item_package_path, 'wb') as f:
                        f.write(item_package_xz_url.read())

        if os.path.isfile(item_package_path):
            return item_package_path

        return None

    def dict_factory(self, cursor, row):
        obj = {}
        for i, column in enumerate(cursor.description):
            name = column[0]
            value = row[i]
            if name not in obj:
                obj[name] = value
        return obj

    def file_id(self):
        item_package_path = self.__fetch_item_package()
        if not item_package_path:
            return None

        with sqlite3.connect(item_package_path) as db:
            c = db.cursor()
            try:
                c.execute('''SELECT value FROM metadata WHERE key='file_id' LIMIT 1''')
                row = c.fetchone()
                return row[0] if row else None
            finally:
                c.close()

    def html(self, subitem_uri=None, paragraph_id=None):
        item_package_path = self.__fetch_item_package()
        if not item_package_path:
            return None

        with sqlite3.connect(item_package_path) as db:
            original_text_factory = db.text_factory
            db.text_factory = bytes
            c = db.cursor()
            try:
                if paragraph_id:
                    c.execute('''SELECT content_html, start_index, end_index FROM paragraph_metadata
                                     INNER JOIN subitem_content ON paragraph_metadata.subitem_id=subitem_content.subitem_id
                                     INNER JOIN subitem ON subitem_content.subitem_id=subitem.id
                                 WHERE uri=? AND paragraph_id=?''', [subitem_uri, paragraph_id])
                    (html, start_index, end_index) = c.fetchone()

                    return html[start_index:end_index].decode('utf-8')
                else:
                    c.execute('''SELECT content_html FROM subitem_content
                                     INNER JOIN subitem ON subitem_content.subitem_id=subitem.id
                                 WHERE uri=?''', [subitem_uri])
                    (html,) = c.fetchone()

                    return html[:].decode('utf-8')
            finally:
                c.close()
                db.text_factory = original_text_factory

    def subitems(self):
        item_package_path = self.__fetch_item_package()
        if not item_package_path:
            return None

        with sqlite3.connect(item_package_path) as db:
            db.row_factory = self.dict_factory
            c = db.cursor()
            try:
                c.execute('''SELECT * FROM subitem ORDER BY position''')
                return c.fetchall()
            finally:
                c.close()

    def subitem(self, uri):
        item_package_path = self.__fetch_item_package()
        if not item_package_path:
            return None

        with sqlite3.connect(item_package_path) as db:
            db.row_factory = self.dict_factory
            c = db.cursor()
            try:
                c.execute('''SELECT * FROM subitem WHERE uri=?''', [uri])
                return c.fetchone()
            finally:
                c.close()

    def subitem_html(self, subitem_id):
        item_package_path = self.__fetch_item_package()
        if not item_package_path:
            return None

        with sqlite3.connect(item_package_path) as db:
            c = db.cursor()
            try:
                c.execute('''SELECT content_html FROM subitem_content WHERE subitem_id=? LIMIT 1''', [subitem_id])
                row = c.fetchone()
                return row[0]
            finally:
                c.close()

    def path(self):
        return os.path.dirname(self.__fetch_item_package())

    def related_audio_items(self, subitem_id):
        item_package_path = self.__fetch_item_package()
        if not item_package_path:
            return None

        with sqlite3.connect(item_package_path) as db:
            db.row_factory = self.dict_factory
            c = db.cursor()
            try:
                c.execute('''SELECT * FROM related_audio_item WHERE subitem_id=?''', [subitem_id])
                return c.fetchall()
            finally:
                c.close()

    def related_video_items(self, subitem_id):
        item_package_path = self.__fetch_item_package()
        if not item_package_path:
            return None

        with sqlite3.connect(item_package_path) as db:
            db.row_factory = self.dict_factory
            c = db.cursor()
            try:
                c.execute('''SELECT * FROM related_video_item WHERE subitem_id=?''', [subitem_id])
                return c.fetchall()
            finally:
                c.close()

    def table_exists(self, db, table_name):
        c = db.cursor()
        try:
            c.execute('''SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?''', [table_name])
            return c.fetchone()[0] == 1
        finally:
            c.close()

        return False

    def related_content_items(self, subitem_id):
        item_package_path = self.__fetch_item_package()
        if not item_package_path:
            return None

        with sqlite3.connect(item_package_path) as db:
            db.row_factory = self.dict_factory
            c = db.cursor()
            try:
                c.execute('''SELECT * FROM related_content_item WHERE subitem_id=?''', [subitem_id])
                return c.fetchall()
            finally:
                c.close()
