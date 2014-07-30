from setuptools import setup, find_packages
import os

version = '0.0.1'

setup(
    name='doris_erpnext',
    version=version,
    description='Doris ERPNext Extensions',
    author='Doris',
    author_email='anand@erpnext.com',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=("frappe",),
)
