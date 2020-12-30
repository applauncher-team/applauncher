# Kernel lifecycle

There is a little lifecycle process since you run python until the application finishes, in order the events are:
* ConfigurationReady
* InjectorReady
* KernelReady
* KernelShutdown

Your main application will run after the event `KernelReady`

## ConfigurationReadyEvent
This event will provide you the configuration parsed and validated. In case of any error, the information will
be displayed specifying in a friendly way the errors to fix. Used when a `bundle` needs this to provide some service
to `inject`, like a database connection.

## InjectorReady
At this point everything is ready but until the application code can run, this event allows to do a last thing. This
is useful when a bundle needs another bundle. It's not very common because `dependency injection` solves most of the
cases but you sometimes you need it. We can think this event like a `pre run`.

## KernelReady
At this point the application is fully started. Is when the services are started and here is when your code will
start running. Here you can inject or do whatever you want

## KernelShutdown
When a `ctrl + c` or `sigterm` is received, the kernel will raise this event. The bundles subscribed to this event
should prepare the shutdown process (close connection), and your service will receive the signal to start the shutdown
process. By default, there will be grace time of 10 seconds. If any code is not able to be stopped in this grace time
period, it will be killed. Anyway, resending the sigterm signal will kill the processes too.