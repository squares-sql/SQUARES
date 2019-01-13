from setuptools import setup, find_packages

install_dependencies = [
    'Click',
    'colorama',
    'sexpdata',
    'z3-solver'
]
develop_dependencies = [
    'mypy',  # for type checking
    'rpy2',  # for Morpheus. TODO: This should really belong to the client package
    'lark-parser',  # for parsing
    'sphinx',  # for documentation generation
]

setup(
    name='tyrell',
    version='0.1dev',
    packages=find_packages(),
    license='LICENSE.txt',
    description='Deduction-based synthesis framework',
    install_requires=install_dependencies,
    extras_require={
        'dev': develop_dependencies
    },
    entry_points={
        'console_scripts': [
            'parse-tyrell-spec=tyrell.parse_tyrell_spec:cli',
        ],
    },
)
