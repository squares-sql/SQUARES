from setuptools import setup, find_packages

setup(
    name='tyrell',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'rpy2',
        'toml',
        'Click'
    ],
    entry_points={
        'console_scripts': [
            'run-tyrell=main:cli',
        ],
    },
)
