from setuptools import setup

exec(open("mementoembed/version.py").read())

setup(
    name=__appname__.lower(),
    version=__appversion__,
    packages=[ __appname__.lower() ],
    include_package_data=True,
    install_requires=[
        'flask',
        'bs4',
        'html5lib',
        'requests',
        'readability-lxml',
        'Pillow',
        'tldextract',
        'httpcache',
        'lockfile',
        'justext',
        'htmlmin',
        'dicttoxml',
        'cachecontrol',
        'filelock',
        'requests_futures'
    ],
    scripts=['bin/fetch_surrogate_data'],
    test_suite="tests"
)
