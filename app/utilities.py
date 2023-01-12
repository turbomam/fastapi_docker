import csv
import pprint
from dataclasses import dataclass, field
from typing import Dict, Optional, List

# from linkml.utils.schema_builder import SchemaBuilder
from linkml_runtime import SchemaView

# from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.linkml_model import (
    SchemaDefinition,
    ClassDefinition,
    SlotDefinition,
)

import logging

from linkml_runtime.linkml_model.meta import PatternExpression
from linkml_runtime.utils.yamlutils import extended_str

# configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# todo simplify by adding typecode annotations in addition to the structured patterns and settings?


@dataclass
class ViewCache:
    """Caches multiple LinkML SchemaViews in a dict. The index is the URL of the schema."""

    # todo is logger getting initialized IN this class?

    cache: Dict[str, SchemaView] = field(default_factory=dict)

    def update_from_url(self, url: str):
        """Updates the cache with a new SchemaView, obtained from a url for the schema."""
        try:
            self.cache[url] = SchemaView(url)
        except Exception as e:
            logger.error(e)

    def update_from_schema(self, url: str, schema: SchemaDefinition):
        """Updates the cache with a new SchemaView, obtained from a schema."""
        # todo could check if the passed url matches the schema.id
        try:
            self.cache[url] = SchemaView(schema)
        except Exception as e:
            logger.error(e)

    def get_view(self, url: str) -> Optional[SchemaView]:
        """Returns a SchemaView from the cache, if it exists."""
        try:
            return self.cache[url]
        except KeyError as e:
            logger.error(e)
            return None

    def trust_cache(self, url: str) -> Optional[SchemaView]:
        """Returns a SchemaView from the cache if possible. Otherwise, populates the cache first."""
        if url in self.cache:
            logger.error("cache hit")
            return self.cache[url]
        else:
            logger.error("cache miss")
            try:
                self.update_from_url(url)
                logger.error("cache updated")
                return self.cache[url]
            except Exception as e:
                logger.error(e)
                return None


def get_induced_from_view(
        view: SchemaView, classname: str
) -> Optional[ClassDefinition]:
    """Returns the structured pattern for a class if available."""

    # todo wrapping a function in a function... what benefit?
    #  the exception isn't doing anything besides logging and returning None

    try:
        induced_class = view.induced_class(classname)
        return induced_class
    except Exception as e:
        logger.error(e)
        return None


def get_slotdef_from_class(
        classobj: ClassDefinition, slotname: str
) -> Optional[SlotDefinition]:
    """Returns a slot definition from a class if available."""
    try:
        slot_def = classobj["attributes"][slotname]
        return slot_def
    except Exception as e:
        logger.error(e)
        return None


def get_structpat_from_slotdef(slotdef: SlotDefinition) -> Optional[PatternExpression]:
    """Returns a structured pattern from a slot definition if available."""
    try:
        structpat = slotdef["structured_pattern"]
        return structpat
    except Exception as e:
        logger.error(e)
        return None


def get_syntax_from_structpat(structpat: PatternExpression) -> Optional[extended_str]:
    """Returns a structured pattern from a slot definition if available."""
    try:
        syntax = structpat["syntax"]
        return syntax
    except Exception as e:
        logger.error(e)
        return None


def extract_typecode_name_from_syntax(syntax: extended_str) -> Optional[str]:
    try:
        local_portion = syntax.split(":")[1]
        chunks_by_hyphen = local_portion.split("-")
        typecode_chunk = chunks_by_hyphen[0]
        # remove first and final characters (curly brackets)
        bare_typecode = typecode_chunk[1:-1]
        return bare_typecode
    except Exception as e:
        logger.error(e)
        return None


def get_schema_settings(view: SchemaView) -> Optional[Dict]:
    """Returns a dictionary of schema settings, if available."""
    # todo what KIND of Dict is returned?
    try:
        schema_settings = view.schema.settings
        return schema_settings
    except Exception as e:
        logger.error(e)
        return None


def get_typecode_from_settings_by_name(
        typecode_name: str, settings: Dict
) -> Optional[str]:
    try:
        typecode_value = settings[typecode_name]["setting_value"]
        return typecode_value
    except Exception as e:
        logger.error(e)
        return None


def get_typecode_wrapper(
        view: SchemaView, class_name: str, slot_name: str
) -> Optional[str]:
    induced_class = get_induced_from_view(view, class_name)

    slotdef = get_slotdef_from_class(induced_class, slot_name)

    structpat = get_structpat_from_slotdef(slotdef)

    syntax = get_syntax_from_structpat(structpat)

    typecode_name = extract_typecode_name_from_syntax(syntax)

    settings = get_schema_settings(view)

    typecode_value = get_typecode_from_settings_by_name(typecode_name, settings)

    return typecode_value


def get_ancestors(view: SchemaView, class_name: str) -> Optional[list]:
    try:
        ancestors = view.class_ancestors(class_name)
        return ancestors
    except Exception as e:
        logger.error(e)
        return None


def get_typecode_via_ancestors(
        view: SchemaView, class_name: str, slot_name: str
) -> Optional[Dict[str, str]]:
    ancestors = get_ancestors(view, class_name)
    if ancestors is not None:
        for ancestor in ancestors:
            # print(ancestor)
            typecode = get_typecode_wrapper(view, ancestor, slot_name)
            if typecode is not None:
                return {"ancestor": ancestor, "typecode": typecode}
    return None


def get_typcodes_by_ancestor_whole_schema(
        view: SchemaView, slot_name: str
) -> Optional[List[Dict[str, str]]]:
    rows = []
    # print("\n")
    try:
        classes = view.all_classes()
        classnames = [v.name for k, v in classes.items()]
        classnames.sort()
    except Exception as e:
        logger.error(e)
        return None
    for class_name in classnames:
        class_obj = view.induced_class(class_name)
        # class_obj = view.get_class(class_name)
        slots = class_obj["attributes"]
        slotnames = [v.name for k, v in slots.items()]
        uses_key_slot = slot_name in slotnames
        if uses_key_slot:
            ancestor_typecode = get_typecode_via_ancestors(view, class_name, slot_name)

            if ancestor_typecode:
                for_rows = {
                    "class": class_name,
                    f"uses_{slot_name}": uses_key_slot,
                    "from_ancestor": ancestor_typecode["ancestor"],
                    "typecode": ancestor_typecode["typecode"],
                }
            else:
                for_rows = {
                    "class": class_name,
                    f"uses_{slot_name}": uses_key_slot,
                    "from_ancestor": class_name,
                    "typecode": None,
                }

        else:
            for_rows = {
                "class": class_name,
                f"uses_{slot_name}": uses_key_slot,
                "from_ancestor": None,
                "typecode": None,
            }
        rows.append(for_rows)

    return rows


def send_class_typecodes_to_tsv(data: List[Dict], output_file_name: str):
    """Sends a list of dictionaries to a CSV file."""
    keys = data[0].keys()
    with open(output_file_name, "w") as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys, delimiter="\t")
        dict_writer.writeheader()
        dict_writer.writerows(data)
