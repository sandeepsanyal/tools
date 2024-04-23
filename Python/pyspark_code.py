from pyspark.sql import SparkSession

spark = SparkSession.builder.appName('pyspark-by-examples').getOrCreate()

import pyspark.pandas as ps

sharepoint_path = r"/Users/wrngnfreeman/Library/CloudStorage/OneDrive-Personal/shared_projects"

psdf = ps.read_csv(
    sharepoint_path + r"/Home Credit Default Risk/application_train.csv"
)

psdf.groupby(
    by=["TARGET"]
).agg(
    {
        "AMT_INCOME_TOTAL": "mean",
        "AMT_CREDIT": "mean"
    }
)