import sqlite3
import json


class FileHistory(object):
    """ Creates and manages sqlite db to keep track of the opened files
    base on the filepath as the primary key. Each record is uniquely
    identified by `file_path` and has a number fields. The state field
    is a dictionary representing any state to be restored when the file
    is opened again.

    Parameters
    ----------
    db_path : str
        file path to store the database.
        (Needs to be expanded for default location on different OS's)
    """
    def __init__(self, db_path):
        self._db = None
        self._db = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        self._db.row_factory = sqlite3.Row
        c = self._db.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS file_history (
                file_path TEXT PRIMARY KEY,
                last_opened TIMESTAMP,
                title TEXT,
                artist TEXT,
                album TEXT,
                state TEXT)
            ''')

    def update(self,
               file_path=None,
               last_opened=None,
               title=None,
               artist=None,
               album=None,
               state=None):
        """ Inserts or replaces a record identified by `file_path`. """
        state = json.dumps(state)
        c = self._db.cursor()
        c.execute('''
            INSERT OR REPLACE INTO file_history (
                file_path,
                last_opened,
                title,
                artist,
                album,
                state)
            VALUES (?,?,?,?,?,?)
            ''', (file_path, last_opened, title, artist, album, state))
        self._db.commit()

    def get(self, file_path):
        """ Retrives a record by `file_path`, returning None for non-exisent records. """
        c = self._db.cursor()
        c.execute('SELECT * FROM file_history WHERE file_path=?', (file_path,))
        record = c.fetchone()
        if record is None:
            return None

        record = dict(record)
        record['state'] = json.loads(record['state'])
        return record

    def recent(self, limit):
        """ Returns the `limit` most recent records based on `last_opened`
        time stamp. Excludes state dictionary. """
        c = self._db.cursor()
        c.execute('''
            SELECT file_path, last_opened, title, artist, album
            FROM file_history
            ORDER BY last_opened DESC
            LIMIT ?
            ''', (limit,))
        records = c.fetchall()
        return [dict(record) for record in records]

    def __del__(self):
        if self._db is not None:
            self._db.close()
