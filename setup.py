from setuptools import setup, find_packages

setup(
    name="gevent-socketio",
    version="0.3.5-beta",
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
    install_requires=("gevent-websocket",),
    setup_requires=("versiontools >= 1.7",),
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
)
