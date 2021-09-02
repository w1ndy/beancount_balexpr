from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setup(
    name = 'beancount_balexpr',
    packages = find_packages(),
    python_requires = '>=3.3',
    version = '0.4.0',
    license = 'MIT',
    description = 'Check balances against simple expressions combining multiple accounts in beancount',
    long_description = long_description,
    long_description_content_type = 'text/markdown',
    author = 'Di Weng',
    author_email = 'mystery.wd@gmail.com',
    url = 'https://github.com/w1ndy/beancount_balexpr',
    keywords = [ 'beancount' ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
