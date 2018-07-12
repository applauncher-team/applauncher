from setuptools import setup

with open('requirements.txt') as fp:
    install_requires = fp.read()

setup(
    name='applauncher',
    packages=['applauncher'],
    version='1.41',
    description='App launcher and base environment',
    author='Alvaro Garcia Gomez',
    author_email='maxpowel@gmail.com',
    url='https://github.com/applauncher-team/applauncher',
    download_url='https://github.com/applauncher-team/applauncher/archive/master.zip',
    keywords=['environment', 'launcher', 'kernel', 'event', 'base'],
    classifiers=['Topic :: Adaptive Technologies', 'Topic :: Software Development', 'Topic :: System',
                 'Topic :: Utilities'],
    install_requires=install_requires
)
