# Bootstrap setuptools installation.
try:
    import pkg_resources
    pkg_resources.require("setuptools >= 0.7")
except:
    from ez_setup import use_setuptools
    use_setuptools()

from setuptools import setup, find_packages

setup(
    name='gwcelery',
    version='0.0.1',
    author='Leo Singer',
    author_email='leo.singer@ligo.org',
    description='Hipster pipeline for annotating LIGO events',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet',
        'Topic :: Scientific/Engineering :: Astronomy'
    ],
    license='GPL-2+',
    install_requires=[
        'celery[redis]',
        # See https://github.com/steinitzu/celery-singleton/pull/1
        # 'celery_singleton',
        'ligo-gracedb',
        'ligo-lvalert'
    ],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'gwcelery = gwcelery:start'
        ]
    }
)
