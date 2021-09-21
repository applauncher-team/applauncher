"""Applaucher kernel and boot process"""
import sys
import signal
import importlib
import types
from multiprocessing import current_process
from typing import List
from rich.traceback import install
from rich.table import Table
from rich.console import Console
from pydantic import ValidationError
from dependency_injector import containers, providers
from .logging import configure_logger
from .service_runner import ProcessServiceRunner
from .event import KernelReadyEvent, KernelShutdownEvent, ConfigurationReadyEvent
from .event import EventManager
from .configuration import load_configuration


install()
configure_logger()


class Configuration(providers.Provider):
    """Configuration injector"""
    def __deepcopy__(self, memo):
        copied = memo.get(id(self))
        if copied is not None:
            return copied

        copied = self.__class__()
        self._copy_overridings(copied, memo)

        return copied

    def _provide(self, _args, _kwargs):
        return Kernel.config


class ServiceContainerMeta(type):
    """Service container use interface. Here all containers will be gathered"""
    def __getattr__(cls, key):
        if cls.container is None:
            raise Exception("Service container not configured yet!")
        if not hasattr(cls.container, key):
            raise Exception(f'Service container does not have any "{key}" service')
        return getattr(cls.container, key)


class ServiceContainer(metaclass=ServiceContainerMeta):
    """This service container will contain all bundle and application containers"""
    container = None


class Kernel:
    """The application initializer. It loads all the components and then let the control to the bundles"""
    inject_bindings = {}
    config = None

    container = containers.DynamicContainer()

    def load_configuration(self, configuration_file, parameters_file):
        """Parse the configuration and put it into the kernel and container"""
        self.console.log("Parsing configuration...")
        try:
            self.config = load_configuration(
                configuration_file_path=configuration_file,
                parameters_file_path=parameters_file,
                bundles=self.bundles
            )
            Kernel.config = self.config
            self.container.configuration = Configuration()
            self.console.log("Configuration [bold green]OK[/]")
        except ValidationError as ex:
            self.console.rule("[bold red]Configuration error")
            for error in ex.errors():
                loc = "[yellow] -> [/]".join([f"[cyan]{i}[/]" for i in error["loc"]])
                self.console.print(f"{loc}: {error['msg']} (type={error['type']})")
            sys.exit()

    def kernel_ready_event(self, _event):
        """Seeing this message is the proof that the events are working"""
        table = Table(show_header=False, style="bold green")
        table.add_row("Kernel ready")
        self.console.print(table)

    def kernel_shutdown_event(self, _event):
        """Seeing this message is the proof that the events are working"""
        table = Table(show_header=False, style="bold cyan")
        table.add_row("Kernel shutdown")
        self.console.print(table)

    def register_event_listeners(self, config_only: bool = False):
        """Add all kernel and bundles listeners"""
        config_text = "for ConfigurationReadyEvent only" if config_only else "for all other events"
        self.console.log(f"Registering event listeners {config_text}")
        for bundle in self.bundles:
            event_list = self.register_event_listeners_for_bundle(bundle, config_only=config_only)
            self.log_event_listeners_registered_for_bundle(bundle, event_list)
        # Blinker does not duplicate signals so there is probably no reason to worry about adding listeners
        # twice, but anyways checking makes sense to me.
        if not config_only:
            self.event_manager.add_listener(event=KernelReadyEvent, listener=self.kernel_ready_event)
            self.event_manager.add_listener(event=KernelShutdownEvent, listener=self.kernel_shutdown_event)
        self.console.log("Events [bold green]OK[/]")

    def register_event_listeners_for_bundle(self, bundle: object, config_only: bool = False):
        """Add bundles' event listeners"""
        registered_listeners = []
        for event_type, listener in getattr(bundle, 'event_listeners', []):
            is_config_event = issubclass(event_type, ConfigurationReadyEvent)
            must_register = is_config_event if config_only else not is_config_event
            if not must_register:
                continue
            self.event_manager.add_listener(event=event_type, listener=listener)
            registered_listeners.append(event_type)
        return registered_listeners

    def log_event_listeners_registered_for_bundle(self, bundle: object, registered_listeners: List[str]):
        """Display in the console the added event listeners"""
        if registered_listeners:
            event_list = ', '.join(
                [f'[bright_magenta]{event_type.__name__}[/]' for event_type in registered_listeners]
            )
            self.console.log(f"Registered events for [bold cyan]{bundle.__class__.__name__}[/]: {event_list}")

    def build_dependency_container(self):
        """Build the kernel and bundles service containers"""
        self.console.log("Building dependency container")
        wire_modules = []
        for bundle in self.bundles:
            if hasattr(bundle, 'injection_bindings'):
                for class_type, provider in bundle.injection_bindings.items():
                    # A container provider is useful when a container has dependencies on other containers. Just provide
                    # the container class as an easy way to use the defaults
                    if isinstance(provider, types.FunctionType):
                        # We use a function instead of directly the Provider to ensure that the dependencies are using
                        # exactly the same container (and not other instance). Otherwise, the singletons will not be
                        # singletons (will be at least two instances, one per container
                        provider = provider(self.container)
                    else:
                        provider = providers.Container(provider)
                    setattr(self.container, class_type, provider)

            if hasattr(bundle, 'wire_modules'):
                wire_modules += bundle.wire_modules

        # Applauncher services
        self.container.event_manager = providers.Object(self.event_manager)
        self.container.kernel = providers.Object(self)

        if wire_modules:
            self.console.log(f"[bold cyan]Wiring[/] modules: {wire_modules}")
            self.container.wire(modules=[importlib.import_module(module) for module in wire_modules])
        self.console.log("Dependency container [bold]built[/]")

    def register_services(self):
        """Register the bundles services but not run them yet, it will be done later"""
        self.console.log("Registering services")
        for bundle in self.bundles:
            if hasattr(bundle, 'services'):
                for service_name, service_function, args, kwargs in bundle.services:
                    self.console.log(f"Adding {service_name}")
                    self.service_runner.add_service(
                        name=service_name,
                        function=service_function,
                        args=args,
                        kwargs=kwargs
                    )

    def __init__(self,
                 environment,
                 bundles,
                 configuration_file="config/config.yml",
                 parameters_file="config/parameters.yml"):
        self.console = Console()
        self.console.log(f"Running environment [bold green]{environment}[/]")
        self.bundles = bundles
        self.environment = environment
        self.event_manager = EventManager()
        self.service_runner = ProcessServiceRunner()
        self.shutting_down = False

        # Signals
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        with self.console.status("[bold green]Booting kernel..."):
            self.load_configuration(configuration_file=configuration_file, parameters_file=parameters_file)
            self.register_event_listeners(config_only=True)
            self.event_manager.dispatch(ConfigurationReadyEvent(configuration=self.config))
            self.register_event_listeners()
            self.build_dependency_container()
            self.event_manager.dispatch(KernelReadyEvent())
            self.register_services()

        self.service_runner.run()

    def _signal_handler(self, _os_signal, _frame):
        self.shutdown()

    def shutdown(self):
        """Start the kernel shutdown process. It will stopp all services and the exit"""
        is_main = current_process().name == 'MainProcess'
        if not self.shutting_down:
            if is_main:
                table = Table(show_header=False, style="bold red")
                table.add_row("Shutdown signal received, press ctrl + c to kill the process")
                self.console.print(table)
                self.shutting_down = True
                self.service_runner.shutdown()
            # The container should be shutted down even in forks
            self.container.shutdown_resources()
        elif is_main:
            self.console.log("[bold red]Killing...[/]")
            self.service_runner.kill()

    def wait(self):
        """Wait until all services are done"""
        self.service_runner.wait()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.event_manager.dispatch(KernelShutdownEvent())


ServiceContainer.container = Kernel.container
