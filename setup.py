import setuptools

setuptools.setup(
    name='response_mocker',
    version='1.0.2',
    description='A simple mocking library for Requests',
    url='https://github.com/menge101/response_mocker',
    author='Nathan Menge',
    author_email='nathan.menge@gmail.com',
    license='MIT',
    packages=setuptools.find_packages(exclude=['tests*']),
    zip_safe=False,
    install_requires=[],
    test_suite="tests"
)
