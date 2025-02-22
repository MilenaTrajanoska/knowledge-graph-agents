import json
from typing import Dict

import openai
import pandas as pd
import requests
import os

from llama_index.llms.openai import OpenAI
from llama_index.core.graph_stores import SimpleGraphStore

from src.graphindex.common.config import (
    SCHEMA_ORG_URI,
    SCHEMA_ORG_LOCAL_PATH_SUBGRAPHS,
    SCHEMA_ORG_LOCAL_PATH,
    SCHEMA_ORG_INDEX_LOCAL_PATH,
    SCHEMA_FILE_NAME
)

from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    SimpleDirectoryReader,
    KnowledgeGraphIndex,
    Settings,
)

from src.graphindex.common.prompts.joins import TABLE_JOINS_PROMPT_SYSTEM, TABLE_JOINS_PROMPT
from src.graphindex.common.utils import (
    create_graph_from_jsonld,
    save_subjects_to_files,
    extract_subgraph_for_each_subject
)

from src.graphindex.common.enumerations import IndexType


class OntologyIndex:
    def __init__(
            self,
            index_type: IndexType,
            source_dir='./schemas',
            output_dir='./index',
            use_schema_org: bool = False,
            ontology_version: str = None
    ) -> None:
        self.uri = SCHEMA_ORG_URI.format(ontology_version=ontology_version)
        self.index_type = index_type
        self.schema_file_name = SCHEMA_FILE_NAME

        if use_schema_org:
            self.schema_local_path = SCHEMA_ORG_LOCAL_PATH.format(
                src_dir=source_dir,
                ontology_version=ontology_version
            )
            self.local_index = SCHEMA_ORG_INDEX_LOCAL_PATH.format(
                output_dir=output_dir,
                ontology_version=ontology_version,
                index_type=str.lower(self.index_type.name)
            )
            self.subgraphs_path = SCHEMA_ORG_LOCAL_PATH_SUBGRAPHS.format(
                src_dir=source_dir,
                ontology_version=ontology_version
            )

        else:
            self.schema_local_path = source_dir
            self.local_index = output_dir
            self.subgraphs_path = f"{source_dir}/subgraphs"

        self.index = None
        self.ontology_version = ontology_version
        self.use_schema_org= use_schema_org

    def _is_local_ontology(self):
        local_path = self.schema_local_path

        if os.path.isdir(local_path):
            return True

        os.makedirs(local_path)
        return False

    def _load_local_index(self):
        local_index = self.local_index

        if os.path.isdir(local_index):
            storage_context = StorageContext.from_defaults(persist_dir=local_index)
            return load_index_from_storage(storage_context)

        os.makedirs(local_index)

        return None

    def _load_schema_org_ontology(self):
        if not self._is_local_ontology():
            release_uri = self.uri

            response = requests.get(release_uri)

            if response.status_code != 200:
                raise Exception(f"Failed to fetch schema.org version {self.ontology_version}. \
                            Status code: {response.status_code}")

            result = response.json()

            graph = create_graph_from_jsonld(result)
            subjects_with_props = extract_subgraph_for_each_subject(graph)
            save_subjects_to_files(
                subjects_with_props,
                self.subgraphs_path
            )

    def _transform_graph_to_vector_store(self):
        try:
            index = self._load_local_index()
        except Exception as err:
            raise Exception("Could not read local index.")

        if not index:
            schema_path = self.subgraphs_path
            index_path = self.local_index

            documents = SimpleDirectoryReader(schema_path).load_data()

            if self.index_type == IndexType.VECTOR:
                index = VectorStoreIndex.from_documents(documents)

            elif self.index_type == IndexType.KNOWLEDGE_GRAPH:
                graph_store = SimpleGraphStore()
                storage_context = StorageContext.from_defaults(graph_store=graph_store)

                llm = OpenAI(temperature=0, model="gpt-4o-mini")
                Settings.llm=llm
                Settings.chunk_size=512

                # NOTE: can take a while!
                index = KnowledgeGraphIndex.from_documents(
                    documents,
                    max_triplets_per_chunk=3,
                    storage_context=storage_context
                )
            else:
                raise NotImplementedError()

            index.storage_context.persist(persist_dir=index_path)

        self.index = index

    def create_index_from_ontology_version(self):
        if self.use_schema_org:
            self._load_schema_org_ontology()
        self._transform_graph_to_vector_store()

    def get_index(self):
        return self.index


def jaccard(list1, list2):
    intersection = len(list(set(list1).intersection(list2)))
    union = len(list((set(list1).union(set(list2)))))
    return intersection / union if union else 0


class ColumnIndex:
    def __init__(
            self,
            tables: Dict[str, pd.DataFrame],
            output_dir: str = "./index",
            openai_model: str = "gpt-4o-mini",
    ):
        self.tables = {k: v.head(10).to_dict() for k, v in tables.items()}
        self.index_path = output_dir
        self.openai_model = openai_model
        self.index = self._load_or_create_index()
        self._save_index(self.index)

    def _load_or_create_index(self):
        if (not os.path.isdir(self.index_path)) or (not len(os.listdir(self.index_path))):
            os.makedirs(self.index_path)
            return self._create_column_index(self.tables)
        else:
            with open(f"{self.index_path}/index.json", "r") as f:
                return json.load(f)

    def _create_column_index(self, tables: Dict[str, pd.DataFrame]):
        system_prompt = TABLE_JOINS_PROMPT_SYSTEM

        prompt = TABLE_JOINS_PROMPT.format(
            tables=json.dumps(tables),
        )

        response = openai.ChatCompletion.create(
            model=self.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
        )

        index = json.loads(response["choices"][0]["message"]["content"])
        self._save_index(index)
        return index

    def _save_index(self, index):
        with open(f"{self.index_path}/index.json", "w") as f:
            f.write(json.dumps(index))

    def get_primary_keys(self):
        return self.index["primaryKeys"]

    def get_foreign_keys(self):
        return self.index["foreignKeys"]

    def get_joins(self):
        return self.index["joins"]

    def get_index(self):
        return self.index
