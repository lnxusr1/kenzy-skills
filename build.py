import sys
import os
import shutil
from pathlib import Path
import json
import zipfile

fldr = os.path.dirname(__file__)
source_folder = os.path.join(fldr, "src")
api_folder = os.path.join(fldr, "api")

src_fldr = os.path.normpath(os.path.join(fldr, "..", "kenzy"))
sys.path.insert(0, os.path.join(src_fldr, "src"))
sys.path.insert(0, source_folder)

inventory = {}
with open(os.path.join(os.path.dirname(__file__), "README.md"), "w", encoding="UTF-8") as ks:
    ks.write("# KENZY.Ai Skills &middot; [![GitHub license](https://img.shields.io/github/license/lnxusr1/kenzy-skills)](https://github.com/lnxusr1/kenzy-skills/blob/master/LICENSE) ![Python Versions](https://img.shields.io/pypi/pyversions/yt2mp3.svg)\n\n")
    ks.write("Skills for kenzy.skillmanager\n\n")

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

                if os.path.isfile(os.path.join(source_folder, skill_name, "README.md")):
                    shutil.copy(os.path.join(source_folder, skill_name, "README.md"), os.path.join(src_fldr, "docs", f"kenzy.skills.{skill_name}.md"))
                    ks.write(f"* [{skill_name}](https://docs.kenzy.ai/en/latest/kenzy.skills.{skill_name}/) - {skill.version}\n")
                else:
                    ks.write(f"* {skill_name} - {skill.version}\n")
                    
            except:
                pass

    ks.write("\n-----\n\n## Help & Support\n\nHelp and additional details is available at [https://kenzy.ai](https://kenzy.ai)")

with open(os.path.join(api_folder, "inventory.json"), "w", encoding="UTF-8") as sw:
    json.dump(inventory, sw, indent=4)

shutil.copy(os.path.join(os.path.dirname(__file__), "README.md"), os.path.join(src_fldr, "docs", "kenzy.skills.md"))