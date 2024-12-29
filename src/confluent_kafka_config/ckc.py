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



import argparse
import shutil
from pathlib import Path
from typing import Literal
from ast import literal_eval
from utils import create_pydantic_schema

def generate_template(
        config_location: Path | str,
        config_type: Literal['JSON', 'YAML']
) -> None:
    if not Path(config_location).is_dir():
        print(f"Directory does not exist. Creating {config_location}...")
        Path(config_location).mkdir(parents=True, exist_ok=True)
    src_path = Path(__file__).joinpath(f'config_example.{config_type.lower()}').as_posix()
    target_path = Path(config_location, f'config_example.{config_type.lower()}').as_posix()
    shutil.copy(src_path, target_path)
    print(f"Template copied to {target_path}")
    return

def entry():
    parser = argparse.ArgumentParser(
        prog='ckc',
        usage='%(prog)s [options]',
        description="confluent-kafka-config CLI utility",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    # Add subparsers to handle subcommands
    subparsers = parser.add_subparsers(
        dest="command",
        help="subcommands",
        required=True
    )

    pydantic_parser = subparsers.add_parser(
        name='pydantic',
        description="confluent-kafka-config CLI utility to convert Kafka Schemas into Pydantic Schemas",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    pydantic_parser.add_argument(
        "--registry-config",
        "-c",
        type=str,
        required=True,
        help="Kafka Registry URL to choose pydantic schemas based on name",
    )
    pydantic_parser.add_argument(
        "--schema-name",
        "-n",
        required=True,
        type=str,
        help="Kafka schema name to use."
    )
    pydantic_parser.add_argument(
        "--output",
        "-o",
        required=True,
        type=str,
        help="A place to put converted schemas"
    )

    config_parser = subparsers.add_parser(
        name='config',
        description="confluent-kafka-config CLI utility generate config file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    config_parser.add_argument(
        '--output',
        '-o',
        type=str,
        required=True,
        help="Copy config_example into designated path.",
        default=Path(__file__).parent.as_posix()
    )
    config_parser.add_argument(
        '--type',
        '-t',
        type=str,
        choices=['YAML', 'JSON'],
        help="Preferred config_example type.",
        required=True,
        default='YAML'
    )


    # Main argument parsing
    args = parser.parse_args()

    # Handle subcommands
    if args.command == "pydantic":
        try:
            create_pydantic_schema(
                schema_name=args.schema_name,
                schemas_dir_path=args.output,
                schema_config=literal_eval(args.registry_config)
            )
        except Exception as err:
            raise err
    elif args.command == "config":
        try:
            generate_template(
                config_location=args.output,
                config_type=args.type
            )
        except Exception as err:
            raise err
    else:
        print("No command provided. Use --generate-template [path] --type [type] to generate a config.")

if __name__ == "__main__":
    entry()