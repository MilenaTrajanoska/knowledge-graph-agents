import sqlite3

import pandas as pd

table = "store_district"
conn = sqlite3.connect(
    "C:/Users/mimi_/Desktop/spider/spider/database/store_product/store_product.sqlite",
    isolation_level=None,
    detect_types=sqlite3.PARSE_COLNAMES)
db_df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
db_df.to_csv(f'./examples/data/spider/{table}.csv', index=False)