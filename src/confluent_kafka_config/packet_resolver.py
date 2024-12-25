import json
from pathlib import Path

ROOT_DIR = Path(__file__).parent.resolve()




# Step 1: Read the Pipfile.lock
with open(ROOT_DIR.parent.parent.joinpath("Pipfile.lock"), "r") as f:
    lock_data = json.load(f)

# Step 2: Extract package versions
package_versions = {
    package: details["version"]
    for package, details in lock_data.get("default", {}).items()
}

dev_package_versions = {
    package: details["version"]
    for package, details in lock_data.get("develop", {}).items()
}

# Step 3: Update the Pipfile
pipfile_lines = []
with open(ROOT_DIR.parent.parent.joinpath("Pipfile"), "r") as f:

    in_default = in_develop = False
    for line in f:
        stripped = line.strip()

        if stripped == "[packages]":
            in_default = True
            in_develop = False
        elif stripped == "[dev-packages]" or stripped == "[develop]":
            in_default = False
            in_develop = True
        elif in_default:
            package = stripped.split("=")[0].strip().lower()
            if package in package_versions:
                line = f"{package} = \"{package_versions[package]}\"\n"
        elif in_develop:
            package = stripped.split("=")[0].strip().lower()
            if package in dev_package_versions:
                line = f"{package} = \"{dev_package_versions[package]}\"\n"

        pipfile_lines.append(line)

# Step 4: Save the modified Pipfile

with open(ROOT_DIR.parent.parent.joinpath("Pipfile"), "w") as f:
    f.writelines(pipfile_lines)