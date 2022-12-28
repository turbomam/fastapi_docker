import io
import json
# import linkml
import nmdc_schema
import pkgutil
from fastapi import FastAPI
from linkml_runtime import SchemaView
from linkml_runtime.dumpers import json_dumper
from typing import Union
from deepdiff import DeepDiff

app = FastAPI()

# decoded_schema = io.BytesIO(pkgutil.get_data("nmdc_schema.nmdc_data", "nmdc.yaml")).getvalue().decode("utf-8")
schema_url = "https://raw.githubusercontent.com/microbiomedata/nmdc-schema/main/src/schema/nmdc.yaml"
schema_view = SchemaView(schema_url)


# todo ? dependency injection


@app.get("/")
def read_root():
    return {"Greetings": "Earth"}


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
