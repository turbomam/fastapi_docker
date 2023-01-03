import csv
import json
import urllib.parse

import requests
# import aiofiles
# from typing import Union
from deepdiff import DeepDiff
# import linkml
# import nmdc_schema
# import pkgutil
from fastapi import FastAPI, Form
from fastapi.responses import FileResponse
from linkml_runtime import SchemaView
from linkml_runtime.dumpers import json_dumper
from pydantic import BaseModel, Field, AnyUrl

names_ages_file = "nages.tsv"
names_ages_data = {}

app = FastAPI()

# decoded_schema = io.BytesIO(pkgutil.get_data("nmdc_schema.nmdc_data", "nmdc.yaml")).getvalue().decode("utf-8")
schema_url = "https://raw.githubusercontent.com/microbiomedata/nmdc-schema/main/src/schema/nmdc.yaml"
schema_view = SchemaView(schema_url)

# Open the TSV file in read mode
with open(names_ages_file, 'r') as tsv_file:
    # Create a DictReader object to read the TSV file
    reader = csv.DictReader(tsv_file, delimiter='\t')

    # Iterate over the rows in the TSV file
    for row in reader:
        # overwrites ages if there are duplicate names
        names_ages_data[row['Name']] = row['Age']


# print(names_ages_data)


# todo ? dependency injection


@app.get("/")
def read_root():
    return {"greetings": "NMDC users!"}


@app.get("/get_global_slot/{slot_name}")
def get_global_slot(slot_name: str):
    slot_obj = schema_view.get_slot(slot_name)
    slot_json = json_dumper.dumps(slot_obj)
    # fastapi custom json serializer?
    # generate pydantic classes for tight integration with fastapi
    slot_dict = json.loads(slot_json)
    return slot_dict


@app.get("/get_slot_class_usage/{slot_name}/{class_name}")
def get_slot_class_usage(slot_name: str, class_name: str):
    usage_slot_obj = schema_view.induced_slot(slot_name, class_name)
    usage_slot_json = json_dumper.dumps(usage_slot_obj)
    usage_slot_dict = json.loads(usage_slot_json)
    return usage_slot_dict


# @app.get("/slot_class_usage/{global_schema_url}/{slot_name}/{class_name}/{usage_schema_url}")
@app.get("/get_global_usage_diff/{slot_name}/{class_name}")
# def get_global_usage_diff(global_schema_url: str, slot_name: str, class_name: str, usage_view: str):
def get_global_usage_diff(slot_name: str, class_name: str):
    """
    Provide the name of a slot in the NMDC schema, and the name of a class that uses that slot.
    A DeepDiff difference between the slot's global definition and it's usage within the class will be returned.
    """
    # global_view = SchemaView(global_schema_url)
    # usage_view = SchemaView(usage_schema_url)
    # class_obj = schema_view.induced_class(class_name)

    global_slot_obj = schema_view.get_slot(slot_name)
    global_slot_json = json_dumper.dumps(global_slot_obj)
    global_slot_dict = json.loads(global_slot_json)

    usage_slot_obj = schema_view.induced_slot(slot_name, class_name)
    usage_slot_json = json_dumper.dumps(usage_slot_obj)
    usage_slot_dict = json.loads(usage_slot_json)

    global_vs_usage = DeepDiff(global_slot_dict, usage_slot_dict, ignore_order=True)

    return global_vs_usage


@app.get("/names_ages_tsv")
async def names_ages_tsv():
    # would be better to stream the file
    return FileResponse(names_ages_file, media_type="text/tab-separated-values")
    # return FileResponse(path=names_ages_file, filename=names_ages_file)


@app.get("/static_oreos")
async def static_oreos():
    response = requests.get('https://world.openfoodfacts.org/api/v0/product/7622300489434.json')
    return response.json()


# @app.get("/get_from_dub_encoded/{double_encoded_url}")
# async def get_from_dub_encoded(double_encoded_url: str):
#     """
#     Try https%253A%252F%252Fworld.openfoodfacts.org%252Fapi%252Fv0%252Fproduct%252F7622300489434.json
#     """
#     original_url = urllib.parse.unquote(urllib.parse.unquote(double_encoded_url))
#     response = requests.get(original_url)
#     return response.json()


class InputModel(BaseModel):
    unencoded_url: AnyUrl = Field(description="An unencoded URL for an external resource", format="url")


@app.post("/unencoded_url")
def unencoded_url(inputs: InputModel):
    response = requests.get(inputs.unencoded_url)
    return response.json()


@app.post("/unencoded_form")
def unencoded_form(url: str = Form(default="https://world.openfoodfacts.org/api/v0/product/7622300489434.json")):
    """
    Try https://world.openfoodfacts.org/api/v0/product/7622300489434.json
    """
    response = requests.get(url)
    return response.json()


# @app.post("/login/")
# async def login(username: str = Form(...), password: str = Form(...)):
#     return {"username": username, "password": password}

@app.get("/get_class_typecode/{class_name}")
def get_class_typecode(class_name: str):
    class_obj = schema_view.induced_class(class_name)
    class_id_struct_patt = class_obj['attributes']['id']['structured_pattern']
    struct_patt_json = json_dumper.dumps(class_id_struct_patt)
    # fastapi custom json serializer?
    # generate pydantic classes for tight integration with fastapi
    struct_patt_dict = json.loads(struct_patt_json)
    struct_patt_syntax = struct_patt_dict['syntax']

    # could probably do this parse in one or a smaller number os steps
    # should customize 5xx return values
    local_portion = struct_patt_syntax.split(':')[1]
    chunks_by_hyphen = local_portion.split('-')
    typecode_chunk = chunks_by_hyphen[0]
    # remove first and final characters (curly brackets)
    bare_typecode = typecode_chunk[1:-1]

    all_settings = schema_view.schema.settings

    return all_settings[bare_typecode]['setting_value']
