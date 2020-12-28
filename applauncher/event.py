import blinker

class EventHierarchy(type):
    def __new__(mcs, name, bases, dct):
        signal_list = [dct["event_name"]]
        for base in bases:
            if hasattr(base, "_signals"):
                signal_list += getattr(base, "_signals")
        dct["_signals"] = signal_list
        return type.__new__(mcs, name, bases, dct)


class Event(metaclass=EventHierarchy):
    event_name = "event"


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

        if isinstance(event, str):
            s = blinker.signal(event)
        else:
            s = blinker.signal(event.event_name)

        s.connect(listener)

    def dispatch(self, event):
        for i in getattr(event, "_signals"):
            blinker.signal(i).send(event)