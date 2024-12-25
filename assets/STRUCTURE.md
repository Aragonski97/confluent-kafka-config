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