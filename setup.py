from setuptools import find_packages, setup

setup(
    author="Rizzo Elisa, Chinellato Marco",
    author_email="884784@stud.unive.it, 886217@stud.unive.it",
    name='DaisPCTO',
    version='0.0.5',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask', 'flask_login', 'flask_wtf', 'psycopg2', "sqlalchemy", "flask_bcrypt", "flask_bootstrap", "flask_admin", 'Flask-OAuth'
    ],
)
