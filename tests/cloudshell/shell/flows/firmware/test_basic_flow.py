import sys
import unittest

from cloudshell.shell.flows.firmware.basic_flow import AbstractFirmwareFlow

if sys.version_info >= (3, 0):
    from unittest import mock
else:
    import mock


class TestAbstractFirmwareFlow(unittest.TestCase):
    def setUp(self):
        class FirmwareFlow(AbstractFirmwareFlow):
            def _load_firmware_flow(self, path, vrf_management_name, timeout):
                pass

        self.logger = mock.MagicMock()
        self.cli_handler = mock.MagicMock()
        self.firmware_flow = FirmwareFlow(logger=self.logger)

    def test_abstract_methods(self):
        """Check that all abstract methods are implemented.

        Instance can't be instantiated without implementation of all abstract methods
        """
        with self.assertRaisesRegexp(
            TypeError,
            "Can't instantiate abstract class TestedClass with "
            "abstract methods _load_firmware_flow",
        ):

            class TestedClass(AbstractFirmwareFlow):
                pass

            TestedClass(logger=self.logger)

    @mock.patch("cloudshell.shell.flows.firmware.basic_flow.UrlParser")
    def test_load_firmware(self, url_parser_class):
        """Check that method will execute _load_firmware_flow."""
        url = mock.MagicMock(__contains__=mock.MagicMock(return_value=True))
        url_parser_class.parse_url.return_value = url
        path = "test path"
        vrf_mmgmt_name = "test vrf mgmt name"
        self.firmware_flow._load_firmware_flow = mock.MagicMock()
        # act
        self.firmware_flow.load_firmware(path=path, vrf_management_name=vrf_mmgmt_name)
        self.firmware_flow._load_firmware_flow.assert_called_once_with(
            path, vrf_mmgmt_name, self.firmware_flow._timeout
        )

    @mock.patch("cloudshell.shell.flows.firmware.basic_flow.UrlParser")
    def test_load_firmware_path_with_invalid_path(self, url_parser_class):
        """Check that method will raise exception if path is invalid."""
        url = mock.MagicMock(__contains__=mock.MagicMock(return_value=False))
        url_parser_class.parse_url.return_value = url
        path = "test path"
        vrf_mmgmt_name = "test vrf mgmt name"
        # act
        with self.assertRaisesRegexp(Exception, "Path is wrong or empty"):
            self.firmware_flow.load_firmware(
                path=path, vrf_management_name=vrf_mmgmt_name
            )
