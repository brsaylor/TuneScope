import datetime
import os.path
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
    directory, filename = os.path.split(file_path)
    record = dict(
        directory=directory,
        filename=filename,
        last_opened=datetime.datetime(2017, 11, 11, 11, 11, second),
        title='test title' + file_path,
        artist='test artist' + file_path,
        album='test album' + file_path
    )
    if incl_state:
        record['state'] = {'stuff': file_path}
    return record


def test_update_get(db_path):
    file_path = '/music/tune.mp3'
    filehistory = FileHistory(db_path)
    record = create_test_record(file_path, 1)
    filehistory.update(**record)
    del filehistory
    filehistory = FileHistory(db_path)
    record2 = filehistory.get(*os.path.split(file_path))
    assert record == record2


def test_recent(db_path):
    records = [create_test_record('/music/tune{}'.format(i), i, incl_state=False)
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
    record = filehistory.get('/', 'nonsense')
    assert record is None


def test_update_existing_record(db_path):
    filehistory = FileHistory(db_path)
    record1 = create_test_record('/music/tune1', 1)
    record2 = create_test_record('/music/tune2', 2)
    filehistory.update(**record1)
    filehistory.update(**record2)
    record1['last_opened'] = datetime.datetime.now()
    filehistory.update(**record1)
    record1_out = filehistory.get('/music', 'tune1')
    record2_out = filehistory.get('/music', 'tune2')
    assert record1_out == record1
    assert record2_out == record2


def test_find_by_filename(db_path):
    filehistory = FileHistory(db_path)
    records = [
        create_test_record('/dir1/file1', 1),
        create_test_record('/dir2/file1', 2),
        create_test_record('/dir3/file2', 3),
        create_test_record('/dir4/file2', 4),
    ]
    for record in records:
        filehistory.update(**record)

    records_out = filehistory.find_by_filename('nonsense', 3)
    assert records_out == []

    expected_records_out = [records[1], records[0]]
    del expected_records_out[0]['state']
    del expected_records_out[1]['state']

    records_out = filehistory.find_by_filename('file1', 1)
    assert records_out == expected_records_out[:1]

    records_out = filehistory.find_by_filename('file1', 3)
    assert records_out == expected_records_out


def test_delete(db_path):
    filehistory = FileHistory(db_path)
    record1 = create_test_record('/dir/file1', 1)
    record2 = create_test_record('/dir/file2', 2)
    filehistory.update(**record1)
    filehistory.update(**record2)
    filehistory.delete('/dir', 'file1')
    del record2['state']
    assert filehistory.recent(10) == [record2]
