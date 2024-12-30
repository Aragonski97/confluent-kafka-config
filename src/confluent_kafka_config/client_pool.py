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

from pathlib import Path
from confluent_kafka.admin import AdminClient
from consumer_context import ConsumerContext
from producer_context import ProducerContext
from validation import KafkaConfig, ClientConfig


class ClientPool:

    def __init__(
            self,
            admin: AdminClient | None = None,
            producers: dict[str, ProducerContext] | None = None,
            consumers: dict[str, ConsumerContext] | None = None,
            assets_path: str | None = None
    ) -> None:
        self.admin = admin
        self.producers = producers
        self.consumers = consumers
        self.assets_path = assets_path


    @classmethod
    def from_config(
            cls,
            config_path: Path | str | None
    ) -> 'ClientPool':
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
        consumers: dict[str, ConsumerContext] = dict()
        producers: dict[str, ProducerContext] = dict()
        if kafka_config.consumers:
            for consumer_config in kafka_config.consumers:
                consumer_config: ClientConfig
                consumer = ConsumerContext.build_context(consumer_config)
                consumer.subscribe()
                consumers[consumer.name] = consumer
        if kafka_config.producers:
            for producer_config in kafka_config.producers:
                producer_config: ClientConfig
                producer = ProducerContext.build_context(producer_config)

                producers[producer.name] = producer

        return cls(
            assets_path=kafka_config.assets_path,
            admin=admin,
            producers=producers,
            consumers=consumers,
        )