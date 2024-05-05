import setuptools
import os

# Install dependencies
os.system("pip install git+https://github.com/openai/CLIP.git")
os.system("pip install sentence-transformers")
os.system("pip install torch")
os.system("pip install pillow")
os.system("pip install request")
os.system("pip install numpy")
os.system("pip install fuzzywuzzy")
os.system("pip install python-Levenshtein")
os.system("pip install sentence-transformers")
os.system("pip install sentence-transformers")
os.system("pip install sentence-transformers")
setuptools.setup(
    name="FuzzyZSIC",
    version="1.0",
    author="Abir",
    description="Fuzzy Zeroshot Image Classification",
    url="https://github.com/TheMAbir/FuzzyZSIC",
    packages=setuptools.find_packages(),
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: MIT License",
        "Operating System :: OS Independent",
    ],
)
