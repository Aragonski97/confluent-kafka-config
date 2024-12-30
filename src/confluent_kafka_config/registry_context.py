#!/usr/bin/env python3
# Copyright 2024 Lazar Jovanovic (https://github.com/Aragonski97)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from confluent_kafka.schema_registry import SchemaRegistryClient
from .utils import create_model_from_avro, import_pydantic_schema, create_pydantic_schema
from .validation import SchemaRegistryConfig

class RegistryContext:

    def __init__(
            self,
            registry_client: SchemaRegistryClient,
            schema_name: str | None = None,
            pydantic_schema_location: str | None = None,
            pydantic_schema_classname: str | None = None
    ) -> None:
        """
        A wrapper around confluent_kafka.schema_registry.SchemaRegistryClient.

        Contains a premade schema registry client and schema information pertaining a given topic.
        Kafka Channels will refer to this class in order to get schema information.
        If schema is not provided in the config_example.yaml file, this class will not be instantiated.

        :param registry_client:
        :param schema_name:
        """

        self.registry_client = registry_client
        self.schema_name = schema_name
        self.pydantic_schema_location = pydantic_schema_location
        self.pydantic_schema_classname = pydantic_schema_classname
        self.schema_latest_version = None
        self.schema_id = None
        self.schema_dict = None
        self.schema_type = None
        self.parsed_schema = None
        self.registered_model = None

    @classmethod
    def build_context(
            cls,
            registry_config: SchemaRegistryConfig
    ) -> 'RegistryContext':
        registry_client = SchemaRegistryClient(registry_config.config)
        return cls(
            registry_client=registry_client,
            schema_name=registry_config.schema_name,
            pydantic_schema_location=registry_config.pydantic_schema_location,
            pydantic_schema_classname=registry_config.pydantic_schema_classname
        )

    def build_from_avro(self):
        if self.pydantic_schema_location and self.pydantic_schema_classname and self.schema_name:
            # will save it by this classname and in this location
            pydantic_model = create_pydantic_schema(
                schema_name=self.schema_name,
                schema_dir_path=self.pydantic_schema_location,
                schema_classname=self.pydantic_schema_classname,
                schema_client=self.registry_client
            )
        elif (not self.pydantic_schema_classname or not self.pydantic_schema_location) and self.schema_name:
            # TODO:
            #  at the moment, it doesn't save it automatically so that the users can decide whether they want
            #  to save the model or not, I should implement this soon:
            pydantic_model = create_model_from_avro(schema=self.schema_dict)
            # save
        elif self.pydantic_schema_location and self.pydantic_schema_classname and not self.schema_name:
            pydantic_model = import_pydantic_schema(
                name=self.pydantic_schema_classname,
                path=self.pydantic_schema_location
            )
            self.schema_name = pydantic_model.__name__
        else:
            err_msg = """Invalid schema.
            schema_name: {self.schema_name},
            pydantic_schema_location: {self.pydantic_schema_location},
            pydantic_schema_classname: {self.pydantic_schema_classname}
            
            Required:
            1) All three --> saves model at location, by name, and returns it
            2) (not pydantic_schema_location or not pydantic_schema_classname) and schema_name --> returns model
            3) pydantic_schema_location and pydantic_schema_classname and not schema_name --> imports from location by name
            """
            raise SyntaxError(err_msg)
        return pydantic_model

    def resolve_schema(self):
        self.schema_latest_version = self.registry_client.get_latest_version(self.schema_name)
        self.schema_id = self.schema_latest_version.schema_id
        self.schema_dict = json.loads(self.schema_latest_version.schema.schema_str)
        self.schema_type = self.schema_latest_version.schema.schema_type

