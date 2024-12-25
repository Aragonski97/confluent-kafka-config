# Confluent Kafka Config

A thin wrapper around the [confluent-kafka-python](https://github.com/confluentinc/confluent-kafka-python) library. This wrapper allows for dynamic instantiation of Consumer, Producer, and Admin clients based on configurations provided in a config file in YAML or JSON formats.

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

## Installation

To install this package, run:

```bash
pip install confluent_kafka_config
```



