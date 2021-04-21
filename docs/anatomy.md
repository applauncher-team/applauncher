# Anatomy

Applauncher tends to be as more simple as possible. These are the main elements that you need to Know

## Bundle

A bundle is like a feature that `Applaucher` will offer to your application. For example, a functionality to
get a `mongodb` working in your application will contain the configuration information, the way to create a mongo
connection and how to provide this connection (usually by dependency injection). So you just import this bundle and
from your code you just request a mongo connection. You dont have to handle the initialization, configuration, closing
connections... You just write your code and `inject` all your dependencies.

A bundle looks something like this:

```python
from applauncher import Kernel, event
from pydantic import BaseModel
from dependency_injector import providers

class MysqlClient:
    def __init__(self, port: int, hostname: str, database: str):
        # This is a fake mysql cliente, but in should 
        # be an sqlalchmy connection or something like this
        pass
    
    def execute_query(self, query: str, params):
        pass

class MysqlConfig(BaseModel):
    port: int = 3306
    hostname: str
    database: str

class MysqlBundle:
    def __init__(self):
        # At this moment we are defining something like a bundle manifest
        
        # The configuration required for this bundle
        self.config_mapping = {
            "mysql": MysqlConfig
        }
        
        # Subscribe to some events
        self.event_listeners = [
            (event.ConfigurationReadyEvent, self.configuration_ready)
        ]

    def configuration_ready(self, event):
        config = event.configuration.mysql
        # In config we have the model `MysqlConfig` but populated
        
        # Here we define the dependency injection. We basically tell
        # what classes will be available to be injected and
        # the parameters needed by the container to instantiate it.
        # This example is using the factory injection (a new 
        # instance will created on every injection) but there are 
        # more options like singleton (when you want to share
        # the same instance) and more posibilites.
        self.injection_bindings = {
            MysqlClient: providers.Factory(
                MysqlClient,
                port=config.port,
                hostname=config.hostname,
                database=config.database
            )
        }

        # In this example, a service does not make sense but it 
        # should only `provide` a mysql connection. But since 
        # this is an example, we will configure one. 
        # [45] is the args and {} the kwargs provided to your
        # service function
        self.services = [
            ("my_service", self.service, [45], {"foo": "bar"})
        ]
        
    # This function will be executed in a separate process once
    # the kernel is ready (configuration loaded, dependency
    # container created...)
    def service(self, value, foo):
        from time import sleep
        while True:
            print("Value is", 45, foo)
            # Value is 45 bar
            sleep(1)

# Create the kernel providing the bundles (here only one, 
# but in a real application you use several bundles).
# The line `kernel.wait()` will wait until all `services`
# finishes and in case a signal (ctrl + c or kill) is
# received, it will try to finish all services gracefully.
with Kernel(bundles=[MysqlBundle()], environment="PROD") as kernel:
    kernel.wait()
```

## Service

It is your code. It can be a web application, your program that processes files, a threaded application... whatever you
want.

## Configuration mapping
If your bundle requires configuration, you have to provide to the application this fields. This mapping contains for example
the connection uri to your database. Applauncher will validate all these information and provides it to the bundle
so we can trust this information. 
The information can comes from a config file, environment variables... Your code does not really care, if just wants the values.
The validation process relies on [Pydantic](https://pydantic-docs.helpmanual.io/) so your validations will be very
fast and powerful.

## Events
Applauncher is event driven. You can raise events (information that is useful to other bundles) and subscribe to events
(in case you want to get notified about something). For example, `kafka_bundle` will raise events on every message
received so your application (and any other bundle) will subscribe to this event.

## Dependency injection
This is the mechanism used to provide and ask for services. Your bundle provide things (like a database connection)
to be injected and other bundles (like your application) can inject them. The dependency injection feature relies on 
 [Dependency Injector](https://python-dependency-injector.ets-labs.org/), check its documentation to see all amazing
features.

## Kernel
The kernel is just the thing that prepares the environment. Basically it loads the configuration and initialize the
bundles and the very basic features (like the dependency injector container or the event system). The kernel also
send `events` to notify these steps (when the configuarion is ready, when the application is fully loaded or when
the bundles should shutdown because a sigterm was received). But there is nothing `smart` in this kernel, it will not
take the control of your application or any unexpected thing at all. The hearth will always be your application.