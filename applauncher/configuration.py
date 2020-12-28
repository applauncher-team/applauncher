from mapped_config.loader import YmlLoader, InvalidDataException


def load_configuration(configuration_file_path, parameters_file_path, bundles):
    mappings = {}
    for bundle in bundles:
        if hasattr(bundle, "config_mapping"):
            mappings.update(bundle.config_mapping)
    c = YmlLoader()
    config = c.load_config(configuration_file_path, parameters_file_path)
    config = c.build_config(config, mappings)

    return config
