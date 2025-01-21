import json

import pandas as pd

from src.graphindex.common.enumerations import IndexType
from src.graphindex.mapping import SemanticMapper
import logging
import time
import glob
from dotenv import load_dotenv

# Log steps to file
logfile = f'logs/{time.time()}.txt'

logging.basicConfig(filename=logfile, level=logging.DEBUG)
logging.getLogger().addHandler(logging.FileHandler(filename=logfile))

if __name__ == '__main__':

    load_dotenv('.env')

    file_paths = glob.glob("examples\\data\\spider\\*.csv")

    mapper = SemanticMapper(
        ontology_source_dir='schemas',
        index_output_dir='indices',
        openai_model='gpt-4o-mini',
        index_type=IndexType.VECTOR
    )

    for file_path in file_paths:
        data = pd.read_csv(file_path)

        table_name =  file_path.split("\\")[-1].replace(".csv", "")

        table_name_readable = table_name.replace("_", " ").replace("Ref_", "").lower()
    
        res = mapper.map(
            columns=data.head(10).to_dict(),
            description=f"The table contains {table_name_readable} information.",
            check_answers_llm='gpt-4o-mini'
        )

        with open(f'examples/data/results/spider/{table_name}.json', 'w') as f:
            f.write(json.dumps(res))
