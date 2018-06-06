from setuptools import setup
setup(
    name='applauncher',
    packages=['applauncher'],
    version='1.3',
    description='App launcher and base environment',
    author='Alvaro Garcia Gomez',
    author_email='maxpowel@gmail.com',
    url='https://github.com/applauncher-team/applauncher',
    download_url='https://github.com/applauncher-team/applauncher/archive/master.zip',
    keywords=['environment', 'launcher'],
    classifiers=['Topic :: Adaptive Technologies', 'Topic :: Software Development', 'Topic :: System',
                 'Topic :: Utilities'],
    install_requires=['mapped_config', 'mediator', 'Inject']
)
