from distutils.core import setup
setup(
  name='applauncher',
  packages=['applauncher'],
  version='1.011',
  description='App launcher and base environment',
  author='Alvaro Garcia Gomez',
  author_email='maxpowel@gmail.com',
  url='https://github.com/maxpowel/applauncher',
  download_url='https://github.com/maxpowel/applauncher/archive/master.zip',
  keywords=['environment', 'launcher'],
  classifiers=['Topic :: Adaptive Technologies', 'Topic :: Software Development', 'Topic :: System', 'Topic :: Utilities'],
  install_requires=['mapped_config', 'zope.event', 'Inject', 'six']
)
