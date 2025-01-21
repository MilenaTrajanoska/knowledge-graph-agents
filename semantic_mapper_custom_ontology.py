import json

import pandas as pd

from src.graphindex.common.enumerations import IndexType
from src.graphindex.mapping import SemanticMapper
import logging
import time

# Log steps to file
logfile = f'logs/{time.time()}.txt'

logging.basicConfig(filename=logfile, level=logging.DEBUG)
logging.getLogger().addHandler(logging.FileHandler(filename=logfile))

if __name__ == '__main__':

    data = pd.read_csv('./examples/data/fashion_products.csv')

    # the gs1 directory will be created in the indices folder and the index will be stored there
    # for next iterations using the same ontology, the index will be reused
    mapper = SemanticMapper(
        ontology_source_dir='schemas/gs1/latest',
        index_output_dir='indices/gs1',
        openai_model='gpt-4o-mini',
        index_type=IndexType.VECTOR,
        target_ontology='gs1',
        ontology_version='latest'
    )
    res = mapper.map(
        columns=data.head(10).to_dict(),
        description="The table contains product fashion products information.",
        check_answers_llm='gpt-4'
    )

    with open('data/results/custom_ontology_mapping_result_fashion.json', 'w') as f:
        f.write(json.dumps(res))
