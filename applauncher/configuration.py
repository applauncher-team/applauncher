"""Configuration format loaders"""
import os
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
        with open(source) as parameters_source:
            loaded = yaml.safe_load(parameters_source.read())
            if loaded:
                for key, value in loaded.items():
                    if isinstance(value, str):
                        loaded[key] = "'" + value + "'"
                return loaded
        return {}

    def load_config(self, config_source, parameters_source):
        """For YML, the source it the file path"""
        with open(config_source) as config_source_file:
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
            final_configuration = config_raw.format(**parameters)
            final_configuration = yaml.safe_load(final_configuration)
            return final_configuration if final_configuration is not None else {}
