from distutils.core import setup

setup(
    name='python-gospel-library',
    version='1.0.0dev',
    packages=['gospellibrary',],
    license='MIT',
    description='Python package that parses Gospel Library content.',
    long_description=open('README.md').read(),
    install_requires=[
        'requests==2.4.3',
        'reprutils==1.0',
    ],
)
