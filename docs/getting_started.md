# Getting started

Applauncher tends to be as more simple as possible. These are the main elements that you need to Know

## Bundle

A bundle is like a `functionality` that `Applaucher` will offer to your application. For example, a functionality to
get a `mongodb` working in your application will contain the configuration information, the way to create a mongo
connection and how to provide this connection (usually by dependency injection). So you just import this bundle and
from your code you just request a mongo connection. You dont have to handle the initialization, configuration, closing
connections... You just write your code and `inject` all your dependencies.

## Service

It is your code. It can be a web application, your program that processes files, a threaded application... whatever you
want.

## Configuaration mapping


## Events


