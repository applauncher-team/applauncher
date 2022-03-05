"""Configuration format loaders"""
import locale
import os
import re
import string
from abc import ABC, abstractmethod

import yaml
from pydantic import create_model


def load_configuration(configuration_file_path, parameters_file_path, bundles):
    """Combines the configuration and parameters and build the configuration object"""
    mappings = {}
    for bundle in bundles:
        if hasattr(bundle, "config_mapping"):
            mappings.update(bundle.config_mapping)
    loader = YmlLoader()
    return loader.build_config(mappings, config_source=configuration_file_path, parameters_source=parameters_file_path)


def is_string(value):
    """Check if the value is actually a string or not"""
    try:
        float(value)
        return False
    except ValueError:
        if value.lower() in ["true", "false"]:
            return False
        return True


class ConfigurationLoader(ABC):
    """Base configuration loader"""
    @abstractmethod
    def load_parameters(self, source):
        """Convert the source into a dictionary"""

    @abstractmethod
    def load_config(self, config_source, parameters_source):
        """Prase the config file and build a dictionary"""

    def build_config(self, config_mappings, config_source, parameters_source):
        """By using the loaded parameters and loaded config, build the final configuration object"""
        configuration_class = create_model('Configuration', **{k: (v, ...) for k, v in config_mappings.items()})
        return configuration_class(**self.load_config(config_source, parameters_source))


class YmlLoader(ConfigurationLoader):
    """YML Format parser and config loader"""
    def load_parameters(self, source):
        """For YML, the source it the file path"""
        with open(source, encoding=locale.getpreferredencoding(False)) as parameters_source:
            loaded = yaml.safe_load(parameters_source.read())
            if loaded:
                for key, value in loaded.items():
                    if isinstance(value, str):
                        loaded[key] = "'" + value + "'"
                return loaded
        return {}

    def load_config(self, config_source, parameters_source):
        """For YML, the source it the file path"""
        with open(config_source, encoding=locale.getpreferredencoding(False)) as config_source_file:
            config_raw = config_source_file.read()

            parameters = {}
            # Parameters from file
            if os.path.isfile(parameters_source):
                params = self.load_parameters(parameters_source)
                if params is not None:
                    parameters.update(params)

            # Overwrite parameters with the environment variables
            env_params = {}
            env_params.update(os.environ)
            for key, value in env_params.items():
                if is_string(value):
                    env_params[key] = "'" + value + "'"

            parameters.update(env_params)
            # Replace the parameters
            final_configuration = FormatterWithListYAML().format(config_raw, **parameters)
            final_configuration = yaml.safe_load(final_configuration)
            return final_configuration if final_configuration is not None else {}


class FormatterWithListYAML(string.Formatter):
    """This class adds extra formatting options to format a string as a list.
    Both [] and YAML-style (item list with -) are supported.
    """

    def __init__(self, default_spaces: int = 2, default_splitter: str = ','):
        """Instantiate class with specific params.

        :param default_spaces: If YAML item list is used, how many spaces should prefix each line?
        :param default_splitter: If no splitter is provided, which character wil be used to split the string?
        """
        self.default_spaces = default_spaces
        self.default_splitter = default_splitter

    def format_field(self, value, format_spec) -> str:
        """Takes the value which should replace the placeholder in the format string and returns it ready.

        :param value: This is the value which will replace a specific {PLACEHOLDER} in the string.
        :param format_spec: This string describes how to format that value {PLACEHOLDER:format_spec}

        :return: The formatted value to be inserted.
        """
        if format_spec.startswith('['):
            return self._format_list_field(value, format_spec)
        return super().format_field(value, format_spec)

    def _format_list_field(self, value, format_spec) -> str:
        """This is the specific logic to convert the string into a list.

        :param value: This is the value which will replace a specific {PLACEHOLDER} in the string.
        :param format_spec: This string describes how to format that value {PLACEHOLDER:format_spec}

        :return: The formatted value to be inserted."""
        if len(format_spec) > 2 and format_spec[2] == ']':
            splitter = format_spec[1]
        else:
            splitter = self.default_splitter
        # Found out the value is enclosed in quotes sometimes D:
        split_value = value.rstrip("'").lstrip("'").rstrip('"').lstrip('"').split(splitter)
        make_item_list = '-' in format_spec
        if not make_item_list:
            # f-string can't be used since we have both quoting marks occupied.
            return '["{}"]'.format('", "'.join(split_value))  # pylint: disable=consider-using-f-string
        spaces = re.search(r'\.(\d+)', format_spec)
        spaces = int(spaces.groups()[0]) if spaces else self.default_spaces
        add_prefix_to_first = '^' in format_spec
        output = '{}{}'.format(f"\n{' ' * spaces}- " if add_prefix_to_first else '', split_value[0])
        for list_element in split_value[1:]:
            output += f"\n{' ' * spaces}- {list_element}"
        return output
