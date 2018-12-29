from setuptools import setup, find_packages

setup(
    name='tyrell',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'mypy',  # for type checking
        'rpy2',
        'lark-parser',
        'Click',
        'colorama',
        'sexpdata',
        'z3-solver'
    ],
    entry_points={
        'console_scripts': [
            'parse-spec=parse_spec:cli',
        ],
    },
)
