import airflow
from datetime import datetime, timedelta
from airflow.operators.python_operator import PythonOperator
import pyspark
from pyspark.sql import SQLContext
from pyspark.sql import SparkSession
from airflow.models import DAG
import pyspark.sql.functions as f
from functools import reduce
from pyspark.sql.functions import from_unixtime, col
from datetime import datetime, timedelta
from pyspark.sql import functions as F
from pyspark.sql.types import *
from pyspark.sql.functions import *
from pyspark.sql.functions import col, when
now = datetime.now()


args = {
    'owner': 'Hassan',
    "start_date": datetime(now.year, now.month, now.day),
    'provide_context': True,
    'depends_on_past': True,
    'wait_for_downstream': True,
}

dag = DAG(
    dag_id='ETL_Striming',
    default_args=args,
    schedule_interval=timedelta(1),
    max_active_runs=1,
    concurrency=1
)


# -----------------------------------------------------------------------------------------
# inner functions
def create_spark_session(spark_host):
    app = SparkSession \
        .builder \
        .appName("striming") \
        .config("spark.jars.packages",
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2")\
        .config("spark.cores.max","1")\
        .config("spark.executor.memory", "1g")\
        .config("spark.executor.cores","1")\
        .config("spark.dynamicAllocation.initialExecutors","1")\
        .master(spark_host) \
        .getOrCreate()
    return app

def metadata():
    schema =StructType([
            StructField("fullDocument", StructType(
                [StructField("_id", StructType([StructField("$oid", StringType(), False)]), False)
                    ,StructField("givenName", StringType(), False)
                    ,StructField("familyName", StringType(), False)
                    ,StructField("email", StringType(), False)
                    ,StructField("gender", StringType(), False)
                    ,StructField("phoneNumber", StringType(), False)
                    ,StructField("dateOfBirth", StructType([StructField("$date", StringType(), False)]), False)
                 ]),
                        False)
        ])
		
    return schema


# -----------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------

# task functions

# -----------------------------------------------------------------------------------------
def compress_to_trusted_dimuserlive(**kwargs):
     spark = create_spark_session("spark://spark:7077")
     sc = spark.sparkContext
     sqlContext = SQLContext(sc)
     print( spark.sparkContext._conf.getAll())
     df = spark.readStream.format("kafka").option("kafka.bootstrap.servers", "broker:29092").option("subscribe", "topic1.mydb.user1").option("startingOffsets", "latest").load()
     personStringDF = df.selectExpr("CAST(value AS STRING)")
     personDF = personStringDF.select(from_json(col("value"), metadata()).alias("data"))\
    .select("data.fullDocument._id.$oid","data.fullDocument.givenName"
            ,"data.fullDocument.familyName","data.fullDocument.email","data.fullDocument.gender","data.fullDocument.phoneNumber",
            "data.fullDocument.dateOfBirth.$date")
     personDF.writeStream.format("parquet").option("checkpointLocation", "hdfs://namenode:9000//checkpoint/dir").option("path","hdfs://namenode:9000//destination/dir").start().awaitTermination()
# -----------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------
# operators
t_compress_to_trusted_dimuserlive = PythonOperator(
    task_id='compress_to_trusted_dimuserlive',
    python_callable=compress_to_trusted_dimuserlive,
    dag=dag, )


t_compress_to_trusted_dimuserlive
