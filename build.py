import sys
import os
from pathlib import Path
import json
import zipfile

fldr = os.path.dirname(__file__)
source_folder = os.path.join(fldr, "src")
api_folder = os.path.join(fldr, "api")

sys.path.insert(0, os.path.normpath(os.path.join(fldr, "..", "kenzy", "src")))
sys.path.insert(0, source_folder)

inventory = {}
for skill_name in os.listdir(source_folder):
    if os.path.isdir(os.path.join(source_folder, skill_name)):
        try:
            exec(f"import {skill_name}")
            skill = eval(f"{skill_name}.create_skill()")

            inventory[skill_name] = {
                "path": skill_name,
                "name": skill.name,
                "description": skill.description,
                "version": skill.version
            }

            os.makedirs(os.path.join(api_folder, "pkg", skill_name), exist_ok=True)
            with zipfile.ZipFile(os.path.join(api_folder, "pkg", skill_name, str(skill.version) + ".zip"), "w", zipfile.ZIP_DEFLATED) as z:
                files = Path(os.path.join("src", skill_name)).rglob("*")
                for fname in files:
                    file_name = str(fname)
                    if os.path.basename(file_name).startswith("."):
                        continue
                    
                    if "__pycache__" in file_name:
                        continue

                    z.write(file_name, file_name[len(os.path.join("src")):])
        except:
            pass

with open(os.path.join(api_folder, "inventory.json"), "w", encoding="UTF-8") as sw:
    json.dump(inventory, sw, indent=4)
