from setuptools import find_packages, setup

setup(
    name='dfa',
    version='0.1.3',
    description='Python library for modeling DFAs.',
    url='https://github.com/mvcisback/dfa',
    author='Marcell Vazquez-Chanlatte',
    author_email='marcell.vc@eecs.berkeley.edu',
    license='MIT',
    install_requires=[
        'attrs',
        'funcy',
    ],
    packages=find_packages(),
)
