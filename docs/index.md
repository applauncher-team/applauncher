# Applauncher

Applauncher is a tool that helps you to reuse your code by sharing all default
functionalities among all of your projects. 

When you have several projects you realize that, in the beginning, you always write the
same stuff (the database connection handlers, the configuration loader...). And it is
very annoying. More than annoying, it is a problem because everytime you create a new project
you need to spend time and the components are not exactly the same (due little customizations).

In summary, if I usually use `mongodb` and `redis`, why not just create a thing that just 
provides me that? It's like using `libraries`, but in this case we import `features`.

This tool was developed with the following ideas in mind:

* **Not intrusive:** It does not tell you how to develop, but you should adapt your `main.py` (in the end applauncher is a launcher)
* **Simple:** Your applications are complex enough to add even more
* **Fast:** Applauncher should not steal your computing resources
* **Tested:** Applauncher is tested and relies on very tested libraries
* **Community:** Since many requirements are common (mysql, sentry...) any contribution can be enjoyed by anyone!




Bundleszzzzzz
