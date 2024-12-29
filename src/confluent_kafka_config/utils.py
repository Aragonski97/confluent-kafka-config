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

import pydantic_core
from confluent_kafka import KafkaException
from pydantic import BaseModel, create_model
from dataclasses_avroschema.pydantic import AvroBaseModel
from datetime import datetime
from enum import Enum
from typing import Union, Type, Callable
from importlib.util import spec_from_file_location
from confluent_kafka.schema_registry import SchemaRegistryClient
import json

ROOT_DIR = Path(__file__).parent.resolve()


def create_pydantic_schema(
        schema_name: str,
        schemas_dir_path: str | Path,
        schema_config: dict | None = None,
        content: str | None = None
) -> None:
    assert schema_config or content
    if not schemas_dir_path.endswith("/"):
        schemas_dir_path = schemas_dir_path + "/"
    # if schema_registry_url is provided, it will override content arg
    if schema_config:
        try:
            registry_client = SchemaRegistryClient(schema_config)
        except KafkaException as err:
            raise err
        else:
            schema_latest_version = registry_client.get_latest_version(schema_name)
            content = json.loads(schema_latest_version.schema.schema_str)
            model = create_model_from_avro(content)
            model_code = _generate_module_code(model)
            with open(
                    f"{schemas_dir_path}{model.__name__}.py", "w"
            ) as f:
                f.write(model_code)
            return
    else:
        ...
def import_pydantic_schema(
        name: str,
        path: str | Path | None
) -> Type[AvroBaseModel]:
    # location is actually the primary arg, name is not needed, but defined as such in the signature
    module = spec_from_file_location(name=..., location=path)
    pydantic_schema = getattr(module, name)
    if pydantic_schema is None:
        raise TypeError(f"Pydantic schema not found on path: {path}")
    return pydantic_schema

def _generate_module_code(model):
    """Generate Python module code for a Pydantic model."""
    _model_name = model.__name__
    _hints = model.__annotations__
    _fields = model.model_fields
    _module_code = (
        'import typing\n'
        'from dataclasses_avroschema import AvroModel\n'
        'from dataclasses import dataclass\n'
        'from datetime import datetime\n\n'
    )
    _module_code += f"@dataclass\n"
    _module_code += f"class {_model_name}(AvroModel):\n\n"
    _nullable = ""
    _non_nullable = ""
    for _field_name in _hints.keys():

        _field = _fields[_field_name]
        _type = _hints[_field_name]
        _default = _field.get_default()
        if _type is datetime:
            _type = 'datetime'
        if _default is not pydantic_core.PydanticUndefined:
            # _nullable += f"\t{_field_name}: {_type} = AvroField(name='{_field_name}', default={_default})\n"
            _nullable += f"\t{_field_name}: {_type} = {_default}\n"
        else:
            _non_nullable += f"\t{_field_name}: {_type}\n"
    _module_code += _non_nullable + _nullable
    return _module_code

def parse_type(type_string: str | dict) -> type | None:
    if isinstance(type_string, dict):
        primitive_type = type_string.get("type")
        # TODO: Investigate whether there are differences in logicalType to datatime
        # logical_type = type_string.get("logicalType")
        if primitive_type == "long":
            return datetime
        if primitive_type == "enum":
            return Enum
        else:
            raise TypeError(f"Unsupported primitive type {type_string}")
    match type_string:
        case "null":
            return None
        case "boolean":
            return bool
        case "int":
            return int
        case "long":
            return float
        case "float":
            return float
        case "double":
            return float
        case "bytes":
            return bytes
        case "string":
            return str


def parse_record_avro_string_type(field: dict) -> dict:
    _name = field.get('name')
    _type = field.get('type')
    # Because field.get returns None both if 'default' key is not present and
    # if field["default"] is None, so I have to make sure 'default' exists as a key.
    # By the definition of pydantic.create_model(), if Ellipsis (...) is supplied as field default,
    # the pydantic.Field will be required=True, therefore I choose Ellipsis as default in _default.
    _default = ... if 'default' not in field.keys() else field['default']
    _parsed_type = parse_type(_type)
    return {_name: (_parsed_type, _default)}

def parse_avro_record_list_type(field: dict) -> dict:
    _name = field.get('name')
    _types = field.get('type')
    # Because field.get returns None both if 'default' key is not present and
    # if field["default"] is None, I have to check if 'default' exists as a key.
    # By the definition of pydantic.create_model(), if Ellipsis (...) is supplied as field default,
    # the pydantic.Field will be required=True, therefore I choose Ellipsis as default in _default.
    # That being said, if the 'default' in field.keys() and is None, the _parsed_nn_type has to be nullable.
    _default = ... if 'default' not in field.keys() else field['default']
    # Union is set operation, therefore _parsed_subtypes is logically a set
    # even though any positional iterable would work
    _parsed_subtypes = {parse_type(_subtype) for _subtype in _types}
    # Create a Union of Types which can be the type of value.
    _subtype_union = Union[*_parsed_subtypes]
    return {_name: (_subtype_union, _default)}

def parse_avro_record_schema(schema: dict) -> dict:
    assert schema.get('fields') is not None
    # get fields from the schema
    # formatted fields
    formatted_fields = dict()
    for field in schema['fields']:
        if isinstance(field['type'], str):
            formatted_fields.update(parse_record_avro_string_type(field))
        if isinstance(field['type'], list):
            formatted_fields.update(parse_avro_record_list_type(field))
        elif isinstance(field['type'], dict):
            _name = field.get('name')
            _type = field.get('type')
            _parsed_type = parse_type(_type)
            _default = ... if 'default' not in field.keys() else field['default']
            formatted_fields.update({_name: (_parsed_type, _default)})
    return formatted_fields


def create_model_name(schema: dict, prefix: str | None = None) -> str:
    """
    Best naming conventions:
    https://stackoverflow.com/a/47291235
    https://cnr.sh/essays/how-paint-bike-shed-kafka-topic-naming-conventions

        1. Avoid topic names based on things that change.
        2. Avoid topic names based on information that would be stored in other places.
        3. Avoid topic names based on their planned consumers/producers.
        4. Decide casing early on, and consider enforcing it or at least monitor it.

    This function, however, enforces underscores, since this name will be used to create a python module.
    You can't import python-module.py with Pycharm, and I find this notation ugly anyway.
    As for the dots, I don't know enough about python pathing to count on viability of .py modules naming
    with a.b.c.d.e.py since dot is used as access operator in importing.
    Also, lowercase names are enforced.
    """
    _name: str = schema.get('name')
    _namespace: str = schema.get('namespace')
    _type: str = schema.get('type')
    assert (_name or _namespace) and _type
    _processed_name = ""
    if _name:
        _name = _name.replace('-', '_')
        _name = _name.replace('.', '_')
        _processed_name += _name + '_'
    if _namespace:
        _namespace = _namespace.replace('-', '_')
        _namespace = _namespace.replace('.', '_')
        _processed_name += _namespace + '_'
    _type = _type.replace('-', '_')
    _type = _type.replace('.', '_')
    _processed_name += _type
    if prefix:
        _processed_name = prefix + '_' + _processed_name + '_schema'
    return _processed_name.lower()

def create_model_from_avro(schema: dict) -> Type[BaseModel] | Callable:
    """
    Dynamically Creates a model based on schema as per pydantic.create_model function.
    Parses types and makes an adequate format for this function to be called.
    :param schema: Python dictionary containing full Apache AVRO schema.
    :return: A Pydantic model class callable. Not an instance!
    """
    _parsed_schema: dict | None = None
    if schema.get('type') == 'record':
        _parsed_schema = parse_avro_record_schema(schema=schema)
    # cfc stands for confluent-kafka-config
    _model_name: str = create_model_name(schema=schema, prefix='cfc')
    # TODO: Submit ticket to Pydantic repo to reconfigure create_model signature in such a way that
    #  allows for model_name to be used as a key-value combination when calling the function.
    #  As of now, I can't state model_name=_model_name due to * in signature.
    return create_model(
        _model_name,
        __base__=AvroBaseModel,
        **_parsed_schema
    )
