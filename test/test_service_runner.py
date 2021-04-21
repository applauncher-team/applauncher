from applauncher.service_runner import ProcessServiceRunner
from multiprocessing import Manager
import time
import signal


# Just a dummy process
def handler(signum, frame):
    print("HANDLER")


def infinito():
    try:
        signal.signal(signal.SIGTERM, handler)
        signal.signal(signal.SIGINT, handler)
    except Exception as e:
        print(e)

    while True:
        time.sleep(1)

# The tests
class TestClass:
    def test_run(self):
        r = ProcessServiceRunner()
        r.add_service(name="A", function=infinito)
        r.add_service(name="B", function=infinito)
        r.add_service(name="C", function=infinito)
        r.add_service(name="D", function=infinito)
        assert len(r.running_services) == 4
        # In the beginning everything is stopeed
        name, process = r.running_services[0]
        assert name == "A"
        assert process.is_alive() is False
        name, process = r.running_services[1]
        assert name == "B"
        assert process.is_alive() is False
        name, process = r.running_services[2]
        assert name == "C"
        assert process.is_alive() is False
        name, process = r.running_services[3]
        assert name == "D"
        assert process.is_alive() is False

        r.run()
        # Now everything should be running
        name, process = r.running_services[0]
        assert name == "A"
        assert process.is_alive() is True
        name, process = r.running_services[1]
        assert name == "B"
        assert process.is_alive() is True
        name, process = r.running_services[2]
        assert name == "C"
        assert process.is_alive() is True
        name, process = r.running_services[3]
        assert name == "D"
        assert process.is_alive() is True
        r.kill()

    def test_shutdown(self):
        r = ProcessServiceRunner()
        r.add_service(name="A", function=infinito)
        r.add_service(name="B", function=infinito)
        r.add_service(name="C", function=infinito)
        r.add_service(name="D", function=infinito)
        assert len(r.running_services) == 4
        # In the beginning everything is stopeed
        name, process = r.running_services[0]
        assert name == "A"
        assert process.is_alive() is False
        name, process = r.running_services[1]
        assert name == "B"
        assert process.is_alive() is False
        name, process = r.running_services[2]
        assert name == "C"
        assert process.is_alive() is False
        name, process = r.running_services[3]
        assert name == "D"
        assert process.is_alive() is False

        r.run()
        # Now everything should be running
        name, process = r.running_services[0]
        assert name == "A"
        assert process.is_alive() is True
        name, process = r.running_services[1]
        assert name == "B"
        assert process.is_alive() is True
        name, process = r.running_services[2]
        assert name == "C"
        assert process.is_alive() is True
        name, process = r.running_services[3]
        assert name == "D"
        assert process.is_alive() is True

        r.shutdown(grace_time=2)
        time.sleep(3)
        # Now everything should be stopped
        name, process = r.running_services[0]
        assert name == "A"
        assert process.is_alive() is False
        name, process = r.running_services[1]
        assert name == "B"
        assert process.is_alive() is False
        name, process = r.running_services[2]
        assert name == "C"
        assert process.is_alive() is False
        name, process = r.running_services[3]
        assert name == "D"
        assert process.is_alive() is False

    def test_kill(self):
        r = ProcessServiceRunner()
        r.add_service(name="A", function=infinito)
        r.add_service(name="B", function=infinito)
        r.add_service(name="C", function=infinito)
        r.add_service(name="D", function=infinito)
        assert len(r.running_services) == 4
        # In the beginning everything is stopeed
        name, process = r.running_services[0]
        assert name == "A"
        assert process.is_alive() is False
        name, process = r.running_services[1]
        assert name == "B"
        assert process.is_alive() is False
        name, process = r.running_services[2]
        assert name == "C"
        assert process.is_alive() is False
        name, process = r.running_services[3]
        assert name == "D"
        assert process.is_alive() is False

        r.run()
        # Now everything should be running
        name, process = r.running_services[0]
        assert name == "A"
        assert process.is_alive() is True
        name, process = r.running_services[1]
        assert name == "B"
        assert process.is_alive() is True
        name, process = r.running_services[2]
        assert name == "C"
        assert process.is_alive() is True
        name, process = r.running_services[3]
        assert name == "D"
        assert process.is_alive() is True

        r.kill()
        # Now everything should be stopped
        name, process = r.running_services[0]
        assert name == "A"
        assert process.is_alive() is False
        name, process = r.running_services[1]
        assert name == "B"
        assert process.is_alive() is False
        name, process = r.running_services[2]
        assert name == "C"
        assert process.is_alive() is False
        name, process = r.running_services[3]
        assert name == "D"
        assert process.is_alive() is False

    def test_wait(self):
        """Check that we are actually waiting for the service to end"""
        r = ProcessServiceRunner()
        manager = Manager()
        d = manager.dict()
        d["value"] = 0

        def wait_function(data):
            data["value"] = 1
            time.sleep(1)

        r.add_service(name="A", function=wait_function, args=(d,))
        assert d["value"] == 0
        r.run()
        assert len(r.running_services) == 1
        r.wait()
        assert d["value"] == 1

    def test_shutdown_no_grace_time(self):
        r = ProcessServiceRunner()
        r.add_service(name="A", function=infinito)
        assert len(r.running_services) == 1
        name, process = r.running_services[0]
        assert name == "A"
        assert process.is_alive() is False
        r.run()
        assert process.is_alive() is True
        r.shutdown(grace_time=1)
        assert process.is_alive() is False
