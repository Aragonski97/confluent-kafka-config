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
from structlog import get_logger
from pathlib import Path

class RegistryContext:

    def __init__(
            self,
            registry_client: SchemaRegistryClient,
            schema_name: str,
            pydantic_model_path: str | Path | None = None
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
        self.pydantic_model = None
        self.logger = get_logger()

        self.schema_latest_version = None
        self.schema_id = None
        self.schema_dict = None
        self.schema_type = None
        self.parsed_schema = None
        self.registered_model = None
        if not self.schema_name:
            self.logger.warning(event="Schema missing!")
        else:
            self.resolve_schema()

    def resolve_schema(self):
        self.schema_latest_version = self.registry_client.get_latest_version(self.schema_name)
        self.schema_id = self.schema_latest_version.schema_id
        self.schema_dict = json.loads(self.schema_latest_version.schema.schema_str)
        self.schema_type = self.schema_latest_version.schema.schema_type

