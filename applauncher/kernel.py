import logging
import inject
import zope.event
import mapped_config.loader
from abc import ABCMeta, abstractmethod
import six

# This class is only used for an friendly injection of configuration
class Configuration(object):
    pass


class Environments(object):
    DEVELOPMENT = "dev"
    PRODUCTION = "prod"
    TEST = "test"


class KernelReadyEvent(object):
    pass


class InjectorReadyEvent(object):
    pass

@six.add_metaclass(ABCMeta)
class Kernel(object):

    def __init__(self, environment, bundles, configuration_file="config/config.yml", parameters_file="config/parameters.yml"):
        self.logger = None
        self.configuration_file = configuration_file
        self.parameters_file = parameters_file
        self.bundles = bundles
        self.environment = environment

        try:
            self.configuration = self.load_configuration(environment)
            # Injection provided by the base system
            injection_bindings = {
                Kernel: self,
                Configuration: self.configuration
            }
            # Injection from other bundles
            for bundle in self.bundles:
                if hasattr(bundle, 'injection_bindings'):
                    injection_bindings.update(bundle.injection_bindings)

            # Set this kernel and configuration available for injection
            def my_config(binder):
                for key, value in injection_bindings.items():
                    binder.bind(key, value)
            inject.configure(my_config)
            zope.event.notify(InjectorReadyEvent())
        except Exception as e:
            logging.exception(e)
            raise e

        self.configure_logger(environment=environment)
        self.logger.info("Kernel started")
        zope.event.notify(KernelReadyEvent())

    def configure_logger(self, environment):
        # Get root logger
        self.logger = logging.getLogger(self.__class__.__name__)
        root_logger = logging.getLogger('')
        if environment == Environments.DEVELOPMENT:
            logging.basicConfig(level=logging.DEBUG)
            self.logger.setLevel(logging.DEBUG)
            root_logger.setLevel(logging.DEBUG)

            # Console output
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            # Remove the default handlers
            del root_logger.handlers[:]
            root_logger.addHandler(ch)
            root_logger.info("Console Handler Ready")
        elif environment == Environments.PRODUCTION:
            pass
            # Fluent output
            # fluent_config = self.configuration.fluent
            # h = handler.FluentHandler('fluent', host=fluent_config.host, port=fluent_config.port)
            # # formatter = handler.FluentRecordFormatter(custom_format)
            # formatter = handler.FluentRecordFormatter()
            # h.setFormatter(formatter)
            # h.setLevel(logging.DEBUG)
            # root_logger.addHandler(h)
            # root_logger.info("Fluentd configuration ready")
        self.logger.info("Logger initialized")

    def load_configuration(self, environment):
        mappings = [bundle.config_mapping for bundle in self.bundles if hasattr(bundle, "config_mapping")]
        c = mapped_config.loader.YmlLoader()
        #path.dirname(path.realpath(__file__))
        config = c.load_config(self.configuration_file, self.parameters_file)
        try:
            config = c.build_config(config, mappings)
        except mapped_config.loader.NoValueException as ex:
            print("Configuration error: " + str(ex))
            exit()
        except mapped_config.loader.NodeIsNotConfiguredException as ex:
            print("Configuration error: " + str(ex))
            exit()
        except mapped_config.loader.IgnoredFieldException as ex:
            print("Configuration error: " + str(ex))
            exit()

        return config

