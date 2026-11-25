# --- Environment setup (env vars, Hadoop classpath, findspark) ---
# Stdlib/third-party imports needed below; pyspark itself is deliberately imported later, after findspark.init(), since findspark is what makes pyspark importable in the first place.
import json
import math
import os
import re
import subprocess
import urllib.request
import warnings

import psutil
from dotenv import load_dotenv

# Load env vars from a .env file (JAVA_HOME, SPARK_HOME, HADOOP_HOME, SPARK_MASTER_URL, etc.)
load_dotenv()

# Fail fast if the required Java/Spark/Hadoop paths are not configured.
required_vars = ["JAVA_HOME", "SPARK_HOME", "HADOOP_HOME"]
missing = [v for v in required_vars if not os.environ.get(v)]
if missing:
    raise EnvironmentError(f"Missing required environment variables in .env: {missing}")

# Ask the local Hadoop install for its classpath and expose it to Spark so Spark can find Hadoop's jars at runtime.
try:
    hadoop_classpath = subprocess.check_output(
        [os.path.join(os.environ["HADOOP_HOME"], "bin", "hadoop"), "classpath"]
    ).decode().strip()
except (OSError, subprocess.CalledProcessError) as exc:
    raise EnvironmentError(f"Could not run '{os.path.join(os.environ['HADOOP_HOME'], 'bin', 'hadoop')} classpath' — check that HADOOP_HOME points to a valid Hadoop install") from exc
os.environ["SPARK_DIST_CLASSPATH"] = hadoop_classpath

# findspark makes the pyspark package importable by locating SPARK_HOME and adding its python/ and py4j zips to sys.path — it must run before pyspark is imported below, and after SPARK_HOME is validated above.
import findspark
findspark.init(os.environ["SPARK_HOME"])

from pyspark import SparkContext
from pyspark.sql import SparkSession

# --- Determine master URL FIRST; everything else depends on it ---
SPARK_MASTER_URL = os.environ.get("SPARK_MASTER_URL", "")

# Fallback figures used when there is no reachable cluster (i.e. running local[N]); cores are logical (hyperthreads counted) and RAM is what's currently free, not total installed, so sizing shrinks if other apps are already using memory. psutil.cpu_count() can return None on platforms where the OS doesn't report a core count, hence the "or 1" fallback.
local_machine_cores = psutil.cpu_count(logical=True) or 1
local_machine_ram_gb = psutil.virtual_memory().available / 1024**3


# --- Cluster/local resource detection ---
def _get_live_cluster_resources(master_url: str) -> tuple[int | None, int | None]:
    """
    Query the Spark Master REST API for ALIVE workers.

    Parameters
    ----------
    master_url : str
        Spark master URL, e.g. "spark://host:7077". Only standalone-master URLs are supported; anything else short-circuits to (None, None).

    Returns
    -------
    tuple[int | None, int | None]
        (total_cores, total_memory_mb) summed across ALIVE workers, or (None, None) if the URL isn't a standalone spark:// master or the master's REST API can't be reached.

    Notes
    -----
    Only the first host in `master_url` is probed via HTTP, so an HA standalone cluster configured with multiple comma-separated masters (spark://host1:port1,host2:port2) is only reachable through this function when host1 happens to be the current leader.
    total_memory_mb reflects each ALIVE worker's configured capacity (the master's "memory" field), not memory currently free — it does not account for executors already running on that worker for other applications.
    """
    match = re.match(r"spark://([^:]+):", master_url)
    if not match:
        return None, None
    host = match.group(1)
    try:
        with urllib.request.urlopen(f"http://{host}:8080/json/", timeout=5) as resp:
            data = json.load(resp)
        alive_workers = [w for w in data.get("workers", []) if w.get("state") == "ALIVE"]
        total_cores = sum(w.get("cores", 0) for w in alive_workers)
        total_memory_mb = sum(w.get("memory", 0) for w in alive_workers)
        return total_cores or None, total_memory_mb or None
    except Exception:
        return None, None


# --- Resolve cores/memory to use for local[N] fallback and driver sizing ---
if SPARK_MASTER_URL.startswith("spark://"):
    total_cluster_cores, total_cluster_memory_mb = _get_live_cluster_resources(SPARK_MASTER_URL)
    total_cluster_cores = total_cluster_cores or local_machine_cores
    total_cluster_memory_gb = (total_cluster_memory_mb / 1024) if total_cluster_memory_mb else local_machine_ram_gb
else:
    total_cluster_cores = local_machine_cores
    total_cluster_memory_gb = local_machine_ram_gb

# Use all available cores (no headroom reserved) for local[N] parallelism and as the live_cores fallback below.
NUM_CORES = total_cluster_cores
# Floor at 2g so a busy machine can't produce a "0g"/"1g" driver that dies mid-job.
# Cap at 4g since the driver rarely needs more for non-production analysis work.
DRIVER_MEMORY = f"{min(4, max(2, math.floor(total_cluster_memory_gb * 0.8)))}g"

# If no master was configured, fall back to a local cluster sized to this machine's cores.
if not SPARK_MASTER_URL:
    SPARK_MASTER_URL = f"local[{NUM_CORES}]"

# Extra JDBC/Excel connector jars made available to every SparkSession; the spark-excel package's _2.13 suffix must match this Spark install's Scala build version (2.12 vs 2.13) or dependency resolution will fail at session-creation time.
SPARK_PACKAGES = [
    "org.postgresql:postgresql:42.7.11",  # postgresql connector
    "org.xerial:sqlite-jdbc:3.46.1.3",  # sqlite connector
    "dev.mauch:spark-excel_2.13:4.0.0_0.31.2",  # excel connector
]

# Driver memory must be set before the JVM launches, so it's passed via PYSPARK_SUBMIT_ARGS rather than through SparkConf; spark.driver.memory has no effect if set after the JVM has already started.
if "PYSPARK_SUBMIT_ARGS" not in os.environ:
    os.environ["PYSPARK_SUBMIT_ARGS"] = f"--driver-memory {DRIVER_MEMORY} pyspark-shell"
else:
    warnings.warn(f"PYSPARK_SUBMIT_ARGS is already set, so the computed DRIVER_MEMORY ({DRIVER_MEMORY}) will NOT be applied to the driver JVM — the existing value takes effect instead: {os.environ['PYSPARK_SUBMIT_ARGS']!r}")


# --- SparkContext lifecycle helpers (recover from a dead context left over from a previous run) ---
def _context_is_alive(sc: SparkContext | None) -> bool:
    """
    Check whether a SparkContext's underlying JVM context is still running.

    Parameters
    ----------
    sc : pyspark.SparkContext | None
        The context to check, or None.

    Returns
    -------
    bool
        True only if sc is not None and its underlying JVM SparkContext hasn't been stopped.
    """
    if sc is None:
        return False
    try:
        return not sc._jsc.sc().isStopped()
    except Exception:
        return False


def _clear_stale_context() -> None:
    """
    Clear PySpark's cached SparkContext/SparkSession singleton references if they point to a dead context.

    If a previous run left behind a dead SparkContext (e.g. after a kernel crash or JVM death), PySpark's cached singleton references stop getOrCreate() from starting a fresh one. This resets those references so a new session can be built.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    sc = getattr(SparkContext, "_active_spark_context", None)
    if sc is None or _context_is_alive(sc):
        return
    for attr in ("_instantiatedSession", "_activeSession", "_active_session"):
        if hasattr(SparkSession, attr):
            try:
                setattr(SparkSession, attr, None)
            except Exception:
                pass
    try:
        if SparkContext._gateway is not None:
            SparkContext._gateway.shutdown()  # best-effort; avoids orphaning the JVM subprocess if it's actually still alive
        SparkContext._active_spark_context = None
        SparkContext._gateway = None
        SparkContext._jvm = None
    except Exception:
        pass


# --- Public API ---
def get_spark_session(app_name: str) -> SparkSession:
    """
    Build (or fetch) a configured SparkSession, sized to the resolved cluster/local resources.

    Cleans up any dead context left over from a previous run, creates the session with fixed reliability/connector settings plus the module-level driver memory and master URL, then sets shuffle partitions and exposes cluster.total.cores / cluster.total.memory.gb on the session config based on a fresh read of live cluster resources.

    Parameters
    ----------
    app_name : str
        Name to register the Spark application under (shown in the Spark UI).

    Returns
    -------
    pyspark.sql.SparkSession
        A ready-to-use Spark session.

    Raises
    ------
    RuntimeError
        If SparkSession.builder.getOrCreate() fails, most likely because the driver JVM from a previous run is dead.
    """
    _clear_stale_context()

    try:
        spark = (
            SparkSession.builder
            .appName(app_name)
            .master(SPARK_MASTER_URL)
            .config("spark.driver.memory", DRIVER_MEMORY)
            .config("spark.network.timeout", "900s")
            .config("spark.executor.heartbeatInterval", "120s")
            .config("spark.rpc.askTimeout", "900s")
            .config("spark.shuffle.io.maxRetries", "10")
            .config("spark.shuffle.io.retryWait", "60s")
            .config("spark.reducer.maxReqsInFlight", "1")
            .config("spark.executor.memory", "3g")  # fixed regardless of detected cluster/local size — NUM_CORES/DRIVER_MEMORY above only drive local[N] parallelism, driver sizing, and shuffle.partitions below
            .config("spark.executor.cores", "2")
            .config("spark.jars.packages", ",".join(SPARK_PACKAGES))
            .getOrCreate()
        )
    except Exception as exc:
        # Surface actionable troubleshooting steps instead of a raw Py4J/JVM error.
        raise RuntimeError(
            "Could not create a SparkSession. The driver JVM from a previous run is most likely dead.\n"
            "  1. Restart the kernel / Python process.\n"
            "  2. Check the driver log (stderr) for OutOfMemoryError or a lost connection to the master.\n"
            f"  3. If using a standalone master, confirm app state at the master web UI. Master URL: {SPARK_MASTER_URL}"
        ) from exc

    # Re-check the cluster's live resources now that we're connected, so shuffle partitions reflect what's actually available rather than the possibly-stale values computed at import time.
    if SPARK_MASTER_URL.startswith("spark://"):
        live_cores, live_memory_mb = _get_live_cluster_resources(SPARK_MASTER_URL)
        live_cores = live_cores or NUM_CORES
    else:
        live_cores = NUM_CORES
        live_memory_mb = None

    # Rule of thumb: 2 shuffle partitions per core, so work is spread evenly across the cluster.
    shuffle_partitions = live_cores * 2
    spark.conf.set("spark.sql.shuffle.partitions", shuffle_partitions)
    # Stash cluster sizing on the session's own config so calling code can inspect it later (e.g. to size repartition() calls) without re-querying the master.
    spark.conf.set("cluster.total.cores", str(live_cores))
    if live_memory_mb:
        spark.conf.set("cluster.total.memory.gb", str(round(live_memory_mb / 1024, 1)))

    return spark
