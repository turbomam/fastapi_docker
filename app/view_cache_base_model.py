import logging
from typing import Dict, Optional

from linkml.utils.schema_builder import SchemaBuilder
from linkml_runtime import SchemaView
from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.linkml_model import SchemaDefinition
from pydantic import BaseModel

import logging

# configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ViewCache(BaseModel):
    """Caches multiple LinkML SchemaViews in a dict. The index is the URL of the schema."""

    cache: Dict[str, SchemaView] = {}
    logger = logging.getLogger(__name__)

    def __post_init__(self):
        self.logger = logging.getLogger(__name__)

    def update_from_url(self, url: str):
        """Updates the cache with a new SchemaView, obtained from a url for the schema."""
        try:
            self.cache[url] = SchemaView(url)
            self.logger.info(f"SchemaView at url {url} added to cache")
        except Exception as e:
            self.logger.error(f"Error adding url {url} to cache: {e}")

    def update_from_schema(self, url: str, schema: SchemaDefinition):
        """Updates the cache with a new SchemaView, obtained from a schema."""
        try:
            self.cache[url] = SchemaView(schema)
            self.logger.info(f"SchemaView for schema at url {url} added to cache")
        except Exception as e:
            self.logger.error(f"Error adding schema to cache: {e}")

    def get_view(self, url: str) -> Optional[SchemaView]:
        """Returns a SchemaView from the cache, if it exists."""
        try:
            return self.cache[url]
        except KeyError as e:
            self.logger.error(f"Error getting view from url {url}:{e}")
            return None

    def trust_cache(self, url: str) -> Optional[SchemaView]:
        """Returns a SchemaView from the cache if possible. Otherwise, populates the cache first."""
        if url in self.cache:
            return self.cache[url]
        else:
            try:
                self.update_from_url(url)
                return self.cache[url]
            except Exception as e:
                self.logger.error(f"Error adding url {url} to cache: {e}")
                return None


# view_cache = ViewCache()

# b = SchemaBuilder()
# min_schema = b.schema
#
# view_cache.cache["https://example.com/"] = SchemaView(min_schema)
#
# # view_cache.update_from_schema("https://example.com/", min_schema)
#
# fetched = view_cache.cache["https://example.com/"]
#
# # fetched = view_cache.get_view("https://example.com/")
#
# logger.info(yaml_dumper.dumps(fetched.schema))
