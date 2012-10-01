"""multiblob's distutils setup.py"""
from setuptools import setup

NAME = 'multiblob'
setup(
    name                 = NAME,
    version              = '1.0.0',
    author               = 'Alexander Kuehrmann, Tong Lin, Felix Stuermer',
    author_email         = '',
    description          = 'a competitive game for multitouch surfaces',
    packages             = ['multiblob'],
    package_data         = {
        'multiblob' : ['data/*', ],
        },
    include_package_data = True,
    install_requires     = [
        'setuptools', 
        'pyglet',
        'cogen',
        'lepton',
        ],
    entry_points         = """
    [console_scripts]
    multiblob = multiblob.client:main
    """,
    zip_safe             = False,
    )

