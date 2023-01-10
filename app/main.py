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


# todo the next four methods are really the same,
#  just with different prompts for TSV file URLs and different hard-coded column names


@app.post("/undefined_mixs_assigned_terms/")
# async
def undefined_mixs_assigned_terms(
    def_file_url: str = Form(
        default="https://raw.githubusercontent.com/GenomicsStandardsConsortium/mixs/issue-511-tested-schemasheets/schemasheets/tsv_in/MIxS_6_term_updates_global_partial_slotdefs.tsv"
    ),
    def_file_term_col: str = Form(default="SAFE Structured comment name"),
    assignment_file_url: str = Form(
        default="https://raw.githubusercontent.com/GenomicsStandardsConsortium/mixs/issue-511-tested-schemasheets/schemasheets/tsv_in/MIxS_6_term_updates_slot_assignments_and_usages.tsv"
    ),
    assignment_file_term_col: str = Form(default="Structured comment name"),
) -> List[str]:
    """
    Return a list of all terms in the def_file that are not assigned in the assignment_file
    """

    undefined_terms = term_diffs_from_tsvs(
        tsv_url_1=assignment_file_url,
        col_name_1=assignment_file_term_col,
        tsv_url_2=def_file_url,
        col_name_2=def_file_term_col,
    )
    undefined_terms.sort()

    return undefined_terms


@app.post("/unassigned_mixs_defined_terms/")
# async ?
def unassigned_mixs_defined_terms(
    def_file_url: str = Form(
        default="https://raw.githubusercontent.com/GenomicsStandardsConsortium/mixs/issue-511-tested-schemasheets/schemasheets/tsv_in/MIxS_6_term_updates_global_partial_slotdefs.tsv"
    ),
    def_file_term_col: str = Form(default="SAFE Structured comment name"),
    assignment_file_url: str = Form(
        default="https://raw.githubusercontent.com/GenomicsStandardsConsortium/mixs/issue-511-tested-schemasheets/schemasheets/tsv_in/MIxS_6_term_updates_slot_assignments_and_usages.tsv"
    ),
    assignment_file_term_col: str = Form(default="Structured comment name"),
) -> List[str]:
    """
    Return a list of all terms in the def_file that are not assigned in the assignment_file
    """

    unassigned_terms = term_diffs_from_tsvs(
        tsv_url_1=def_file_url,
        col_name_1=def_file_term_col,
        tsv_url_2=assignment_file_url,
        col_name_2=assignment_file_term_col,
    )
    unassigned_terms.sort()

    return unassigned_terms


@app.post("/undefined_mixs_assigned_packages/")
# async
def undefined_mixs_assigned_packages(
    def_file_url: str = Form(
        default="https://raw.githubusercontent.com/GenomicsStandardsConsortium/mixs/issue-511-tested-schemasheets/schemasheets/tsv_in/MIxS_6_term_updates_classdefs.tsv"
    ),
    def_file_term_col: str = Form(default="SAFE checklist"),
    assignment_file_url: str = Form(
        default="https://raw.githubusercontent.com/GenomicsStandardsConsortium/mixs/issue-511-tested-schemasheets/schemasheets/tsv_in/MIxS_6_term_updates_slot_assignments_and_usages.tsv"
    ),
    assignment_file_term_col: str = Form(default="class"),
) -> List[str]:
    """
    Return a list of all terms in the def_file that are not assigned in the assignment_file. Has this been updated?
    """

    undefined_packages = term_diffs_from_tsvs(
        tsv_url_1=assignment_file_url,
        col_name_1=assignment_file_term_col,
        tsv_url_2=def_file_url,
        col_name_2=def_file_term_col,
    )
    undefined_packages.sort()

    return undefined_packages


@app.post("/unassigned_mixs_defined_packages/")
# async ?
def unassigned_mixs_defined_packages(
    def_file_url: str = Form(
        default="https://raw.githubusercontent.com/GenomicsStandardsConsortium/mixs/issue-511-tested-schemasheets/schemasheets/tsv_in/MIxS_6_term_updates_classdefs.tsv"
    ),
    def_file_term_col: str = Form(default="SAFE checklist"),
    assignment_file_url: str = Form(
        default="https://raw.githubusercontent.com/GenomicsStandardsConsortium/mixs/issue-511-tested-schemasheets/schemasheets/tsv_in/MIxS_6_term_updates_slot_assignments_and_usages.tsv"
    ),
    assignment_file_term_col: str = Form(default="class"),
) -> List[str]:
    """
    Return a list of all terms in the def_file that are not assigned in the assignment_file. Has this been updated?
    """

    unassigned_packages = term_diffs_from_tsvs(
        tsv_url_1=def_file_url,
        col_name_1=def_file_term_col,
        tsv_url_2=assignment_file_url,
        col_name_2=assignment_file_term_col,
    )
    unassigned_packages.sort()

    return unassigned_packages


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

    return remaining_items


def term_diffs_from_tsvs(
    tsv_url_1: str, col_name_1: str, tsv_url_2: str, col_name_2: str
) -> List[str]:
    terms_1 = unique_vals_from_tsv_by_url_and_colname(
        tsv_url=tsv_url_1, col_name=col_name_1
    )
    terms_2 = unique_vals_from_tsv_by_url_and_colname(
        tsv_url=tsv_url_2, col_name=col_name_2
    )

    terms_1_minus_terms_2 = list(set(terms_1) - set(terms_2))
    return terms_1_minus_terms_2


def unique_vals_from_tsv_by_url_and_colname(tsv_url: str, col_name: str):
    terms = list(set(tsv_url_to_term_list(tsv_url=tsv_url, term_column_name=col_name)))

    return terms


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


@app.get("/get_class_typecode_table/")
# async?
# what's the return type?
# tsv file download?
def get_class_typecode_table():
    try:
        all_settings = schema_view.schema.settings
    except KeyError:
        return "Schema does not include a settings block", 404

    all_classes = schema_view.all_classes()
    all_class_names = [v["name"] for k, v in all_classes.items()]
    all_class_names.sort()

    all_class_attributes = []
    for class_name in all_class_names:
        this_class_attributes = {}
        this_class_induced = schema_view.induced_class(class_name)
        this_class_attributes["class"] = class_name

        this_class_induced_slots = schema_view.class_induced_slots(class_name)
        this_class_induced_slots_names = [i["name"] for i in this_class_induced_slots]
        this_class_induced_slots_names.sort()
        # this_class_attributes["slots"] = this_class_induced_slots_names

        this_class_attributes["uses_id"] = "false"
        this_class_attributes["typecode"] = ""
        class_id_struct_patt = ""

        if "id" in this_class_induced_slots_names:
            this_class_attributes["uses_id"] = "true"
            try:
                class_id_struct_patt = this_class_induced["attributes"]["id"][
                    "structured_pattern"
                ]
            except KeyError:
                class_id_struct_patt = ""

        if class_id_struct_patt:
            try:

                local_portion = class_id_struct_patt["syntax"].split(":")[1]
                chunks_by_hyphen = local_portion.split("-")
                typecode_chunk = chunks_by_hyphen[0]
                # remove first and final characters (curly brackets)
                bare_typecode = typecode_chunk[1:-1]

                try:
                    this_class_attributes["typecode"] = all_settings[bare_typecode][
                        "setting_value"
                    ]
                except KeyError:
                    this_class_attributes["typecode"] = ""

            except KeyError:
                this_class_attributes["typecode"] = ""

        all_class_attributes.append(this_class_attributes)

    # return all_class_attributes

    keys = all_class_attributes[0].keys()

    class_types_file_name = "class_typecodes.tsv"

    with open(class_types_file_name, "w") as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys, delimiter="\t")
        dict_writer.writeheader()
        dict_writer.writerows(all_class_attributes)

    return FileResponse(class_types_file_name, media_type="text/tab-separated-values")
