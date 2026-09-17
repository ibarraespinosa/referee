from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="referee-pdf",
    version="1.0.0",
    author="Sergio Ibarra-Espinosa",
    author_email="zergioibarra@gmail.com",
    description="Acrobat-like PDF Annotation & Review Editor for Ubuntu/Linux",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ibarraespinosa/referee",
    project_urls={
        "Bug Tracker": "https://github.com/ibarraespinosa/referee/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Environment :: X11 Applications :: Qt",
        "Topic :: Multimedia :: Graphics :: Viewers",
        "Topic :: Text Processing :: Markup",
    ],
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "PyQt5>=5.15.0",
        "pymupdf>=1.24.0",
    ],
    entry_points={
        "console_scripts": [
            "referee=referee.app:main",
            "pdf-reviewer=referee.app:main",
        ],
    },
)
