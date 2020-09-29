from subprocess import call

packages = [
    "numpy",
    "pandas",
    "sqlalchemy",
    "pyodbc"
    "openpyxl",
    "xlrd",
    "savReaderWriter",
    "pyreadstat",
    "wheel",
    "bs4",
    "requests",
    "matplotlib",
    "seaborn",
    "statsmodels",
    "scipy",
    "scikit-learn",
    "tqdm",
    "notebook",
    "tensorflow",
    "kmeans",
    "kmodes"
]

for package in packages:
    call(  # update all packages in shell
        "pip install " + package,
        shell=True
    )
