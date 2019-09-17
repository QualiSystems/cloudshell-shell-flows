import sys
import unittest

from cloudshell.shell.flows.configuration.basic_flow import AbstractConfigurationFlow

if sys.version_info >= (3, 0):
    from unittest import mock
else:
    import mock


class TestAbstractConfigurationFlow(unittest.TestCase):
    def setUp(self):
        self.logger = mock.MagicMock()
        self.resource_config = mock.MagicMock()
        self.cli_handler = mock.MagicMock()
        self.api = mock.MagicMock()

        class ConfigurationFlow(AbstractConfigurationFlow):
            def _save_flow(self):
                pass

            def _restore_flow(self):
                pass

            @property
            def _file_system(self):
                return "flash:"

            def save_flow(self):
                pass

        self.config_flow = ConfigurationFlow(
            logger=self.logger, resource_config=self.resource_config
        )

    def test_abstract_methods(self):
        """Check that all abstract methods are implemented.

        Instance can't be instantiated without implementation of all abstract methods
        """
        with self.assertRaisesRegexp(
            TypeError,
            "Can't instantiate abstract class TestedClass with abstract methods "
            "_file_system, _restore_flow, _save_flow",
        ):

            class TestedClass(AbstractConfigurationFlow):
                pass

            TestedClass(logger=self.logger, resource_config=self.resource_config)

    def test_save(self):
        expected_path = "expected full path"
        folder_path = "test path"
        config_type = "running"
        self.resource_config.name = "test name"
        self.config_flow._save_flow = mock.MagicMock()
        self.config_flow._get_path = mock.MagicMock(return_value=expected_path)
        self.config_flow._validate_configuration_type = mock.MagicMock()
        # act
        result = self.config_flow.save(
            folder_path=folder_path,
            configuration_type=config_type,
            vrf_management_name=None,
            return_artifact=False,
        )
        # verify
        self.assertEqual(result, expected_path)
        self.config_flow._validate_configuration_type.assert_called_once_with(
            config_type
        )
        self.config_flow._save_flow.assert_called_once_with(
            folder_path=expected_path,
            configuration_type=config_type,
            vrf_management_name=self.resource_config.vrf_management_name,
        )

    def test_restore(self):
        expected_path = "expected full path"
        path = "test path"
        config_type = "running"
        restore_method = "override"
        self.resource_config.name = "test name"
        self.config_flow._restore_flow = mock.MagicMock()
        self.config_flow._get_path = mock.MagicMock(return_value=expected_path)
        self.config_flow._validate_configuration_type = mock.MagicMock()
        # act
        self.config_flow.restore(
            path=path,
            configuration_type=config_type,
            restore_method=restore_method,
            vrf_management_name=None,
        )
        # verify
        self.config_flow._restore_flow.assert_called_once_with(
            path=expected_path,
            configuration_type=config_type,
            restore_method=restore_method,
            vrf_management_name=self.resource_config.vrf_management_name,
        )

    def test_orchestration_save(self):
        pass

    def test_validate_configuration_type(self):
        config_type = "Running"
        # act # verify
        self.config_flow._validate_configuration_type(configuration_type=config_type)

    def test_validate_configuration_type__invalid_config_type(self):
        config_type = "invalid"
        if sys.version_info >= (3, 0):
            assert_regex = self.assertRaisesRegex
        else:
            assert_regex = self.assertRaisesRegexp

        # act # verify
        with assert_regex(
            Exception, "Configuration Type is invalid. Should be startup or running"
        ):
            self.config_flow._validate_configuration_type(
                configuration_type=config_type
            )

    @mock.patch("cloudshell.shell.flows.configuration.basic_flow.UrlParser")
    def test_get_path(self, url_parser_class):
        """Check that method will return UrlParser.build_url() result."""
        path = "some path"
        url = {url_parser_class.SCHEME: "ftp"}
        url_parser_class.parse_url.return_value = url
        builded_url = mock.MagicMock()
        url_parser_class.build_url.return_value = builded_url
        # act
        result = self.config_flow._get_path(path=path)
        # verify
        self.assertEqual(result, builded_url)
        url_parser_class.parse_url.assert_called_once_with(path)

    @mock.patch("cloudshell.shell.flows.configuration.basic_flow.UrlParser")
    def test_get_path_with_empty_path(self, url_parser_class):
        """Check that method will use backup location and backup type."""
        self.resource_config.backup_location = "backup_location"
        self.resource_config.backup_type = "backup_type"
        url = mock.MagicMock()
        url_parser_class.build_url.return_value = url
        # act
        self.config_flow._get_path()
        # verify
        url_parser_class.parse_url.assert_called_once_with(
            "backup_type://backup_location"
        )

    @mock.patch("cloudshell.shell.flows.configuration.basic_flow.UrlParser")
    def test_get_path_failed_to_build_url(self, url_parser_class):
        """Check that method will raise Exception if it unable to build the URL."""
        url_parser_class.build_url.side_effect = Exception
        # act
        with self.assertRaisesRegexp(
            Exception, "Failed to build path url to remote host"
        ):
            self.config_flow._get_path(path="some path")

    def test_get_path_for_default_file_system(self):
        self.resource_config.backup_location = "resource_startup.cfg"
        self.resource_config.backup_type = self.config_flow._file_system
        expected_path = "{}//{}".format(
            self.config_flow._file_system, self.resource_config.backup_location
        )
        # act
        path = self.config_flow._get_path()
        # verify
        self.assertEqual(expected_path, path)
