from setuptools import find_packages, setup


def get_requirements():
    with open("requirements.txt", "r") as fp:
        reqs = [req.strip() for req in fp.readlines()]
    return reqs


setup(
    name="SCOT",
    version="4.2.0",
    description="Sandia Cyber Omni Tracker Server",
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=get_requirements(),
)
