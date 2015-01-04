from distutils.core import setup

setup(
    name='nativeconfig',
    version='1.0',
    py_modules=['nativeconfig'],
    url='https://github.com/GreatFruitOmsk/nativeconfig',
    license='MIT',
    author='Ilya Kulakov',
    author_email='kulakov.ilya@gmail.com',
    description='Cross-platform python module to store application config via'
                'native subsystems like Windows Registry or NSUserDefaults.'
)
