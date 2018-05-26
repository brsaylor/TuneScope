import sqlite3
import json


class FileHistory(object):
    """ Creates and manages a SQLite database with information about files that
    TuneScope has opened before. Each record (returned as a dict by `get` and
    `recent`) has the following fields:

    directory : str
        absolute path of the directory containing the file, excluding the
        trailing slash (unless it is the root directory)
    filename : str
        base name of the file
    last_opened : datetime
    title : str
    artist : str
    album : str
    state : dict
        any state to be restored when the file is opened again

    Records are uniquely identified by (directory, filename).

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
                directory TEXT,
                filename TEXT,
                last_opened TIMESTAMP,
                title TEXT,
                artist TEXT,
                album TEXT,
                state TEXT,
                PRIMARY KEY (directory, filename)
            )
            ''')

    def update(self,
               directory=None,
               filename=None,
               last_opened=None,
               title=None,
               artist=None,
               album=None,
               state={}):
        """ Insert or replace a record identified by (directory, filename) """
        state = json.dumps(state)
        c = self._db.cursor()
        c.execute('''
            INSERT OR REPLACE INTO file_history (
                directory,
                filename,
                last_opened,
                title,
                artist,
                album,
                state)
            VALUES (?,?,?,?,?,?,?)
            ''', (directory, filename, last_opened, title, artist, album, state))
        self._db.commit()

    def get(self, directory, filename):
        """ Retrieve a record by (directory, filename), returning None for
        non-existent records. """
        c = self._db.cursor()
        c.execute(
            'SELECT * FROM file_history WHERE directory = ? AND filename = ?',
            (directory, filename))
        record = c.fetchone()
        if record is None:
            return None

        record = dict(record)
        record['state'] = json.loads(record['state'])
        return record

    def find_by_filename(self, filename, limit):
        """ Return the `limit` most recent records with the given `filename`,
        excluding the state dictionary """
        c = self._db.cursor()
        c.execute('''
            SELECT directory, filename, last_opened, title, artist, album
            FROM file_history
            WHERE filename = ?
            ORDER BY last_opened DESC
            LIMIT ?
            ''', (filename, limit))
        records = c.fetchall()
        return [dict(record) for record in records]

    def recent(self, limit):
        """ Returns the `limit` most recent records based on `last_opened`
        time stamp. Excludes state dictionary. """
        c = self._db.cursor()
        c.execute('''
            SELECT directory, filename, last_opened, title, artist, album
            FROM file_history
            ORDER BY last_opened DESC
            LIMIT ?
            ''', (limit,))
        records = c.fetchall()
        return [dict(record) for record in records]

    def delete(self, directory, filename):
        """ Delete the record with the given directory and filename """
        c = self._db.cursor()
        c.execute('DELETE FROM file_history WHERE directory = ? AND filename = ?',
                  (directory, filename))

    def __del__(self):
        if self._db is not None:
            self._db.close()
