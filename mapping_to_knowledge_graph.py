import logging
import json
import pandas as pd
from dotenv import load_dotenv
import glob
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF


mapping_tables = {
    "district": "https://schema.org/Place",
    "Products": "https://schema.org/Product",
    "Ref_Characteristic_Types": "https://schema.org/QualitativeValue",
    "Ref_Product_Categories": "https://schema.org/CategoryCode",
    "Sales_details": "https://schema.org/OrderItem",
    "Sales_header": "https://schema.org/Order",
    "store": "https://schema.org/Store",
}

primary_keys = {
  "Characteristics": "characteristic_id",
  "Ref_Colors": "color_code",
  "sales_header": "id",
  "Product_Characteristics": ["product_id", "characteristic_id"],
  "Ref_Product_Categories": "product_category_code",
  "store": "Store_ID",
  "Products": "product_id",
  "district": "District_ID",
  "store_district": ["Store_ID", "District_ID"],
  "Ref_Characteristic_Types": "characteristic_type_code",
  "sales_details": "id",
  "store_product": ["Store_ID", "Product_ID"]
}

relations_mapping =[
  {
    "subject": "Store_ID",
    "predicate": "https://schema.org/location",
    "object": "District_ID",
    "table_name_relation": "store_district",
    "subject_table_name": "store",
    "object_table_name": "district"
  },
  {
    "subject": "Store_ID",
    "predicate": "https://schema.org/offers",
    "object": "Product_ID",
    "table_name_relation": "store_products",
    "subject_table_name": "store",
    "object_table_name": "Products"
  },
  {
    "subject": "sales_header_id",
    "predicate": "https://schema.org/orderNumber",
    "object": "id",
    "table_name_relation": "sales_details",
    "tableObject": "sales_header",
    "subject_table_name": "sales_details",
    "object_table_name": "sales_header"
  },
  {
    "subject": "product_id",
    "predicate": "https://schema.org/orderedItem",
    "object": "product_id",
    "table_name_relation": "sales_details",
    "tableObject": "Products",
    "subject_table_name": "sales_details",
    "object_table_name": "Products"
  },
#   {
#     "subject": "product_id",
#     "predicate": "https://schema.org/additionalType",
#     "object": "product_id",
#     "table_name_relation": "Product_Characteristics",
#     "tableObject": "Products",
#     "subject_table_name": "Product_Characteristics",
#     "object_table_name": "Products"
#   },
#   {
#     "subject": "characteristic_id",
#     "predicate": "https://schema.org/featureList",
#     "object": "characteristic_id",
#     "table_name_relation": "Product_Characteristics",
#     "tableObject": "Characteristics",
#     "subject_table_name": "Product_Characteristics",
#     "object_table_name": "Characteristics"
#   },
#   {
#     "subject": "characteristic_id",
#     "predicate": "https://schema.org/additionalType",
#     "object": "characteristic_type_code",
#     "table_name_relation": "Product_Characteristics",
#     "tableObject": "Ref_Characteristic_Types",
#     "subject_table_name": "Product_Characteristics",
#     "object_table_name": "Ref_Characteristic_Types"
#   }
]




if __name__ == "__main__":
    mapping_paths = glob.glob('examples\\data\\results\\spider\\*.json')

    base_url = "http://example_db.org"
    
    g = Graph()

    for mapping_path in mapping_paths:
        with open(mapping_path, 'r') as f:
            mapping = json.load(f)

        table_path = mapping_path.replace('results\\', '').replace('.json', '.csv')
        table = pd.read_csv(table_path)

        table_name = table_path.split('\\')[-1].replace('.csv', '')

        if table_name in mapping_tables:
            entity_type = mapping_tables[table_name]
            primary_key = primary_keys[table_name]
        
            for i, row in table.iterrows():
                row_id = row[primary_key]
                uri = URIRef(f"{base_url}#{table_name}{row_id}")
                g.add((uri, RDF.type, URIRef(entity_type)))
                for column in mapping["mappingResult"]:
                    column_name = column["originalTermName"]
                    mapped_column = column.get("targetTermUri")
                    value = row[column_name]
                    if mapped_column and value:
                        g.add((uri, URIRef(mapped_column), Literal(value)))
        else:
            rels = [m for m in relations_mapping if m["table_name_relation"] == table_name]
            for i, row in table.iterrows():
                for relation in rels:
                    subject_id = row[relation['subject']]
                    object_id = row[relation['object']]
                    subject_uri = URIRef(f"{base_url}#{relation['subject_table_name']}{subject_id}")
                    object_uri = URIRef(f"{base_url}#{relation['object_table_name']}{object_id}")
                    g.add((subject_uri, URIRef(relation["predicate"]), object_uri))

    g.serialize('knowledge_graph_products.ttl', format='turtle')
