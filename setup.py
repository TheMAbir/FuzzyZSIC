import setuptools
import os

# Install dependencies
os.system("pip install git+https://github.com/openai/CLIP.git")
os.system("pip install sentence-transformers")

setuptools.setup(
    name="FuzzyZSIC",
    version="1.0",
    author="Abir",
    description="Fuzzy Zeroshot Image Classification",
    url="https://github.com/TheMAbir/FuzzyZSIC",
    packages=setuptools.find_packages(),
    install_requires=[
        "torch",
        "clip",
        "Pillow",
        "requests",
        "numpy",
        "sentence-transformers",
        "fuzzywuzzy",
        "python-Levenshtein"
    ],
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
