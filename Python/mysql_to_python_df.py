import pandas as pd
from sqlalchemy import create_engine

# MySQL connection
user = ""
password = ""
host = ""
database = ""
engine = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{database}')

## Importing datasets to python
application_train = pd.read_sql(
    sql="",
    con=engine
)

