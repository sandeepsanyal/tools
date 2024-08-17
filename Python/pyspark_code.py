from pyspark import SparkContext, SparkConf
sc = SparkContext(conf=SparkConf().setAppName("test").setMaster("local"))

numbers = list(range(15))
rdd = sc.parallelize(numbers, 5)
rdd.glom().collect()


# From csv to pyspark
from pyspark.sql import SparkSession
import pyspark.pandas as ps
spark = SparkSession.builder.appName('name_your_app').getOrCreate()

sharepoint_path = r"/Users/wrngnfreeman/Library/CloudStorage/OneDrive-Personal/shared_projects"

psdf = ps.read_csv(  # reads as a pyspark.pandas.frame.DataFrame
    sharepoint_path + r"/Home Credit Default Risk/application_train.csv"
)



# From mysql to pyspark
from pyspark.sql import SparkSession

sc = SparkSession.builder \
    .appName('hcdr') \
    .config("spark.jars", "/usr/local/mysql-9.0.1-macos14-arm64/mysql-connector-j-9.0.0/mysql-connector-j-9.0.0.jar") \
    .getOrCreate()

source_df = sc.read.format('jdbc').options(  # reads as a pyspark.pandas.frame.DataFrame
    url='jdbc:mysql://localhost:3306/home_credit_default_risk',
    driver='com.mysql.cj.jdbc.Driver',
    dbtable='application_train',
    user='root',
    password='Pgl-9U5-a52').load()

