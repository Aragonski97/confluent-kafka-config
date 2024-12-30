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

from confluent_kafka import Producer, Message, KafkaError
from confluent_kafka.serialization import SerializationContext, MessageField
from pydantic import BaseModel
from .validation import ClientConfig
from .topic_context import ProducerTopic


class ProducerContext:

    def __init__(
            self,
            name: str,
            topics: dict[str, ProducerTopic],
            config: dict
    ) -> None:

        self.name = name
        self.topics = topics
        self.config = config
        self.consumer: Producer | None = None

    @classmethod
    def build_context(
            cls,
            client_config: ClientConfig,
    ) -> 'ProducerContext':
        _topics = dict()
        for _topic in client_config.topics:
            __topic = ProducerTopic.build_context(_topic)
            _topics[client_config.name] = __topic
        return cls(
            name=client_config.name,
            topics=_topics,
            config=client_config.config
        )

    def produce(
            self,
            key: str,
            value: BaseModel,
    ) -> None:

        # Manually commit the offset for this partition only
        if not self.topic:
            self._logger.warning("Subject by that name doesn't exist")
            return
        try:
            if self.topic.registry_context:
                key = self.topic.key_serialization_method(key, SerializationContext(self.topic.name, MessageField.KEY))
                value = self.topic.value_serialization_method(
                    value, SerializationContext(self.topic.name, MessageField.VALUE)
                )
            else:
                key = self.topic.key_serialization_method(key, SerializationContext(self.topic.name, MessageField.KEY))
                value = value.model_dump_json(indent=True, exclude_none=True)
            # will override internal partitioner logic
            if self.topic.partitioner:
                for partition in self.topic.partitioner:
                    self._producer.produce(
                        topic=self.topic.name,
                        partition=partition,
                        key=key,
                        value=value,
                        on_delivery=self.delivery_report
                    )
            else:
                self._producer.produce(
                    topic=self.topic.name,
                    key=key,
                    value=value,
                    on_delivery=self.delivery_report
                )
                return
        except Exception as err:
            self._logger.warning(err)
            raise err

    def delivery_report(self, err: KafkaError, msg: Message):
        if err is not None:
            self._logger.info("Delivery failed for User record {}: {}".format(msg.key(), err))
            return
        self._logger.info('User record {} successfully produced to {} [{}] at offset {}'.format(
            msg.key(), msg.topics(), msg.partition(), msg.offset()))



