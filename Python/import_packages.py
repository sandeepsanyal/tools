from subprocess import call

packages = [
    "numpy",
    "pandas",
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
    "kmeans",
    "kmodes",
    "xgboost",
    "tqdm",
    "notebook",
    "tensorflow",
    "pyspark",
    "findspark"
]

for package in packages:
    call(  # update all packages in shell
        "python3 -m pip install " + package,
        shell=True
    )
