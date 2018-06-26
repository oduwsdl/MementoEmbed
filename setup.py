from setuptools import setup

# to get pylint to shut up
__appname__ = None
__appversion__ = None

# __appname__, __appversion__, and friends come from here
exec(open("mementoembed/version.py").read())

setup(
    name=__appname__.lower(),
    version=__appversion__,
    packages=[ __appname__.lower() ],
    include_package_data=True,
    install_requires=[
        'Pillow',
        'bs4',
        'cachecontrol',
        'dicttoxml',
        'filelock',
        'flask',
        'html5lib',
        'htmlmin',
        'httpcache',
        'justext',
        'lockfile',
        'readability-lxml',
        'redis',
        'requests',
        'requests_futures',
        'tldextract'
    ],
    scripts=['bin/fetch_surrogate_data'],
    test_suite="tests"
)
