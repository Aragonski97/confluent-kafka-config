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


import yaml
import json
from io import TextIOWrapper
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from pathlib import Path


class AdminConfig(BaseModel):
    config: dict

class SchemaRegistryConfig(BaseModel):
    url: str

class TopicConfig(BaseModel):
    name: str
    partitions: list[int] | None = Field(default=None)
    schema_name: str | None = Field(default=None)

class ClientConfig(BaseModel):
    name: str
    topic: TopicConfig | None = Field(default=None)
    config: dict

class KafkaConfig(BaseSettings):
    admin: AdminConfig
    schema_registry: SchemaRegistryConfig
    consumers: list[ClientConfig] | None = Field(default=None)
    producers: list[ClientConfig] | None = Field(default=None)

    class Config:
        case_sensitive = False
        # docker container path
        secrets_dir = '/run/secrets'

    @classmethod
    def from_yaml(
            cls,
            path: Path | str | None = None,
            file_io: TextIOWrapper | None = None
    ):
        try:
            if file_io is not None:
                data = yaml.safe_load(file_io)
                return cls(**data)
            if path is None:
                raise ValueError("Neither path nor file is specified.")
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
            return cls(**data)
        except (yaml.YAMLError, FileNotFoundError) as err:
            ...

    @classmethod
    def from_json(
            cls,
            path: Path | str | None = None,
            file_io: TextIOWrapper | None = None
    ):
        try:
            if file_io is not None:
                data = json.load(file_io)
                return cls(**data)
            if path is None:
                raise ValueError("Neither path nor file is specified.")
            with open(path, 'r') as f:
                data = json.load(f)
            return cls(**data)
        except (json.JSONDecodeError, FileNotFoundError) as err:
            ...

    @classmethod
    def load_config(
            cls,
            config_path: Path | str | None,
    ) -> 'KafkaConfig':
        if config_path is None:
            raise FileNotFoundError("Neither path nor file is specified.")
        if config_path.endswith('.json'):
            cb = KafkaConfig.from_json
        elif config_path.endswith('.yaml'):
            cb = KafkaConfig.from_yaml
        else:
            raise TypeError('config_path must be of type "json" or "yaml".')
        with open(config_path, 'r') as f:
            return cb(file_io=f, path=config_path)
