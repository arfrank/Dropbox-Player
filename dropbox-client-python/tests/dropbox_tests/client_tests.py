from nose.tools import *
from dropbox import client, rest, auth
from helpers import login_and_authorize
import os
import simplejson as json



config = auth.Authenticator.load_config("config/testing.ini")
dba = auth.Authenticator(config)
print "CONFIG", config

token = dba.obtain_request_token()
login_and_authorize(dba.build_authorize_url(token), config)
access_token = dba.obtain_access_token(token, config['verifier'])
db_client = client.DropboxClient(config['server'], config['content_server'], 80, dba, access_token)

CALLBACK_URL = 'http://printer.example.com/request_token_ready'
RESOURCE_URL = 'http://' + config['server'] + '/0/oauth/echo'


def test_delete():
    db_client.file_delete("sandbox", "/tohere")
    return db_client

def test_put_file():
    for target in ["tests/file with spaces.txt",
                   "tests/dropbox_tests/client_tests.py", ]:
        f = open(target)
        resp = db_client.put_file("sandbox", "/", f)
        print "BODY: ", resp.body
        assert resp
        assert_equal(resp.status, 200)

    return db_client


def test_get_file():
    db_client = test_put_file()
    for target in ["/client_tests.py", "/file with spaces.txt", ]:
        resp = db_client.get_file("sandbox", target)
        body = resp.read()
        print "BODY: ", body
        assert_equal(resp.status, 200)
        assert len(body) > 0


def test_event_metadata():
    if os.path.exists("tests/sfj_data.json"):
        db_client = test_delete()
        events = json.load(open("tests/sfj_data.json"))
        uid = events.keys()[0]
        nsid = events[uid].keys()[0]
        sjid = str(events[uid][nsid][0])

        # include invalid data: bad uid
        events["1000"] = events[uid]
        # bad nsid
        events[uid]["1000"] = events[uid][nsid]
        # bad sjids
        events[uid][nsid].append("1000")

        for user_id, ns_and_jids in events.items():
            resp = db_client.event_metadata("sandbox", user_id, events[user_id])
            assert_equal(resp.status, 200)
            assert user_id in resp.data

            print "EVENT", resp.data

            if uid in resp.data:
                assert uid in resp.data, resp.data
                assert nsid in resp.data[uid], resp.data
                assert sjid in resp.data[uid][nsid].keys()
                md = resp.data[uid][nsid][sjid].keys()
                assert "path" in md or "error" in md

                print "AVAILABLE", db_client.event_content_is_available(resp.data[uid][nsid][sjid])

   
def test_event_content():
    if os.path.exists("tests/sfj_data.json"):
        events = json.load(open("tests/sfj_data.json"))
        uid = events.keys()[0]
        nsid = events[uid].keys()[0]
        sjid_list = events[uid][nsid]

        db_client = test_delete()
        for sjid in sjid_list:
            resp = db_client.event_content("sandbox", uid, nsid, sjid)
            body = resp.read()

            assert resp.status == 200 or resp.status == 404, "Status was: %d" % resp.status

            if 'x-dropbox-metadata' in resp.headers:
                assert_equal(resp.headers['x-dropbox-metadata'].keys(), ['path', 'is_dir', 'mtime', 'latest', 'size'])

        # file does not exist
        resp = db_client.event_content("sandbox", uid, nsid, sjid+1000)
        assert_equal(resp.status, 404)

        # namespace does not exist
        resp = db_client.event_content("sandbox", uid, int(nsid)+1000, sjid)
        assert_equal(resp.status, 404)

        # uid does not exist
        resp = db_client.event_content("sandbox", int(uid)+1000, nsid, sjid)
        assert_equal(resp.status, 404)


def test_account_info():
    db_client = test_delete()
    resp = db_client.account_info()
    assert resp

    assert_equal(resp.status, 200)
    assert_equal(resp.data.keys(), [u'country', u'display_name', u'uid', u'quota_info'])


def test_fileops():
    db_client = test_delete()
    test_put_file()

    resp = db_client.file_create_folder("sandbox", "/tohere")
    assert_equal(resp.status, 200)
    assert_equal(resp.data.keys(), [u'hash', u'thumb_exists', u'bytes', u'modified', u'path',
                                    u'is_dir', u'size', u'root', u'contents', u'icon'])

    resp = db_client.file_copy("sandbox", "/client_tests.py", "/tohere/client_tests.py")
    print resp.headers
    assert_equal(resp.status, 200)
    assert_equal(resp.data.keys(), [u'thumb_exists', u'bytes', u'modified',
                                    u'path', u'is_dir', u'size', u'root',
                                    u'mime_type', u'icon'])

    resp = db_client.file_move("sandbox", "/tohere/client_tests.py",
                                  "/tohere/client_tests.py.temp")
    assert_equal(resp.status, 200)

    resp = db_client.file_delete("sandbox", "/tohere/client_tests.py.temp")
    assert_equal(resp.status, 200)
    assert_equal(resp.body, "OK")
    assert not resp.data


def test_metadata():
    db_client = test_delete()
    resp = db_client.metadata("sandbox", "/tohere")
    assert resp
    assert_equal(resp.status, 200)
    assert_equal(resp.data.keys(), [u'is_deleted', u'thumb_exists',
                                    u'bytes', u'modified', u'path', u'is_dir',
                                    u'size', u'root', u'hash', u'contents', u'icon'])


def test_links():
    db_client = test_put_file()
    url = db_client.links("sandbox", "/client_tests.py")
    assert_equal(url, "http://" + config['server'] + "/0/links/sandbox/client_tests.py")


def test_thumbnails():
    db_client.file_delete("sandbox", "/sample_photo.jpg")

    f = open("tests/sample_photo.jpg")
    resp = db_client.put_file("sandbox", "/", f)
    assert_equal(resp.status, 200)

    resp = db_client.get_file("sandbox", "/sample_photo.jpg")
    body = resp.read()
    assert_equal(resp.status, 200)
    assert len(body) > 0

    resp = db_client.thumbnail("sandbox", "/sample_photo.jpg", size='large')
    thumb = resp.read()
    assert_equal(resp.status, 200)
    assert len(body) > len(thumb)

