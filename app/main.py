"""
https://github.com/turbomam/fastapi_docker
"""

# todo mypy --strict app

import csv
import json
from typing import Dict, List, Union, Tuple, Any

import requests

from deepdiff import DeepDiff  # type: ignore

# import linkml
# import nmdc_schema
# import pkgutil
from fastapi import FastAPI, Form
from fastapi.responses import FileResponse

from linkml_runtime import SchemaView  # type: ignore

from linkml_runtime.dumpers import json_dumper  # type: ignore
from pydantic import BaseModel, Field, AnyUrl

# names_ages_file = "names_ages.tsv"
# names_ages_data: List[Dict[str, Union[str, int]]] = []

app = FastAPI()

# decoded_schema = io.BytesIO(pkgutil.get_data("nmdc_schema.nmdc_data", "nmdc.yaml")).getvalue().decode("utf-8")
schema_url = "https://raw.githubusercontent.com/microbiomedata/nmdc-schema/main/src/schema/nmdc.yaml"
schema_view = SchemaView(schema_url)


# # just showing how to return TSV
# # Open the TSV file in read mode
# with open(names_ages_file, "r") as tsv_file:
#     # Create a DictReader object to read the TSV file
#     reader = csv.DictReader(tsv_file, delimiter="\t")
#
#     # Iterate over the rows in the TSV file
#     for row in reader:
#         # overwrites ages if there are duplicate names
#         names_ages_data[row["Name"]] = row["Age"]

# todo: Elais encourages async, but SO answer XXX discourages in situation XXX


@app.get("/")
# async
def read_root() -> str:
    return "see /docs for API documentation"


@app.get("/get_global_slot/{slot_name}")
# async
def get_global_slot(slot_name: str) -> Any:
    slot_obj = schema_view.get_slot(slot_name)
    slot_json = json_dumper.dumps(slot_obj)
    # fastapi custom json serializer?
    # generate pydantic classes for tight integration with fastapi
    slot_dict = json.loads(slot_json)
    return slot_dict


@app.get("/get_slot_class_usage/{slot_name}/{class_name}")
# async
def get_slot_class_usage(slot_name: str, class_name: str) -> Any:
    usage_slot_obj = schema_view.induced_slot(slot_name, class_name)
    usage_slot_json = json_dumper.dumps(usage_slot_obj)
    usage_slot_dict = json.loads(usage_slot_json)
    return usage_slot_dict


# @app.get("/slot_class_usage/{global_schema_url}/{slot_name}/{class_name}/{usage_schema_url}")
@app.get("/get_global_usage_diff/{slot_name}/{class_name}")
# def get_global_usage_diff(global_schema_url: str, slot_name: str, class_name: str, usage_view: str):
# async
def get_global_usage_diff(slot_name: str, class_name: str) -> Any:
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


# @app.get("/names_ages_tsv")
# # async
# def names_ages_tsv():
# # would be better to stream the file
#     return FileResponse(names_ages_file, media_type="text/tab-separated-values")
#     # return FileResponse(path=names_ages_file, filename=names_ages_file)


# @app.get("/static_oreos")
# # async
# def static_oreos():
# response = requests.get(
#         "https://world.openfoodfacts.org/api/v0/product/7622300489434.json"
#     )
#     return response.json()


# @app.get("/get_from_dub_encoded/{double_encoded_url}")
# # async
# def get_from_dub_encoded(double_encoded_url: str):
# """
#     Try https%253A%252F%252Fworld.openfoodfacts.org%252Fapi%252Fv0%252Fproduct%252F7622300489434.json
#     """
#     original_url = urllib.parse.unquote(urllib.parse.unquote(double_encoded_url))
#     response = requests.get(original_url)
#     return response.json()


class InputModel(BaseModel):
    unencoded_url: AnyUrl = Field(
        description="An unencoded URL for an external resource", format="url"
    )


# @app.post("/unencoded_url")
# def unencoded_url(inputs: InputModel):
#     response = requests.get(inputs.unencoded_url)
#     return response.json()


# @app.post("/unencoded_form")
# def unencoded_form(
#     url: str = Form(
#         default="https://world.openfoodfacts.org/api/v0/product/7622300489434.json"
#     ),
# ):
#     """
#     Try https://world.openfoodfacts.org/api/v0/product/7622300489434.json
#     """
#     response = requests.get(url)
#     return response.json()


@app.get("/get_class_typecode/{class_name}")
# async
def get_class_typecode(class_name: str) -> Union[tuple[str, int], Any]:
    # Validate input
    # todo this doesn't actually return a 400 error
    if not isinstance(class_name, str) or not class_name:
        return "Null or non-string class_name", 400

    # todo: when entering an undefined class name
    #  unhelpful 500 error
    #  AttributeError: 'NoneType' object has no attribute 'name'
    try:
        class_obj = schema_view.induced_class(class_name)
    except KeyError:
        return (
            f"The schema couldn't be loaded or it does not include class {class_name}",
            404,
        )

    try:
        class_id_struct_patt = class_obj["attributes"]["id"]["structured_pattern"]
    except KeyError:
        return (
            f"Class {class_name} does not include a ['attributes']['id']['structured_pattern'] path",
            404,
        )

    struct_patt_json = json_dumper.dumps(class_id_struct_patt)
    # fastapi custom json serializer?
    # generate pydantic classes for tight integration with fastapi
    struct_patt_dict = json.loads(struct_patt_json)

    try:
        struct_patt_syntax = struct_patt_dict["syntax"]
    except KeyError:
        return (
            f"Class {class_name}'s ['attributes']['id']['structured_pattern'] does not include a ['syntax']",
            404,
        )

    try:
        # could probably do this parse in one or a smaller number os steps
        local_portion = struct_patt_syntax.split(":")[1]
        chunks_by_hyphen = local_portion.split("-")
        typecode_chunk = chunks_by_hyphen[0]
        # remove first and final characters (curly brackets)
        bare_typecode = typecode_chunk[1:-1]
    except Exception:
        return "Error parsing class ID structured pattern", 500

    try:
        all_settings = schema_view.schema.settings
    except KeyError:
        return "Schema does not include a settings block", 404

    try:
        return all_settings[bare_typecode]["setting_value"]
    except KeyError:
        return "Typecode not found", 404


@app.post("/undefined_mixs_assigned_terms/")
# async
def undefined_mixs_assigned_terms(
    def_file_url: str = Form(
        default="https://raw.githubusercontent.com/GenomicsStandardsConsortium/mixs/issue-511-tested-schemasheets/schemasheets/tsv_in/MIxS_6_term_updates_global_partial_slotdefs.tsv"
    ),
    assignment_file_url: str = Form(
        default="https://raw.githubusercontent.com/GenomicsStandardsConsortium/mixs/issue-511-tested-schemasheets/schemasheets/tsv_in/MIxS_6_term_updates_slot_assignments_and_usages.tsv"
    ),
) -> List[str]:
    """
    Return a list of all terms in the def_file that are not assigned in the assignment_file
    """

    defined_terms = list(
        set(
            tsv_url_to_term_list(
                tsv_url=def_file_url, term_column_name="SAFE Structured comment name"
            )
        )
    )
    defined_terms.sort()

    assigned_terms = list(
        set(
            tsv_url_to_term_list(
                tsv_url=assignment_file_url, term_column_name="Structured comment name"
            )
        )
    )
    assigned_terms.sort()

    undefined_terms = list(set(assigned_terms) - set(defined_terms))
    undefined_terms.sort()

    return undefined_terms

    # return ["a", "b", "c"]


@app.post("/unassigned_mixs_defined_terms/")
# async ?
def unassigned_mixs_defined_terms(
    def_file_url: str = Form(
        default="https://raw.githubusercontent.com/GenomicsStandardsConsortium/mixs/issue-511-tested-schemasheets/schemasheets/tsv_in/MIxS_6_term_updates_global_partial_slotdefs.tsv"
    ),
    assignment_file_url: str = Form(
        default="https://raw.githubusercontent.com/GenomicsStandardsConsortium/mixs/issue-511-tested-schemasheets/schemasheets/tsv_in/MIxS_6_term_updates_slot_assignments_and_usages.tsv"
    ),
) -> List[str]:
    """
    Return a list of all terms in the def_file that are not assigned in the assignment_file
    """

    defined_terms = list(
        set(
            tsv_url_to_term_list(
                tsv_url=def_file_url, term_column_name="SAFE Structured comment name"
            )
        )
    )
    defined_terms.sort()

    assigned_terms = list(
        set(
            tsv_url_to_term_list(
                tsv_url=assignment_file_url, term_column_name="Structured comment name"
            )
        )
    )
    assigned_terms.sort()

    unassigned_terms = list(set(defined_terms) - set(assigned_terms))
    unassigned_terms.sort()

    return unassigned_terms


# async
def tsv_url_to_term_list(
    tsv_url: str, term_column_name: str, discard_first_n: int = 2
) -> List[str]:
    # Download the TSV file from the URL
    response = requests.get(tsv_url)
    # print(f"response type: {type(response).class_name}")

    # Decode the contents of the response
    text = response.text

    # Create a DictReader object to parse the TSV file
    reader = csv.DictReader(text.splitlines(), delimiter="\t")

    term_list = []
    for row in reader:
        # Each row is a dictionary that maps the column names to the values
        term_list.append(row[term_column_name])

    remaining_items = term_list[discard_first_n:]

    remaining_items.sort()

    remaining_items = remaining_items

    return remaining_items


@app.post("/compare_slots_in_two_classes/")
# async?
def compare_slots_in_two_classes(
    schema_1_url: str = Form(
        default="https://raw.githubusercontent.com/GenomicsStandardsConsortium/mixs/main/model/schema/mixs.yaml"
    ),
    class_1_name: str = Form(default="water"),
    schema_2_url: str = Form(
        default="https://raw.githubusercontent.com/microbiomedata/sheets_and_friends/main/artifacts/nmdc_submission_schema.yaml"
    ),
    class_2_name: str = Form(default="water"),
) -> Dict[str, List[str]]:
    # which source for mixs schema?
    """
    SLOW! Should cache returned views, at least. Compare the slots in two schemas and return the set differences
    """
    # todo refactor
    view_1 = SchemaView(schema_1_url)
    class_1_slots_obj_list = view_1.class_induced_slots(class_1_name)
    class_1_slots_names = [slot_obj["name"] for slot_obj in class_1_slots_obj_list]
    class_1_slots_names = list(set(class_1_slots_names))
    class_1_slots_names.sort()
    schema_1_name = view_1.schema.name

    view_2 = SchemaView(schema_2_url)
    class_2_slots_obj_list = view_2.class_induced_slots(class_2_name)
    class_2_slots_names = [slot_obj["name"] for slot_obj in class_2_slots_obj_list]
    class_2_slots_names = list(set(class_2_slots_names))
    class_2_slots_names.sort()
    schema_2_name = view_2.schema.name

    class_1_only = list(set(class_1_slots_names) - set(class_2_slots_names))
    class_1_only.sort()

    class_2_only = list(set(class_2_slots_names) - set(class_1_slots_names))
    class_2_only.sort()

    return {
        f"Slots only found in {schema_1_name}'s {class_1_name}": class_1_only,
        f"Slots only found in {schema_2_name}'s {class_2_name}": class_2_only,
    }
