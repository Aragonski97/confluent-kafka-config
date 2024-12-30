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

from dataclasses_avroschema.pydantic import AvroBaseModel
import fastavro
from confluent_kafka import TopicPartition
from confluent_kafka.serialization import StringDeserializer, StringSerializer
from confluent_kafka.schema_registry.avro import AvroDeserializer, AvroSerializer
from .registry_context import RegistryContext
from .validation import TopicConfig


class TopicContext:

    def __init__(
            self,
            name: str,
            registry_context: RegistryContext | None = None,
            partitions: list[int] | None = None,
            pydantic_model: AvroBaseModel | None = None

    ):
        self.name = name
        self.registry_context = registry_context
        self.partitions = [TopicPartition(self.name, partition=p) for p in partitions] if partitions else None
        self.pydantic_model = pydantic_model
        self.key_serialization_method = None
        self.value_serialization_method = None

    def __repr__(self):
        return self.name

    @classmethod
    def build_context(
            cls,
            topic_config: TopicConfig
    ) -> 'TopicContext':
        registry_context = RegistryContext.build_context(topic_config.registry_config)
        if not registry_context.schema_name:
            print(f"Schema not supplied for topic: {topic_config.name}.")
            return cls(
                name=topic_config.name,
                partitions=topic_config.partitions,
                registry_context=registry_context,
            )
        else:
            print(f"Using schema: {registry_context.schema_name} for {topic_config.name}.")
            registry_context.resolve_schema()
            if registry_context.schema_type is None:
                return cls(
                    name=topic_config.name,
                    partitions=topic_config.partitions,
                    registry_context=registry_context,
                )
            if registry_context.schema_type == "AVRO":
                pydantic_model = registry_context.build_from_avro()
                return cls(
                    name=topic_config.name,
                    partitions=topic_config.partitions,
                    registry_context=registry_context,
                    pydantic_model=pydantic_model
                )
            else:
                raise NotImplementedError("Other types not implemented yet!")
class ProducerTopic(TopicContext):

    def _configure_json_serialization(self) -> None:
        print("Json schema not implemented yet!")
        raise TypeError("Json schema not implemented yet!")

    def _configure_avro_serialization(self) -> None:
        self.registry_context.parsed_schema = fastavro.parse_schema(self.registry_context.schema_dict)
        self.value_serialization_method = AvroSerializer(
            schema_registry_client=self.registry_context.registry_client,
            schema_str=self.registry_context.schema_latest_version.schema.schema_str,
            to_dict=lambda obj, ctx: self.registry_context.registered_model.model_dump(obj, context=ctx)
        )
        self.key_serialization_method = StringSerializer('utf_8')
        print(f"Avro serialization set for {self.name}")

    def _configure_protobuf_serialization(self) -> None:
        print("Protobuf schema not implemented yet!")
        raise TypeError("Protobuf schema not implemented yet!")

    def _configure_serialization(self) -> None:
        if not self.registry_context:
            return
        match self.registry_context.schema_type:
            case "JSON":
                self._configure_json_serialization()
            case "AVRO":
                self._configure_avro_serialization()
            case "PROTOBUF":
                self._configure_protobuf_serialization()
            case _:
                print(f"Schema of type {self.registry_context.schema_type} not recognized")
                raise ValueError(f"Schema of type {self.registry_context.schema_type} not recognized")

class ConsumerTopic(TopicContext):

    def _configure_json_deserialization(self) -> None:
        print("Json schema not implemented yet!")
        raise TypeError("Json schema not implemented yet!")

    def _configure_avro_deserialization(self) -> None:
        self.pydantic_model = self.registry_context.build_from_avro()
        self.registry_context.parsed_schema = fastavro.parse_schema(self.registry_context.schema_dict)
        self.registry_context.parsed_schema = self.pydantic_model.validate_schema()
        self.value_serialization_method = AvroDeserializer(
            schema_registry_client=self.registry_context.registry_client,
            schema_str=self.registry_context.schema_latest_version.schema.schema_str,
            from_dict=lambda obj, ctx: self.pydantic_model.model_validate(obj, context=ctx)
        )
        self.key_serialization_method = StringDeserializer('utf_8')
        print(f"Avro serialization set for {self.name}")

    def _configure_protobuf_deserialization(self) -> None:
        print("Protobuf schema not implemented yet!")
        raise TypeError("Protobuf schema not implemented yet!")

    def configure_deserialization(self) -> None:
        if not self.registry_context:
            return
        match self.registry_context.schema_type:
            case "JSON":
                self._configure_json_deserialization()
            case "AVRO":
                self._configure_avro_deserialization()
            case "PROTOBUF":
                self._configure_protobuf_deserialization()
            case _:
                print(f"Schema of type {self.registry_context.schema_type} not recognized")
                raise ValueError(f"Schema of type {self.registry_context.schema_type} not recognized")