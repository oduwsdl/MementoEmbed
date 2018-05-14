from setuptools import setup

setup(
    name='mementoembed',
    version='0.0.1a0',
    packages=['mementoembed'],
    include_package_data=True,
    install_requires=[
        'flask',
        'bs4',
        'html5lib',
        'archivenow',
        'requests',
        'readability-lxml'
    ],
    scripts=['bin/fetch_surrogate_data'],
    test_suite="tests"
)