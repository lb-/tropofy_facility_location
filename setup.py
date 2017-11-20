from setuptools import setup, find_packages

requires = [
    'tropofy',
    'pulp==1.6.2',
]

setup(
    name='tropofy-facility-location',
    version='1.0',
    description='This is a Tropofy example package',
    author='Tropofy',
    url='http://www.tropofy.com',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requires,
)
