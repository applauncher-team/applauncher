import os
import yaml
from abc import ABC, abstractmethod
from pydantic import create_model

def load_configuration(configuration_file_path, parameters_file_path, bundles):
    mappings = {}
    for bundle in bundles:
        if hasattr(bundle, "config_mapping"):
            mappings.update(bundle.config_mapping)
    c = YmlLoader()
    return c.build_config(mappings, config_source=configuration_file_path, parameters_source=parameters_file_path)

def is_string(value):
    try:
        float(value)
        return False
    except ValueError:
        if value.lower() in ["true", "false"]:
            return False
        else:
            return True


class ConfigurationLoader(ABC):
    @abstractmethod
    def load_parameters(self, source):
        """Convert the source into a dictionary"""
        pass

    @abstractmethod
    def load_config(self, config_source, parameters_source):
        pass

    def build_config(self, config_mappings, config_source, parameters_source):
        Configuration = create_model('Configuration', **{k: (v, ...) for k, v in config_mappings.items()})
        return Configuration(**self.load_config(config_source, parameters_source))


class YmlLoader(ConfigurationLoader):
    def load_parameters(self, source):
        """For YML, the source it the file path"""
        with open(source) as parameters_source:
            loaded = yaml.safe_load(parameters_source.read())
            if loaded:
                for k, v in loaded.items():
                    if isinstance(v, str):
                        loaded[k] = "'" + v + "'"
                return loaded

    def load_config(self, config_source, parameters_source):
        """For YML, the source it the file path"""
        with open(config_source) as config_source:
            config_raw = config_source.read()

            parameters = {}
            """Parameteres from file"""
            if os.path.isfile(parameters_source):
                params = self.load_parameters(parameters_source)
                if params is not None:
                    parameters.update(params)

            """Overwrite parameteres with the environment variables"""
            env_params = {}
            env_params.update(os.environ)
            for k, v in env_params.items():
                if is_string(v):
                    env_params[k] = "'" + v + "'"

            parameters.update(env_params)
            """Replace the parameters"""
            final_configuration = config_raw.format(**parameters)
            final_configuration = yaml.safe_load(final_configuration)
            return final_configuration if final_configuration is not None else {}