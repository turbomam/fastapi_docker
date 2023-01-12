import logging
import pprint
from timeit import default_timer as timer

from linkml.utils.schema_builder import SchemaBuilder
from linkml_runtime import SchemaView
from starlette.testclient import TestClient

import app.utilities as au
from app.main import app

# configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = TestClient(app)


def test_root_endpoint():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"greetings": "NMDC users!"}


def test_cache():
    view_cache = au.ViewCache()

    b = SchemaBuilder()
    min_schema = b.schema

    view_cache.cache["http://example.org/test-schema"] = SchemaView(min_schema)

    fetched = view_cache.cache["http://example.org/test-schema"]

    assert fetched.schema.id == "http://example.org/test-schema"


def test_cache_trusting():
    view_cache = au.ViewCache()

    # https://raw.githubusercontent.com/linkml/linkml/main/examples/PersonSchema/personinfo.yaml is too small
    # try https://raw.githubusercontent.com/microbiomedata/nmdc-schema/main/src/schema/nmdc.yaml
    schema_url = "https://raw.githubusercontent.com/microbiomedata/nmdc-schema/main/src/schema/nmdc.yaml"
    start = timer()
    first_fetch = view_cache.trust_cache(schema_url)
    end = timer()
    first_duration = end - start

    start = timer()
    second_fetch = view_cache.trust_cache(schema_url)
    end = timer()
    second_duration = end - start

    assert first_duration > second_duration


def test_integration_for_study():
    nmdc_url = "https://raw.githubusercontent.com/microbiomedata/nmdc-schema/main/src/schema/nmdc.yaml"
    class_name = "Study"
    slot_name = "id"
    expected_typecode = "sty"

    view_cache = au.ViewCache()

    nmdc_view = view_cache.trust_cache(nmdc_url)

    induced_class = au.get_induced_from_view(nmdc_view, class_name)

    slotdef = au.get_slotdef_from_class(induced_class, slot_name)

    structpat = au.get_structpat_from_slotdef(slotdef)

    syntax = au.get_syntax_from_structpat(structpat)

    typecode_name = au.extract_typecode_name_from_syntax(syntax)

    settings = au.get_schema_settings(nmdc_view)

    typecode_value = au.get_typecode_from_settings_by_name(typecode_name, settings)

    assert typecode_value == expected_typecode


def test_wrapper_for_study():
    nmdc_url = "https://raw.githubusercontent.com/microbiomedata/nmdc-schema/main/src/schema/nmdc.yaml"
    class_name = "Study"
    slot_name = "id"
    expected_typecode = "sty"

    view_cache = au.ViewCache()
    nmdc_view = view_cache.trust_cache(nmdc_url)

    typecode_value = au.get_typecode_wrapper(nmdc_view, class_name, slot_name)

    assert typecode_value == expected_typecode


def test_get_ancestors():
    nmdc_url = "https://raw.githubusercontent.com/microbiomedata/nmdc-schema/main/src/schema/nmdc.yaml"
    class_name = "Biosample"
    expected_ancestors = ["Biosample", "MaterialEntity", "NamedThing"]

    view_cache = au.ViewCache()
    nmdc_view = view_cache.trust_cache(nmdc_url)

    ancestors = au.get_ancestors(nmdc_view, class_name)

    assert ancestors == expected_ancestors


def test_via_ancestors():
    nmdc_url = "https://raw.githubusercontent.com/microbiomedata/nmdc-schema/main/src/schema/nmdc.yaml"

    # class_name = "Biosample"
    # slot_name = "id"
    # expected = {"ancestor": "Biosample", "typecode": "bsm"}

    class_name = "MagsAnalysisActivity"
    slot_name = "id"
    expected = {"ancestor": "", "typecode": "acty"}

    view_cache = au.ViewCache()
    nmdc_view = view_cache.trust_cache(nmdc_url)

    ancestor_typecode_dict = au.get_typecode_via_ancestors(
        view=nmdc_view, class_name=class_name, slot_name=slot_name
    )

    assert ancestor_typecode_dict == expected


def test_whole_schema_typecodes():
    nmdc_url = "https://raw.githubusercontent.com/microbiomedata/nmdc-schema/main/src/schema/nmdc.yaml"
    class_name = "Biosample"
    slot_name = "id"
    expected_typecode = "bsm"

    view_cache = au.ViewCache()
    nmdc_view = view_cache.trust_cache(nmdc_url)

    rows = au.get_typcodes_by_ancestor_whole_schema(view=nmdc_view, slot_name=slot_name)

    keyed_rows = {row["class"]: row for row in rows}

    pprint.pprint(keyed_rows)

    assert keyed_rows[class_name]["typecode"] == expected_typecode


def test_sending_typecodes():
    nmdc_url = "https://raw.githubusercontent.com/microbiomedata/nmdc-schema/main/src/schema/nmdc.yaml"
    slot_name = "id"

    view_cache = au.ViewCache()
    nmdc_view = view_cache.trust_cache(nmdc_url)

    rows = au.get_typcodes_by_ancestor_whole_schema(view=nmdc_view, slot_name=slot_name)

    au.send_class_typecodes_to_tsv(data=rows, output_file_name="nmdc_class_typecodes.tsv")
