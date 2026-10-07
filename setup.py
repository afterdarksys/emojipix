from setuptools import setup

setup(
    name='emojipix',
    version='0.1.0',
    py_modules=['emojipix'],
    install_requires=[
        'emoji',
        'rich'
    ],
    entry_points={
        'console_scripts': [
            'emojipix=emojipix:main',
        ],
    },
    description="A supercharged CLI tool for converting text and emojis",
    author="ryan",
)
