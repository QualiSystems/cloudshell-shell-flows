import unittest

from cloudshell.shell.flows.utils import networking_utils


class TestUrlParser(unittest.TestCase):
    def setUp(self):
        self.url_data = {
            "scheme": "https",
            "fragment": "",
            "hostname": "test.host.com",
            "netloc": "cisco:securePassword!1@test.host.com:22",
            "port": 22,
            "query": "arg=val",
            "username": "cisco",
            "password": "securePassword!1",
            "path": "/some_path",
            "filename": "test_file_name.ext",
        }
        self.url = (
            "https://cisco:securePassword!1@test.host.com:22"
            "/some_path/test_file_name.ext?arg=val"
        )

    def test_parse_url(self):
        # act
        result = networking_utils.UrlParser.parse_url(url=self.url)
        # verify
        self.assertEqual(result, self.url_data)

    def test_build_url(self):
        # act
        result = networking_utils.UrlParser.build_url(url=self.url_data)
        # verify
        self.assertEqual(result, self.url)

    def test_build_url_without_scheme(self):
        url_data = self.url_data.copy()
        url_data["scheme"] = ""

        self.assertRaisesRegexp(
            Exception,
            "Url missing key value: scheme.",
            networking_utils.UrlParser.build_url,
            url_data,
        )

    def test_build_url_fail_when_url_empty(self):
        url_data = {}

        self.assertRaisesRegexp(
            Exception,
            "Url dictionary is empty.",
            networking_utils.UrlParser.build_url,
            url_data,
        )

    def test_url_parse_and_builder_returns_the_same(self):
        url_data = networking_utils.UrlParser.parse_url(self.url)

        self.assertEqual(networking_utils.UrlParser.build_url(url_data), self.url)

    def test_build_url_without_netloc(self):
        url_data = networking_utils.UrlParser.parse_url("http://test.com")
        url_data["netloc"] = ""
        backup_user = "user"  # we can add it in ConfigurationRunner
        backup_password = "password"
        port = "22"
        url_data.update(
            {
                networking_utils.UrlParser.USERNAME: backup_user,
                networking_utils.UrlParser.PASSWORD: backup_password,
                networking_utils.UrlParser.PORT: port,
            }
        )

        url = networking_utils.UrlParser.build_url(url_data)

        self.assertEqual(url, "http://user:password@test.com:22")

    def test_scp_link_parsed_and_return_same_link(self):
        url = (
            "scp://cisco:securePassword!1@test.host.com:"
            "//d:/some_path/test_file_name.ext?arg=val"
        )
        url_data = networking_utils.UrlParser.parse_url(url)
        new_url = networking_utils.UrlParser.build_url(url_data)
        self.assertEqual(url, new_url)

    def test_link_without_filename(self):
        url = "scp://cisco:securePassword!1@test.host.com" "//some_path/"
        url_data = networking_utils.UrlParser.parse_url(url)
        new_url = networking_utils.UrlParser.build_url(url_data)
        self.assertEqual(url, new_url)

    def test_simple_ftp_path(self):
        url = "ftp://192.168.122.10/Test-running-100418-163658"
        url_data = networking_utils.UrlParser.parse_url(url)
        new_url = networking_utils.UrlParser.build_url(url_data)
        self.assertEqual(url, new_url)
