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
        'aiu==0.1.0a1',
        'Brotli==1.0.4',
        'bs4==0.0.1',
        'cairosvg==2.3.0',
        'dicttoxml==1.7.4',
        'flask==1.0.2',
        'html5lib==1.0.1',
        'htmlmin==0.1.12',
        'imageio==2.5.0',
        'justext==2.2.0',
        'Pillow==5.2.0',
        'python-datauri==0.2.8',
        'python-magic==0.4.15',
        'readability-lxml==0.7',
        'redis==3.0.1',
        'redis_namespace==3.0.1.1',
        'requests>=2.20.0',
        'requests_cache==0.4.13',
        'requests-futures==0.9.9',
        'sphinx==1.8.4',
        'summa==1.2.0',
        'tldextract==2.2.0',
        'wordcloud==1.6.0'
    ],
    test_suite="tests.unit"
)
