import math
import psutil
from pyspark.sql import SparkSession

machine_cores = psutil.cpu_count(logical=True)  # total logical cores on this machine; cross-platform (Mac/Linux/Windows)
machine_ram_gb = psutil.virtual_memory().total / 1024**3  # total physical RAM on this machine; cross-platform (Mac/Linux/Windows)

# Tune these for the machine you're running on.
NUM_CORES = math.ceil(machine_cores * 0.8)  # worker threads Spark uses locally; match to your CPU's performance cores
DRIVER_MEMORY = f"{math.floor(machine_ram_gb * 0.8)}g"  # JVM heap for the driver process
SHUFFLE_PARTITIONS = NUM_CORES * 2  # partitions used after a shuffle (join/groupBy); default of 200 is overkill for a single machine, so scale it off core count instead


def get_spark_session(app_name):
    return (
        SparkSession.builder
        .appName(app_name)  # name shown in the Spark UI/logs, one per script
        .master(f"local[{NUM_CORES}]")  # run Spark in-process using NUM_CORES threads (no cluster)
        .config("spark.driver.memory", DRIVER_MEMORY)
        .config("spark.sql.shuffle.partitions", SHUFFLE_PARTITIONS)
        .getOrCreate()  # reuse the active session if one already exists, else create it
    )
