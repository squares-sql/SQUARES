from setuptools import setup, find_packages

setup(
    name='tyrell',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'rpy2',
        'lark-parser',
        'Click',
        'colorama'
    ],
    entry_points={
        'console_scripts': [
            'parse-spec=parse_spec:cli',
        ],
    },
)