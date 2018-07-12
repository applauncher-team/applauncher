App launcher
=============
[![Build Status](https://travis-ci.org/applauncher-team/applauncher.svg?branch=master)](https://travis-ci.org/applauncher-team/applauncher)

How to install
---------------
pip install applauncher

What is this?
-------------
A base environment for python applications. When you want to build an applications, you have to create your own access
to database, a module loading system and maybe other cools things like dependency injection. This project expose all of
this to your application so you only have to focus in your application.

How it works
------------
This library just provides a simple kernel which provides you anything you want. Do you want the database? Ask for it.
You only have to say to the kernel how to instance these things. The way you provide this features to your application
is through "bundles". In the following sections we will see how does it work.

Launcher script
---------------
Every application needs to be launch. You just need to provide the bundles you want to load (your application implements
a bundle)

```python
from applauncher.kernel import Environments, Kernel
import rest_api.bundle
import myweb.bundle

bundle_list = [
    rest_api.bundle.RestApiBundle(),
    myweb.bundle.WebBundle(),
]

with Kernel(Environments.DEVELOPMENT, bundle_list) as kernel:
   kernel.wait()

```
In the example above, we loaded just 2 bundles. The first one 'rest_api.bundle.RestApiBundle()' provides a
webserver. In this case, this bundle uses flask so once you load this bundle you have a flask application ready to use.
The second one 'myweb.bundle.WebBundle()' is just my application. In this case it just provides the controllers, views
and all this kind of web stuff. In the next sections I will explain you the structure of a bundle.

If you dont use the 'with' clause, the shutdown events will not be called

Bundle structure
----------------
A bundle is a class that describes how to use some software. For example, my api rest bundle links the kernel with flask.
It's just a wrapper!

```python

from applauncher.kernel import KernelReadyEvent, Configuration, KernelShutdownEvent, Kernel, InjectorReadyEvent
import inject

class RestApiBundle(object):
    def __init__(self):
        # The configuration of this bundle. Just an schema about the data required. The kernel will use it to read
        # configuration files, check that everything is fine and provide it to your application.
        self.config_mapping = {
            "rest_api": {
                "use_debugger": True,
                "port": 3003

            }
        }
        # Other bundles will populate this array with their controllers
        self.blueprints = [index_blueprint]
        # This bundle provides an "object" to allow other bundles add new controllers. Its like this bundle "publish" this object
        # to the kernel and other bundles request this object from the kernel.
        self.injection_bindings = {
            ApiBlueprints: self.blueprints
        }
        # This is done with dependency injection which is a very important step. When all dependencies are ready, an
        # event is thrown (there are more type of events of course) so you have to subscribe if you want to be notified
        self.event_listeners = [
            (KernelReadyEvent, self.kernel_ready),
            (KernelShutdownEvent, self.kernel_shutdown)
        ]
    
    @inject.params(kernel=Kernel)
    def kernel_ready(self, event, kernel):
        # In this case I am only interested when the kernel is ready (the last step, when dependency injection,
        # configuration... are loaded)
        # Just request the kernel to run your server as a service (don't create threads manually)
        kernel.run_service(self.start_server)

    # Start the server. See how I inject the configuration. The kernel was in charge to load the configuration and
    # prepare everything else
    @inject.params(config=Configuration)
    def start_sever(self, config):
        app = Flask("MyApi")
        # As we are executing this after all other bundles are loaded (because of KernelReadyEvent), all other bundles
        # should have appended his blueprints into out blueprints array.
        for blueprint in self.blueprints:
            # Just register it into flask
            app.register_blueprint(blueprint)

        # Finally run the server. Its like a normal application but the kernel simplified our work, in this case by
        # providing the configuration and communication with other bundles
        app.run(use_debugger=False, port=config)

     def kernel_shutdown(self, event):
        # Do here whatever is needed to stop your server

```


Now the application bundle

```python
#Flask blueprint and an example controller
my_blueprint = Blueprint(
    'myApp', __name__
)


@mp_blueprint.route("/lol", methods=['GET'])
def my_app_get_index():
    return jsonify({"foo": "bar"})


# The bundle
class WebBundle(object):
    def __init__(self):
        # I dont need any configuration so I simply ignore the field config_mapping
        self.event_listeners = [
            (InjectorReadyEvent, self.event_listener)
        ]

    def event_listener(self, event):
        # When the injection is ready, we request the blueprints array
        # provided by the WebApiBundl
        bp = inject.instance(ApiBlueprints)
        bp.append(my_blueprint)
        # that's all, later the WebApiBundle will run this blueprint
            
```

By default the configuration is at 'config/config.yml' and 'config/parameters.yml' but
you can specify the location in the Kernel constructor.

The configuration files for this example:

config.yml
```yml
rest_api:
    port: {rest_api_port}
    
```

parameters.yml
```yml
rest_api_port: 3003

```

For more information about the configuration files, check [mapped_config](https://github.com/maxpowel/mapped_config) 

