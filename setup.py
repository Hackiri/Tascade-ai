from setuptools import setup, find_packages

# Function to read requirements from requirements.txt
def parse_requirements(filename):
    """Load requirements from a pip requirements file."""
    with open(filename, 'r') as f:
        lineiter = (line.strip() for line in f)
        return [line for line in lineiter if line and not line.startswith("#")]

setup(
    name='tascade-ai',
    version='0.1.0',
    author='Your Name / Windsurf Engineering Team',
    author_email='your.email@example.com',
    description='An AI-powered task management system for project planning and execution.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='(Your project URL if you have one, e.g., a GitHub repo)',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True, # To include non-code files specified in MANIFEST.in (if you create one)
    install_requires=parse_requirements('requirements.txt'),
    entry_points='''
        [console_scripts]
        tascade=cli.main:cli
    ''',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Version Control :: Git',
        'Topic :: Text Editors :: Integrated Development Environments (IDE)'
    ],
    python_requires='>=3.8',
)
