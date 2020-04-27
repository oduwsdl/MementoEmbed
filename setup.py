import os
from setuptools import setup, find_packages
from os import path

# to get pylint to shut up
__appname__ = None
__appversion__ = None

# __appname__, __appversion__, and friends come from here
exec(open("mementoembed/version.py").read())

here = path.abspath(path.dirname(__file__))

print("here is.... {}".format(here))
print("directory contents: {}".format(os.listdir(here)))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name=__appname__.lower(),
    version=__appversion__,
    packages=find_packages(),
    long_description_content_type="text/markdown",
    long_description=long_description,
    url='https://github.com/oduwsdl/MementoEmbed',
    author='Shawn M. Jones',
    author_email='jones.shawn.m@gmail.com',
    license='MIT',
    include_package_data=True,
    install_requires=[
        'aiu',
        'Brotli',
        'bs4',
        'cairosvg',
        'dicttoxml',
        'flask',
        'html5lib',
        'htmlmin',
        'imageio',
        'ImageHash',
        'justext',
        'Pillow',
        'python-datauri',
        'python-magic',
        'readability-lxml',
        'redis',
        'redis_namespace',
        'requests',
        'requests_cache',
        'requests-futures',
        'sphinx',
        'summa',
        'tldextract',
        'wordcloud'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Text Processing',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
    ],
    test_suite="tests.unit",
    zip_safe=True,
    keywords='webarchives memento embeds nlp'
)
