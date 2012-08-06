import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = ''#open(os.path.join(here, 'README.md')).read()
CHANGES = ''#open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'tweetstream'
]

setup(name='twitterstream'
      , version='0.1'
      , description='Streaming twitter updates over Socket.IO'
      , long_description=README + '\n\n' +  CHANGES
      , classifiers=[
            'Intended Audience :: Developers'
            , 'License :: OSI Approved :: BSD License'
            , 'Operating System :: OS Independent'
            , 'Programming Language :: Python'
            , 'Topic :: Internet :: WWW/HTTP :: Dynamic Content'
            , 'Topic :: Software Development :: Libraries :: Python Modules'
      ]
      , author='Philip Neustrom'
      , author_email='philipn@gmail.com'
      , url='https://github.com/abourget/gevent-socketio'
      , license='BSD'
      , packages=find_packages()
      , include_package_data=True
      , zip_safe=False
      , install_requires=requires
      , tests_require=requires
)

