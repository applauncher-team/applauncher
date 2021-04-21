"""Base events used by the applauncher kernel. Bundles events can extend them"""
import blinker


class EventHierarchy(type):
    """Build the full namespace when creating an event"""
    def __new__(cls, name, bases, dct):
        signal_list = [dct["event_name"]]
        for base in bases:
            if hasattr(base, "_signals"):
                signal_list += getattr(base, "_signals")
        dct["_signals"] = signal_list
        return type.__new__(cls, name, bases, dct)


class Event(metaclass=EventHierarchy):
    """Generic event"""
    event_name = "event"


class KernelReadyEvent(Event):
    """Raised when the kernel is fully ready"""
    event_name = "kernel.kernel_ready"


class ConfigurationReadyEvent(Event):
    """Raised when the configuration is ready. The configuration is provided in the event"""
    event_name = "kernel.configuration_ready"

    def __init__(self, configuration):
        self.configuration = configuration


class InjectorReadyEvent(Event):
    """Raised when you can use the dependency injection container"""
    event_name = "kernel.injector_ready"


class KernelShutdownEvent(Event):
    """This event will be sent to your bundle to notify that it should stop everything"""
    event_name = "kernel.kernel_shutdown"


class EventManager:
    """To register and dispatch application events"""
    @staticmethod
    def add_listener(event, listener):
        """Listen for an event"""
        if isinstance(event, str):
            channel = blinker.signal(event)
        else:
            channel = blinker.signal(event.event_name)

        channel.connect(listener)

    @staticmethod
    def dispatch(event):
        """This event will be propagated to all listeners"""
        for channel in getattr(event, "_signals"):
            blinker.signal(channel).send(event)
