from subprocess import call

packages = [
    "pyarrow",
    "numpy",
    "pandas",
    "openpyxl",
    "xlrd",
    "bs4",
    "requests",
    "matplotlib",
    "seaborn",
    "statsmodels",
    "scipy",
    "scikit-learn",
    "xgboost",
    "tqdm",
    "torch",
    "pyspark",
    "findspark",
    "keras",
    "notebook"
]

for package in packages:
    call(  # update all packages in shell
        "pip install " + package,
        shell=True
    )
