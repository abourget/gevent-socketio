import os

from setuptools import setup
from setuptools import find_packages
from setuptools.command.test import test as TestCommand

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))

def get_reqs(*fns):
    lst = []
    for fn in fns:
        for package in open(os.path.join(CURRENT_DIR, fn)).readlines():
            package = package.strip()
            if not package:
                continue
            lst.append(package.strip())
    return lst

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        pytest.main(self.test_args)

setup(
    name="gevent-socketio",
    version="0.3.6",
    description=(
        "SocketIO server based on the Gevent pywsgi server, "
        "a Python network library"),
    author="Jeffrey Gelens",
    author_email="jeffrey@noppo.pro",
    maintainer="Alexandre Bourget",
    maintainer_email="alex@bourget.cc",
    license="BSD",
    url="https://github.com/abourget/gevent-socketio",
    download_url="https://github.com/abourget/gevent-socketio",
    install_requires=get_reqs('pip-requirements.txt'),
    setup_requires=('versiontools >= 1.7'),
    cmdclass = {'test': PyTest},
    tests_require=get_reqs('pip-requirements-test.txt'),
    packages=find_packages(exclude=["examples", "tests"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
    ],
    entry_points="""

    [paste.server_runner]
    paster = socketio.server:serve_paste

    """,
)
