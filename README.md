# Confluent Kafka Config

A thin wrapper around the [confluent-kafka-python](https://github.com/confluentinc/confluent-kafka-python) library. This wrapper allows for dynamic instantiation of Consumer, Producer, and Admin clients based on configurations provided in a config file in YAML or JSON formats.


## Installation

To install this package, run:

```bash
pip install confluent_kafka_config
```

## Structure of config file
```
admin
   └── config
       └── bootstrap.servers:  < host:port >
schema_registry
   └── url:                    < http's://host:port >

consumers < list of dictionaries >
   ├── name:                   < some consumer name, random >
   ├── topic 
   │   ├── name:               < topic name >
   │   ├── partitions:         < a list of partition numbers to consume from, or leave empty >
   │   └── schema_name:        < schema name to use with topic >
   └── config                  < confluent_kafka.Consumer conf >
       ├── bootstrap.servers:  < host:port >
       ├── group.id:           < group name >
       └── ...
       
producers < list of dictionaries >                 
   ├── name:                   < some producer name, random >
   ├── topic 
   │   ├── name:               < topic name >
   │   ├── partitions:         < a list of partition numbers to produce to, or leave empty >
   │   └── schema_name:        < schema name to use with topic >
   └── config                  < confluent_kafka.Producer conf >
       ├── bootstrap.servers:  < host:port >
       ├── acks:               < 0, 1, etc. >
       └── ...
```
## Docs:
### Definitions:
- Client: Either an instance of ProducerContext or ConsumerContext

⚠️ **Warning:** At present, each client expects a single topic with single schema. This will be resolved in the future: https://github.com/Aragonski97/confluent-kafka-config/issues/16

### ClientPool
A wrapper class that contains all consumers / producers instantiated based on config file.
Load ClientPool by calling its class factory function:
```python
from confluent_kafka_config.client_pool import ClientPool

pool = ClientPool.from_config(<path_to_your_config_file>)

# access consumers
#pool.consumers : dict[str, ConsumerContext]

# access producers
#pool.producers: dict[str, ProducerContext]

# get specific consumer by name is pool.consumers[<consumer name>]
# same for producers
# overriden __getitem__ will be implemented in the future: https://github.com/Aragonski97/confluent-kafka-config/issues/15
```
### RegistryContext
A wrapper around ```confluent_kafka.SchemaRegistryClient``` that includes the given schema indended for a client specified in config file.
Based on the schema, a function ```confluent_kafka_config.RegistryContext.create_registered_model``` creates a model based on the schema definied in the registry.
This model is used for deserialization and serialization.

### TopicContext
A wrapper around ```confluent_kafka.TopicPartition``` class that includes not only the topic name and partitions, but also a registered schema specified in the config file.

### ConsumerContext
A wrapper around ```confluent_kafka.Consumer``` class that includes a given ```confluent_kafka_config.TopicContext```.
The function ```confluent_kafka_config.ConsumerContext.consume``` is an exposed version of ```confluent_kafka.Consumer.consume``` which handles some errors.
This error handling will be extensively covered in the future: https://github.com/Aragonski97/confluent-kafka-config/issues/17

### ProducerContext
Almost identical to ConsumerContext, just pertaining ```confluent_kafka.Producer``` class.

### KafkaConfig
A pydantic schema used for loading the config file. Embedded validation, etc.



