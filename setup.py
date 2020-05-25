import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="python-imageseach-drov0",
    version="1.0.0",
    install_requires=requirements,
    author="Teodoro B. Mendes",
    author_email="teobmendes@gmail.com",
    description="A wrapper around openCv to perform image searching with support for async execution with Trio",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/herzog0/trio-python-imagesearch",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
