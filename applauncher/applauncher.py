from rich.traceback import install
install()
from .event import EventManager
from .configuration import load_configuration
from mapped_config import InvalidDataException
import signal
from rich.console import Console
import re
from .logging import configure_logger
from .service_runner import ProcessServiceRunner
from .event import KernelReadyEvent, KernelShutdownEvent


def inject(t):
    return Kernel.inject_bindings[t]()

def register(t, prov):
    Kernel.inject_bindings[t] = prov

class Kernel(object):

    inject_bindings = {}

    def __init__(self,
                 environment,
                 bundles,
                 configuration_file="config/config.yml",
                 parameters_file="config/parameters.yml"):
        self.logger = configure_logger()
        console = Console()
        self.console = console
        console.log(f"Running environment [bold green]{environment}[/]")
        self.bundles = bundles
        self.environment = environment
        self.event_manager = EventManager()
        self.service_runner = ProcessServiceRunner()
        self.shutting_down = False


        with console.status("[bold green]Booting kernel...") as status:
            # Configuration
            console.log(f"Parsing configuration...")
            try:
                self.config = load_configuration(
                    configuration_file_path=configuration_file,
                    parameters_file_path=parameters_file,
                    bundles=bundles
                )
                console.log("Configuration [bold green]OK[/]")
            except InvalidDataException as ex:
                console.rule("[bold red]Configuration error")
                for error in ex.errors:
                    for i in re.findall("\[[A-Za-z]+]", error):
                        error = error.replace(i, f"[bold red]{i[1:-1]}[/]")
                    console.log(error, style="yellow")
            # Events
            console.log("Registering event listeners")
            for bundle in self.bundles:
                if hasattr(bundle, 'event_listeners'):
                    for event_type, listener in bundle.event_listeners:
                        self.event_manager.add_listener(event=event_type, listener=listener)
                    console.log((f"Registered events for [bold cyan]{bundle.__class__.__name__}[/]: {', '.join([f'[bright_magenta]{event_type.__name__}[/]' for event_type, _ in bundle.event_listeners])}"))
            console.log("Events [bold green]OK[/]")

            console.log("Building dependency container")
            for bundle in self.bundles:
                if hasattr(bundle, 'injection_bindings'):
                    for class_type, provider in bundle.injection_bindings.items():
                        register(class_type, provider)
            console.log("Dependency container built")
            console.log("[bold green]Kernel ready[/]")
            self.event_manager.dispatch(KernelReadyEvent())
            console.log("Running services")
            for bundle in self.bundles:
                if hasattr(bundle, 'services'):
                    for service_name, service_function, args, kwargs in bundle.services:
                        console.log(f"Adding {service_name}")
                        self.service_runner.add_service(
                            name=service_name,
                            function=service_function,
                            args=args,
                            kwargs=kwargs
                        )
        self.service_runner.run()
        # Signals
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signal, frame):
        self.shutdown()

    def shutdown(self):
        if not self.shutting_down:
            self.console.log("Shutdown signal received, press ctrl + c to kill the process")
            self.shutting_down = True
            self.service_runner.shutdown()
        else:
            self.console.log("[bold red]Killing...[/]")
            self.service_runner.kill()

    def wait(self):
        self.service_runner.wait()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.event_manager.dispatch(KernelShutdownEvent())
        self.console.log("Kernel shutdown")
