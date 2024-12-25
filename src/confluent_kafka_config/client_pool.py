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


from pathlib import Path
from confluent_kafka.admin import AdminClient
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka_config.consumer_context import ConsumerContext
from confluent_kafka_config.producer_context import ProducerContext
from confluent_kafka_config.validation import KafkaConfig


class ClientPool:

    def __init__(
            self,
            admin: AdminClient | None = None,
            schema_registry: SchemaRegistryClient | None = None,
            producers: dict[str, ProducerContext] | None = None,
            consumers: dict[str, ConsumerContext] | None = None
    ) -> None:
        self.admin = admin
        self.schema_registry = schema_registry
        self.producers = producers
        self.consumers = consumers


    @classmethod
    def from_config(
            cls,
            config_path: Path | str | None
    ):
        kafka_config = KafkaConfig.load_config(config_path)
        if not kafka_config:
            raise SyntaxError(
                "Configuration not correctly written or the config is not properly loaded."
                "Please refer to confluent_kafka_yaml.src.config_example.yaml for an example configuration."
            )
        if kafka_config.admin:
            admin = AdminClient(kafka_config.admin.config)
        else:
            raise ValueError("Kafka admin section missing from config.")
        if kafka_config.schema_registry:
            schema_registry = SchemaRegistryClient(kafka_config.schema_registry.model_dump())
        else:
            raise ValueError("Kafka schema registry section missing from config.")
        consumers: dict[str, ConsumerContext] = dict()
        producers: dict[str, ProducerContext] = dict()
        if kafka_config.consumers:
            for consumer_config in kafka_config.consumers:
                consumer = ConsumerContext(**consumer_config.model_dump())
                consumer.configure(registry_client=schema_registry)
                assert consumers.get(consumer.name) is None
                consumers[consumer.name] = consumer
        if kafka_config.producers:
            for producer_config in kafka_config.producers:
                producer = ProducerContext(**producer_config.model_dump())
                producer.configure(registry_client=schema_registry)
                assert producers.get(producer.name) is None
                producers[producer.name] = producer

        return cls(
            admin=admin,
            schema_registry=schema_registry,
            producers=producers,
            consumers=consumers,
        )
