from nose.tools import *
from dropbox import client, rest, auth



config = auth.Authenticator.load_config("config/trusted_testing.ini")
dba = auth.Authenticator(config)
access_token = dba.obtain_trusted_access_token(config['testing_user'], config['testing_password'])
db_client = client.DropboxClient(config['server'], config['content_server'], 80, dba, access_token)

CALLBACK_URL = 'http://printer.example.com/request_token_ready'
RESOURCE_URL = 'http://' + config['server'] + '/0/oauth/echo'


def test_delete():
    db_client.file_delete("dropbox", "/tohere")
    return db_client

def test_put_file():
    f = open("tests/dropbox_tests/client_tests.py")
    resp = db_client.put_file("dropbox", "/", f)
    assert resp
    assert_equal(resp.status, 200)

    return db_client

def test_get_file():
    db_client = test_put_file()
    resp = db_client.get_file("dropbox", "/client_tests.py")
    assert_equal(resp.status, 200)
    assert len(resp.read()) > 100

def test_account_info():
    db_client = test_delete()
    resp = db_client.account_info()
    assert resp

    assert_equal(resp.status, 200)
    assert resp.data.keys()


def test_fileops():
    db_client = test_delete()
    test_put_file()

    resp = db_client.file_create_folder("dropbox", "/tohere")
    assert_equal(resp.status, 200)
    assert u'hash' in resp.data.keys()

    resp = db_client.file_copy("dropbox", "/client_tests.py", "/tohere/client_tests.py")
    print resp.headers
    assert_equal(resp.status, 200)
    assert u'bytes' in resp.data.keys()

    resp = db_client.file_move("dropbox", "/tohere/client_tests.py",
                                  "/tohere/client_tests.py.temp")
    assert_equal(resp.status, 200)

    resp = db_client.file_delete("dropbox", "/tohere/client_tests.py.temp")
    assert_equal(resp.status, 200)
    assert_equal(resp.body, "OK")
    assert not resp.data


def test_metadata():
    db_client = test_delete()
    resp = db_client.metadata("dropbox", "/tohere")
    assert resp
    assert_equal(resp.status, 200)
    assert u'bytes' in resp.data.keys()


def test_links():
    db_client = test_put_file()
    url = db_client.links("dropbox", "/client_tests.py")
    assert_equal(url, "http://" + config['server'] + "/0/links/dropbox/client_tests.py")


def test_account():
    """
    This is an example of how you might test the account system, but don't do
    this in real life because it'll polute dropbox with thousands of useless
    accounts.  We track who's doing this and will block you if we think you're
    abusing it.

    import time
    from mechanize import Browser, FormNotFoundError

    user_id = str(int(time.time()))
    resp = db_client.account('zed' + user_id + '@tester.com', 'testing', 'Zed', 'Shaw')
    assert_equal(resp.status, 200) 

    resp = db_client.account('zed' + user_id + '@tester.com', 'testing', 'Zed', 'Shaw')
    assert_equal(resp.status, 400) 

    config = auth.Authenticator.load_config("config/trusted_testing.ini")
    dba = auth.Authenticator(config)
    access_token = dba.obtain_trusted_access_token('zed' + user_id + '@tester.com', 'testing')
    cl = client.DropboxClient(config['server'], config['content_server'], 80, dba, access_token)
    resp = cl.account_info()
    assert_equal(resp.data['display_name'], 'Zed Shaw')

    br = Browser()
    br.set_debug_redirects(True)
    br.open('https://dropbox.com/')
    print "FIRST PAGE", br.title(), br.geturl()
    br.select_form(nr=1)
    br['login_email'] = config['testing_user']
    br['login_password'] = config['testing_password']

    resp = br.submit()
    print "RESULT PAGE TITLE", br.title()
    print "RESULT URL", resp.geturl()

    assert br.viewing_html(), "Looks like it busted."
    assert_equal(resp.geturl(), "https://dropbox.com/home")

    """
