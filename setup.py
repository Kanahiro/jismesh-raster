from setuptools import setup, find_packages

setup(
    name="jismesh-raster",
    version="0.2.0",
    description="Generate raster from jismesh-based data. jismesh=Japan Standard Mesh",
    author="Kanahiro Iguchi",
    license="MIT",
    url="https://github.com/Kanahiro/jismesh-raster",
    packages=find_packages(),
    install_requires=["jismesh", "pandas", "Pillow"],
    entry_points={
        "console_scripts": [
            "jismesh-raster=jismesh_raster.rasterize:main",
        ]
    }
)
