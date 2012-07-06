import os
import sys

from setuptools import setup, find_packages, Command

here = os.path.abspath(os.path.dirname(__file__))


def _read(path):
    with open(path) as f:
        data = f.read()
    f.close()

    return data

README = ''
CHANGES = ''

requires = [
    'pyramid'
    , 'gevent'
    , 'gevent-socketio'
    , 'pyramid_socketio'
    , 'redis'
]

if sys.version_info[:3] < (2, 5, 0):
    requires.append('pysqlite')


class PyTest(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import subprocess
        errno = subprocess.call('py.test')
        raise SystemExit(errno)

setup(name='chatter3',
      version='0.0',
      description='chatter3',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web wsgi bfg pylons pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='chatter3',
      install_requires=requires,
      entry_points="""\
      [paste.app_factory]
      main = chatter3:main
      """,
      paster_plugins=['pyramid'],
      )
