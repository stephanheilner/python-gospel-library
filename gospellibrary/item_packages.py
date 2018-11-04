import requests
import os
from zipfile import ZipFile
import sqlite3

try:
    from StringIO import StringIO
    Bytes = StringIO
except ImportError:
    from io import BytesIO
    Bytes = BytesIO

DEFAULT_BASE_URL = 'https://edge.ldscdn.org/mobile/GospelStudy/production/'
DEFAULT_SCHEMA_VERSION = 'v3'
DEFAULT_CACHE_PATH = '/tmp/python-gospel-library'


class ItemPackage:
    def __init__(self, item_external_id, item_version, schema_version=None, base_url=None, session=None, cache_path=None):
        self.item_external_id = item_external_id
        self.item_version = item_version
        self.schema_version = schema_version if schema_version else DEFAULT_SCHEMA_VERSION
        self.base_url = base_url if base_url else DEFAULT_BASE_URL
        self.session = session if session else requests.Session()
        self.cache_path = cache_path if cache_path else DEFAULT_CACHE_PATH

    def exists(self):
        return self.__fetch_item_package() is not None

    def __fetch_item_package(self):
        item_package_path = os.path.join(self.cache_path,
                                         '{schema_version}/item_packages/{item_external_id}/{item_version}'.format(
                                             schema_version=self.schema_version, item_external_id=self.item_external_id,
                                             item_version=self.item_version), 'package.sqlite')
        if not os.path.isfile(item_package_path):
            item_package_zip_url = '{base_url}/{schema_version}/item-packages/{item_external_id}/{item_version}.zip'.format(
                base_url=self.base_url, schema_version=self.schema_version, item_external_id=self.item_external_id,
                item_version=self.item_version)
            r = self.session.get(item_package_zip_url)
            if r.status_code == 200:
                try:
                    os.makedirs(os.path.dirname(item_package_path))
                except OSError:
                    pass

                with ZipFile(Bytes(r.content), 'r') as item_package_zip_file:
                    item_package_zip_file.extractall(os.path.dirname(item_package_path))

        if os.path.isfile(item_package_path):
            return item_package_path

        return None

    def dict_factory(self, cursor, row):
        obj = {}
        for i, column in enumerate(cursor.description):
            name = column[0] if column[0] != '_id' else 'id'
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

    def html(self, uri=None, subitem_uri=None, paragraph_id=None):
        item_package_path = self.__fetch_item_package()
        if not item_package_path:
            return None

        with sqlite3.connect(item_package_path) as db:
            c = db.cursor()
            try:
                c.execute('''SELECT content_html, start_index, end_index FROM paragraph_metadata
                                 INNER JOIN subitem_content ON paragraph_metadata.subitem_id=subitem_content.subitem_id
                                 INNER JOIN subitem ON subitem_content.subitem_id=subitem._id
                             WHERE uri=? AND paragraph_id=?''', [subitem_uri, paragraph_id])
                (html, start_index, end_index) = c.fetchone()

                return html[start_index:end_index].decode('utf-8')
            finally:
                c.close()

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
