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

from confluent_kafka import Consumer, TopicPartition, Message, KafkaException
from confluent_kafka.serialization import SerializationContext, MessageField
from topic_context import ConsumerTopic
from validation import ClientConfig


class ConsumerContext:

    def __init__(
            self,
            name: str,
            topics: dict[str, ConsumerTopic],
            config: dict
    ) -> None:

        self.name = name
        self.topics = topics
        self.config = config
        self.consumer = Consumer(self.config)

    @classmethod
    def build_context(
            cls,
            client_config: ClientConfig,
    ) -> 'ConsumerContext':
        _topics = dict()
        for _topic in client_config.topics:
            __topic = ConsumerTopic.build_context(_topic)
            _topics[client_config.name] = __topic
        return cls(
            name=client_config.name,
            topics=_topics,
            config=client_config.config
        )

    def subscribe(self) -> None:
        """
        All topics must be either assignable or subscribable, which means either all are passed partitions
        or none of them is.
        """
        assert len(self.topics) > 0
        _type = 'ASSIGN' if list(self.topics.values())[0].partitions else 'SUBSCRIBE'
        if _type == 'ASSIGN':
            partitions = list()
            for _topic in list(self.topics.values()):
                partitions.extend(_topic.partitions)
            print(f"Subscribing to topics: {partitions}.")
            self.consumer.assign(partitions=partitions)
        else:
            _topics_to_subscribe_to = [_topic_name.name for _topic_name in self.topics.values()]
            print(f"Subscribing to topics: {_topics_to_subscribe_to}.")
            self.consumer.subscribe(topics=_topics_to_subscribe_to)



    def _extract_message(
            self,
            msg: Message
    ):
        if msg.error():
            return None
        _topic = None
        for topic in self.topics.values():
            if topic.name == msg.topic():
                _topic = topic
            else:
                raise KafkaException(f"Received a message from: {msg.topic()}, however, not specified in {self.topics.keys()}")
        if _topic is None:
            raise KafkaException(f"Received a message from: {msg.topic()}, however, not specified in {self.topics.keys()}")
        key = msg.key()
        value = msg.value()  # noqa
        topic = msg.topic()
        if _topic.key_serialization_method:
            key = _topic.key_serialization_method(
                msg.key(),
                SerializationContext(msg.topics(), MessageField.KEY)
            )
        if _topic.value_serialization_method:
            value = _topic.value_serialization_method(
                msg.value(),  # noqa
                SerializationContext(msg.topics(), MessageField.VALUE)
            )
        return key, value, topic

    def commit(self, msg: Message):
        # Commit the offset
        tp = TopicPartition(msg.topics(), msg.partition(), msg.offset() + 1)
        self.consumer.commit(offsets=[tp], asynchronous=False)

    def consume(self):
        try:
            msg = self.consumer.poll(3600)
            if msg is None:
                return None
            return self._extract_message(msg=msg)
        except Exception as err:
            self.close()
            raise err

    def close(self):
        self.consumer.close()  # Close consumer gracefully

    def pause(self, topic_name: str):
        self.consumer.pause(partitions=self.topics[topic_name].partitions)

    def resume(self, topic_name: str):
        self.consumer.resume(partitions=self.topics[topic_name].partitions)
