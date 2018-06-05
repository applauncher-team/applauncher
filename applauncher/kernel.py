import logging
import inject
import signal
from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor
from mediator import Event as MediatorEvent, Mediator, SubscriberInterface
from mapped_config.loader import YmlLoader, NoValueException, NodeIsNotConfiguredException, IgnoredFieldException


class Configuration(object):
    """This class is only used for an friendly injection of configuration"""
    pass


class Environments(object):
    DEVELOPMENT = "dev"
    PRODUCTION = "prod"
    TEST = "test"


class Event(MediatorEvent):
    """Event is used as en Interface to mediator.Event"""
    pass


class KernelReadyEvent(Event):
    event_name = "kernel.kernel_ready"


class ConfigurationReadyEvent(Event):
    event_name = "kernel.configuration_ready"

    def __init__(self, configuration):
        self.configuration = configuration


class InjectorReadyEvent(Event):
    event_name = "kernel.injector_ready"


class KernelShutdownEvent(Event):
    event_name = "kernel.kernel_shutdown"


class EventManager(object):
    def add_listener(self, event, listener):
        pass

    def add_subscriber(self, subscriber):
        pass

    def dispatch(self, event):
        pass


class EventSubscriber(SubscriberInterface):
    pass


class Kernel(object):

    def __init__(self,
                 environment,
                 bundles,
                 configuration_file="config/config.yml",
                 parameters_file="config/parameters.yml"):
        self.logger = None
        self.configuration_file = configuration_file
        self.parameters_file = parameters_file
        self.bundles = bundles
        self.environment = environment
        self.log_handlers = []
        self.is_shutdown = False
        max_workers = cpu_count() * 5
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.running_services = []
        self.mediator = Mediator()

        try:
            self.configuration = self.load_configuration(environment)

            # Subscribe bundle events
            for bundle in self.bundles:
                if hasattr(bundle, 'event_listeners'):
                    for event_type, listener in bundle.event_listeners:
                        self.mediator.add_listener(event=event_type, listener=listener)

                if hasattr(bundle, 'event_subscribers'):
                    for subscriber in bundle.event_subscribers:
                        self.mediator.add_subscriber(subscriber=subscriber)

            # Injection provided by the base system
            injection_bindings = {
                Kernel: self,
                Configuration: self.configuration,
                EventManager: self.mediator
            }
            self.mediator.dispatch(ConfigurationReadyEvent(self.configuration))
            # Injection from other bundles
            for bundle in self.bundles:
                if hasattr(bundle, 'injection_bindings'):
                    injection_bindings.update(bundle.injection_bindings)

            # Set this kernel and configuration available for injection
            def my_config(binder):
                for key, value in injection_bindings.items():
                    binder.bind(key, value)
            inject.configure(my_config)
            self.mediator.dispatch(InjectorReadyEvent())

            for bundle in self.bundles:
                if hasattr(bundle, 'log_handlers'):
                    self.log_handlers += bundle.log_handlers
        except Exception as e:
            logging.exception(e)
            raise e

        self.configure_logger(environment=environment)
        self.register_signals()
        logging.info("Kernel Ready")
        self.mediator.dispatch(KernelReadyEvent())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.shutdown()

    def register_signals(self):
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signal, frame):
        self.shutdown()

    def run_service(self, service_function, *args):
        self.running_services.append(self.thread_pool.submit(service_function, *args))

    def configure_logger(self, environment):
        log_level = logging.INFO
        if environment == Environments.DEVELOPMENT:
            # Console output
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            self.log_handlers.append(ch)
            log_level = logging.INFO

        logging.basicConfig(level=log_level, handlers=self.log_handlers)
        logging.info("Logger ready")

    def load_configuration(self, environment):
        config_mappings = [bundle.config_mapping for bundle in self.bundles if hasattr(bundle, "config_mapping")]
        config = None
        if len(config_mappings) > 0:
            c = YmlLoader()
            config = c.load_config(self.configuration_file, self.parameters_file)
            try:
                config = c.build_config(config, config_mappings)
            except (NoValueException,
                    NodeIsNotConfiguredException,
                    IgnoredFieldException) as ex:
                print("Configuration error: " + str(ex))
                exit()
        return config

    def shutdown(self):
        if not self.is_shutdown:
            self.is_shutdown = True
            logging.info("Kernel shutting down")
            self.mediator.dispatch(KernelShutdownEvent())
            self.thread_pool.shutdown()
            logging.info("Kernel shutdown")

    def wait(self):
        """Wait for all services to finish"""
        for i in self.running_services:
            i.result()
