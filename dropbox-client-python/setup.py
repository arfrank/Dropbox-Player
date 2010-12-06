from setuptools import setup, find_packages

setup(name='dropbox-client',
      version='1.0',
      description='Dropbox REST API Client',
      author='Dropbox, Inc.',
      author_email='support@getdropbox.com',
      url='http://getdropbox.com/',
      packages=['dropbox'],
      install_requires = ['poster'],
     )

