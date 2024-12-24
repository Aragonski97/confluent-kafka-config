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
import sys
import os
from pathlib import Path
from typing import Literal


def copy_file(
        src_path: str,
        dest_path: str
) -> None:
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    shutil.copy(src_path, dest_path)
    return

def generate_template(
        config_path: Path | str,
        config_type: Literal['JSON', 'YAML']
) -> None:
    if not Path(config_path).is_dir():
        print(f"Directory does not exist. Creating {config_path}...")
        os.makedirs(config_path)
    src_path = Path(__file__).parent.joinpath(f'config_example.{config_type.lower()}').as_posix()
    target_path = Path(config_path, f'config_example.{config_type.lower()}').as_posix()
    copy_file(src_path=src_path, dest_path=target_path)
    print(f"Template copied to {target_path}")
    return

def entry():
    parser = argparse.ArgumentParser(
        prog='confluent-kafka-config',
        usage='%(prog)s [options]',
        description="confluent-kafka-config CLI utility",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        '--path',
        type=str,
        required=True,
        help="Copy config_example into designated path.",
        default=Path(__file__).parent.as_posix()
    )
    parser.add_argument(
        '--type',
        type=str,
        choices=['YAML', 'JSON'],
        help="Preferred config_example type.",
        required=True,
        default='YAML'
    )
    args = parser.parse_args()
    if args.path and args.type:
        generate_template(config_path=args.path, config_type=args.type)
    else:
        print("No command provided. Use --generate-template [path] --type [type] to generate a config.")