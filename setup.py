import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="awspolicy",
    version="0.0.3",
    author="Hailong Li",
    author_email="hailong.leon@gmail.com",
    description="A package that helps modifying AWS policies as an object",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/totoleon/AwsPolicy",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
