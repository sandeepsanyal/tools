from subprocess import call

packages = [
    "numpy",
    "pandas",
    "sqlalchemy",
    "pyodbc",
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
    "pyspark[sql]",
    "pyspark[pandas_on_spark] plotly"
]

for package in packages:
    call(  # update all packages in shell
        "pip install " + package,
        shell=True
    )
