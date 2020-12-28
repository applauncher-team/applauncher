from applauncher.event import EventManager, KernelReadyEvent, ConfigurationReadyEvent

class TestClass:
    def test_events(self):
        em = EventManager()

        class KernelCounter:
            c = 0
            @staticmethod
            def inc(event):
                KernelCounter.c += 1

            @staticmethod
            def dec(event):
                KernelCounter.c -= 1

        class OtherCounter:
            c = 0

            @staticmethod
            def inc(event):
                OtherCounter.c += 1

            @staticmethod
            def dec(event):
                OtherCounter.c -= 1

        assert KernelCounter.c == 0
        assert OtherCounter.c == 0
        em.add_listener(KernelReadyEvent, KernelCounter.inc)
        em.add_listener(ConfigurationReadyEvent, OtherCounter.inc)
        assert KernelCounter.c == 0

        em.dispatch(KernelReadyEvent())
        assert KernelCounter.c == 1
        assert OtherCounter.c == 0

        em.dispatch(KernelReadyEvent())
        assert KernelCounter.c == 2
        assert OtherCounter.c == 0

        em.dispatch(ConfigurationReadyEvent({"config": "config"}))
        assert KernelCounter.c == 2
        assert OtherCounter.c == 1

    def test_event_content(self):
        em = EventManager()

        class OtherCounter:
            config = None
            @staticmethod
            def event(event):
                OtherCounter.config = event.configuration

        assert OtherCounter.config is None
        em.dispatch(ConfigurationReadyEvent({"config": "config"}))
        assert OtherCounter.config is None
        em.add_listener(ConfigurationReadyEvent, OtherCounter.event)
        em.dispatch(ConfigurationReadyEvent({"config": "config"}))
        assert OtherCounter.config == {"config": "config"}