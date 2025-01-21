import json

import pandas as pd

from src.graphindex.common.enumerations import IndexType
from src.graphindex.mapping import SemanticMapper
import logging
import time
from dotenv import load_dotenv

# Log steps to file
logfile = f'logs/{time.time()}.txt'

logging.basicConfig(filename=logfile, level=logging.DEBUG)
logging.getLogger().addHandler(logging.FileHandler(filename=logfile))

if __name__ == '__main__':

    load_dotenv('.env')

    data = pd.read_csv('examples/data/fashion_products.csv')

    mapper = SemanticMapper(
        ontology_source_dir='schemas',
        index_output_dir='indices',
        openai_model='gpt-4o-mini',
        index_type=IndexType.VECTOR
    )
    res = mapper.map(
        columns=data.head(10).to_dict(),
        description="The table contains product fashion products information.",
        check_answers_llm='gpt-4o-mini'
    )

    with open('examples/data/results/mapping_result_fashion.json', 'w') as f:
        f.write(json.dumps(res))
