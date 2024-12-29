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

from structlog import get_logger
from confluent_kafka import TopicPartition
from confluent_kafka.admin import AdminClient
from typing import Callable
from pathlib import Path
from registry_context import RegistryContext
from utils import create_model_from_avro, import_pydantic_schema
import re


class TopicContext:

    def __init__(
            self,
            name: str,
            registry_context: RegistryContext | None = None,
            # def partitioner(key: str) -> int --> Callable[[str], int]
            partitions: list[int] | Callable[[str], int] | None = None,
            pydantic_schema_location: str | Path | None = None
    ):
        self.name = name
        self.partitions = partitions

        self.registry_context = registry_context
        self._logger = get_logger()
        self.pydantic_schema_location = pydantic_schema_location
        self.pydantic_model = None
        self.partitions = list()
        self.key_serialization_method = None
        self.value_serialization_method = None


    def build_from_avro(self):
        if self.registry_context:
            if not self.pydantic_schema_location:
                self.pydantic_model = create_model_from_avro(schema=self.registry_context.schema_dict)
            else:
                formatted_name = re.sub(r"", "", self.pydantic_schema_location)
                import_pydantic_schema(
                    name=self.registry_context.schema_name
                )
        else:
            self._logger.warning(f"No supplied schema")


    def get_partitions(self, admin_client: AdminClient):
        metadata = admin_client.list_topics(self.name, timeout=10)
        self.partitions = metadata.topic_contexts[self.name].partitions.keys()
        return self.partitions

    def get_topic_partitions(self):
        return [TopicPartition(topic=self.name, partition=partition) for partition in self.partitions]

