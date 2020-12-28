from multiprocessing import Process
import asyncio
import os
import logging


class ProcessServiceRunner:
    def __init__(self):
        self.logger = logging.getLogger("service")
        self.running_services = []

    def add_service(self, name, function, args, kwargs):
        self.running_services.append((name, Process(target=function, args=args, kwargs=kwargs)))

    def run(self):
        for name, process in self.running_services:
            self.logger.info(f"Starting service {name}")
            process.start()

    def wait(self):
        self.logger.info(f"Waiting for services to end")
        for _, i in self.running_services:
            i.join()

    def kill(self):
        for name, process in self.running_services:
            self.logger.info(f"Killing service {name} ({process.pid})")
            os.kill(process.pid, 9)
            process.join()


    async def _terminate_processes(self, processes, grace_time=10):
        await asyncio.gather(*[
            self._terminate_process(*i, grace_time) for i in processes
        ])

    async def _terminate_process(self, name, process, grace_time=10):
        self.logger.info(f"Terminating service {name} ({process.pid})")
        process.terminate()
        wait = True
        while wait:
            grace_time -= 1
            await asyncio.sleep(1)
            wait = process.is_alive() and grace_time > 0

        if process.is_alive():
            self.logger.info(f"Killing service {name} ({process.pid})")
            os.kill(process.pid, 9)
            process.join()

    def shutdown(self, grace_time=10):
        self.logger.info(f"Shutting down services (grace time of {grace_time} seconds)")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._terminate_processes(self.running_services, grace_time))

