import datetime
import random

import pytest

from tunescope.filehistory import FileHistory


@pytest.fixture
def db_path(tmpdir_factory):
    return str(tmpdir_factory.mktemp('filehistory').join('filehistory.sqlite3'))


def create_test_record(file_path, second, incl_state=True):
    """ Creates a test record for the library with field values generated
    based on `file_path`. The `second` parameter adjusts the `last_opened`
    time stamp. `incl_state` determines whether the state field is populated
    with dummy data or excluded from the record. """
    record = dict(
        file_path=file_path,
        last_opened=datetime.datetime(2017, 11, 11, 11, 11, second),
        title='test title' + file_path,
        artist='test artist' + file_path,
        album='test album' + file_path
    )
    if incl_state:
        record['state'] = {'stuff': file_path}
    return record


def test_update_get(db_path):
    file_path = '/tune.mp3'
    filehistory = FileHistory(db_path)
    record = create_test_record(file_path, 1)
    filehistory.update(**record)
    del filehistory
    filehistory = FileHistory(db_path)
    record2 = filehistory.get(file_path)
    assert record == record2


def test_recent(db_path):
    records = [create_test_record('/path{}'.format(i), i, incl_state=False)
               for i in range(10)]
    random.shuffle(records)
    filehistory = FileHistory(db_path)
    for record in records:
        filehistory.update(**record)

    assert filehistory.recent(5) == sorted(
        records, reverse=True, key=lambda x: x['last_opened'])[:5]


def test_empty_recent(db_path):
    filehistory = FileHistory(db_path)
    records = filehistory.recent(5)
    assert records == []


def test_nonexistent_record(db_path):
    filehistory = FileHistory(db_path)
    record = filehistory.get('/nonsense')
    assert record is None


def test_update_existing_record(db_path):
    filehistory = FileHistory(db_path)
    record1 = create_test_record('/tune1', 1)
    record2 = create_test_record('/tune2', 2)
    filehistory.update(**record1)
    filehistory.update(**record2)
    record1['last_opened'] = datetime.datetime.now()
    filehistory.update(**record1)
    record1_out = filehistory.get('/tune1')
    record2_out = filehistory.get('/tune2')
    assert record1_out == record1
    assert record2_out == record2
