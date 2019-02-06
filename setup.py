from setuptools import setup, find_packages

# to get pylint to shut up
__appname__ = None
__appversion__ = None

# __appname__, __appversion__, and friends come from here
exec(open("mementoembed/version.py").read())

setup(
    name=__appname__.lower(),
    version=__appversion__,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'aiu',
        'bs4',
        'cairosvg',
        'dicttoxml',
        'flask',
        'html5lib',
        'htmlmin',
        'justext',
        'Pillow',
        'readability-lxml',
        'redis',
        'requests',
        'requests_cache',
        'tldextract'
    ],
    scripts=['bin/fetch_surrogate_data'],
    test_suite="tests"
)
