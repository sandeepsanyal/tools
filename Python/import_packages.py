from subprocess import call

packages = [
	"numpy",
	"pandas",
	"openpyxl",
	"xlrd",
	"wheel",
	"bs4",
	"requests",
	"matplotlib",
	"seaborn",
	"statsmodels",
	"scipy",
	"scikit-learn",
	"notebook"
]

for package in packages:
	call(  # update all packages in shell
	    "pip install " + package,
	    shell=True
	)