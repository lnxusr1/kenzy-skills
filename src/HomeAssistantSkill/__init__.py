import os
import requests
import tempfile
import json
import time
import threading
from kenzy import GenericSkill
from kenzy.extras import strip_punctuation


class HomeAssistantSkill(GenericSkill):
    """
    Skill to tell a joke
    """

    def __init__(self, **kwargs):
        """
        Home Assistant Skill Initialization
        """

        super().__init__(**kwargs)

        self.token = None
        self.url = None
        self.area_alias_overrides = {}

        self._headers = {}
        self._intent_map = {}
        self._dev_timers = {}
        self._timer_running = threading.Event()
        self._timer_running.clear()
        self._timer_thread = None
        self._timer_delay = 0
        self._triggers = []

        self._file_lights = os.path.join(tempfile.gettempdir(), "ha_lights")
        self._file_covers = os.path.join(tempfile.gettempdir(), "ha_covers")
        self._file_locks = os.path.join(tempfile.gettempdir(), "ha_locks")
        self._file_areas = os.path.join(tempfile.gettempdir(), "ha_areas")

        self.name = "HomeAssistantSkill"
        self.description = "Control HomeAssistant lights, fans, covers, and doors"
        self._version = [1, 1, 5]

        self.logger.debug(f"{self.name} loaded successfully.")

    def initialize(self):
        """
        Load intent files for Home Assistant Skill

        Returns:
            (bool): True on success else raises an exception
        """

        # Get Data
        self.token = self.get_setting("token")
        self.url = self.get_setting("url")
        self.area_alias_overrides = self.get_setting("area_aliases")
        self.entity_alias_overrides = self.get_setting("entity_aliases")
        self._timer_delay = self.get_setting("timer_delay", 0.5)
        self._triggers = self.get_setting("triggers", [])

        if self.url is None or self.token is None:
            return False

        self.url = str(self.url).rstrip("/")

        self._headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        self._load_intent_map()
        self._create_intents_from_map()

        self.register_entity_file(f"{self._file_lights}.entity")
        self.register_entity_file(f"{self._file_covers}.entity")
        self.register_entity_file(f"{self._file_locks}.entity")
        self.register_entity_file(f"{self._file_areas}.entity")

        self.register_entity_file("ha_type.entity")
        self.register_entity_file("ha_on_off.entity")
        self.register_entity_file("ha_raise_lower.entity")
        self.register_entity_file("ha_lock_unlock.entity")

        self.register_intent_file("ha_list.intent", self.handle_homeassistant_intent_list)

        if str(self.get_setting("lights", "enable")).lower().strip() == "enable":
            self.register_intent_file(
                f"{self._file_lights}.intent",
                self.handle_homeassistant_intent_lights
            )

        if str(self.get_setting("covers", "enable")).lower().strip() == "enable":
            self.register_intent_file(
                f"{self._file_covers}.intent",
                self.handle_homeassistant_intent_covers
            )

        if str(self.get_setting("locks", "enable")).lower().strip() == "enable":
            self.register_intent_file(
                f"{self._file_locks}.intent",
                self.handle_homeassistant_intent_locks
            )

        self.register_type_trigger("kenzy.image", self.handle_homeassistant_image_trigger)

        self._timer_thread = threading.Thread(target=self._image_timer, daemon=True)
        self._timer_thread.start()

        self.logger.debug(f"{self.name} initialized.")
        return True

    def _create_type_file(self, types, file_name):
        device_names = []

        for type_id in types:
            for a_alias in self._intent_map.get(type_id):
                for device_name in self._intent_map.get(type_id).get(a_alias):

                    if device_name not in device_names:
                        device_names.append(device_name)
                        if (device_name.endswith("light") 
                                or device_name.endswith("fan") 
                                or device_name.endswith("lamp")) \
                                and f"{device_name}s" not in device_names:

                            device_names.append(f"{device_name}s")

        with open(file_name, "w", encoding="UTF-8") as sw:
            for item in device_names:
                sw.write(item.replace("'", "") + "\n")

    def _load_intent_map(self):
        if self.url is None or self.token is None:
            return False

        self.logger.debug("Downloading area list...")
        resp_areas = requests.post(
            f"{self.url}/api/template",
            headers=self._headers,
            timeout=30,
            json={"template": "{{ areas() }}"}
        )

        if not resp_areas.ok:
            self.logger.error("Unable to download area list")
            return False

        areas_list = {}
        for item in json.loads(resp_areas.text.strip().replace("'", "\"")):
            areas_list[item] = {"alias": None, "devices": []}

        for item in areas_list:
            self.logger.debug(f"Processing area = {item}...")

            resp_alias = requests.post(
                f"{self.url}/api/template",
                headers=self._headers,
                timeout=30,
                json={"template": str("{{ area_name('%s') }}" % item)}
            )
            if not resp_alias.ok:
                self.logger.error("Unable to download area alias")
                return False

            areas_list[item]["friendly_name"] = resp_alias.text
            areas_list[item]["alias"] = resp_alias.text if item not in self.area_alias_overrides else self.area_alias_overrides[item]

            resp_area_devs = requests.post(
                f"{self.url}/api/template",
                headers=self._headers,
                timeout=30,
                json={"template": str("{{ area_entities('%s') }}" % item)}
            )

            if not resp_area_devs.ok:
                self.logger.error("Unable to download area device list")
                return False

            areas_list[item]["devices"] = json.loads(
                resp_area_devs.text.strip().replace("'", "\"")
            )

        self.logger.debug("Downloading device list...")

        resp_devs = requests.get(
            f"{self.url}/api/states",
            headers=self._headers,
            timeout=30
        )

        if not resp_devs.ok:
            self.logger.error("Unable to download device list")
            return False

        area_dev_map = {"light": {}, "cover": {}, "lock": {}}

        for item in resp_devs.json():
            entity_id = item.get("entity_id")
            if entity_id.split(".", 1)[0] in ["light", "fan", "cover", "lock"]:
                friendly_name = item.get("attributes", {}).get("friendly_name")

                area_id = None
                for area in areas_list:
                    if entity_id in areas_list.get(area).get("devices", []):
                        area_id = area
                        break

                entity_name = friendly_name.lower().strip()
                short_name = entity_name
                area_alias = areas_list.get(area_id).get("alias", "").replace("'", "").lower()

                if area_id is not None:
                    n = areas_list.get(area_id).get("friendly_name", "").lower()

                    if n != "":
                        short_name = entity_name.replace(n, "").strip()
                        entity_name = entity_name.replace(n, area_alias).strip()

                type_id = entity_id.split(".", 1)[0].lower()

                if str(type_id if type_id != "fan" else "light") not in area_dev_map:
                    area_dev_map[type_id if type_id != "fan" else "light"] = {}

                if area_alias not in area_dev_map.get(type_id if type_id != "fan" else "light"):
                    area_dev_map[type_id if type_id != "fan" else "light"][area_alias] = {}

                short_name = short_name[:-1] if short_name.endswith("lights") or short_name.endswith("fans") or short_name.endswith("lamps") else short_name

                # package = area_dev_map[type_id]
                package = area_dev_map[type_id if type_id != "fan" else "light"][area_alias]

                package[short_name.replace("'", "")] = {
                    "name": entity_name,
                    "area_id": area_id,
                    "entity_id": entity_id,
                    "friendly_name": friendly_name,
                    "short_name": short_name,
                    "type": type_id
                }

                if isinstance(self.entity_alias_overrides, dict):
                    for id in self.entity_alias_overrides:
                        if id == entity_id:
                            if isinstance(self.entity_alias_overrides.get(id), list):
                                for entry in self.entity_alias_overrides.get(id):
                                    short_name = entry.lower().strip()
                                    package[short_name.replace("'", "")] = {
                                        "name": entity_name,
                                        "area_id": area_id,
                                        "entity_id": entity_id,
                                        "friendly_name": friendly_name,
                                        "short_name": short_name,
                                        "type": type_id
                                    }
                            else:
                                short_name = self.entity_alias_overrides.get(id).lower().strip()
                                package[short_name.replace("'", "")] = {
                                    "name": entity_name,
                                    "area_id": area_id,
                                    "entity_id": entity_id,
                                    "friendly_name": friendly_name,
                                    "short_name": short_name,
                                    "type": type_id
                                }

        # self.logger.debug(json.dumps(area_dev_map, indent=4))
        self._intent_map = area_dev_map

        return True

    def _create_intents_from_map(self):
        self._create_entity_for_areas()
        self._create_intents_from_map_lights()
        self._create_intents_from_map_locks()
        self._create_intents_from_map_covers()

    def _create_entity_for_areas(self):
        areas_list = []

        file_name = f"{self._file_areas}.entity"
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        with open(file_name, "w", encoding="UTF-8") as sw:
            for area_alias in self._intent_map.get("light"):
                if area_alias not in areas_list:
                    areas_list.append(area_alias)
                    sw.write(area_alias.replace("'", "") + "\n")

            for area_alias in self._intent_map.get("cover"):
                if area_alias not in areas_list:
                    areas_list.append(area_alias)
                    sw.write(area_alias.replace("'", "") + "\n")

    def _create_intents_from_map_lights(self):
        file_name = f"{self._file_lights}.intent"
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        with open(file_name, "w", encoding="UTF-8") as sw:
            sw.write("(please |) turn {ha_on_off} (all |) (the |) {ha_type} (in this |) (room | location | place |)\n")
            sw.write("(please |) turn {ha_on_off} (all |) (the |) {ha_lights} (in this |) (room | location | place |)\n")
            sw.write("(please |) turn (all |) (the |) {ha_type} {ha_on_off} (in this |) (room | location | place |)\n")
            sw.write("(please |) turn (all |) (the |) {ha_lights} {ha_on_off} (in this |) (room | location | place |)\n")

            sw.write("(please |) turn {ha_on_off} (all |) (the |) {ha_area} {ha_lights}\n")
            sw.write("(please |) turn (the |) {ha_area} {ha_lights} (all |) {ha_on_off}\n")
            sw.write("(please |) turn {ha_on_off} (all |) (the |) {ha_lights} (in | on | under | over | at |) (the |) {ha_area}\n")
            sw.write("(please |) turn (all |) (the |) {ha_lights} (in | on | under | over | at |) (the |) {ha_area} {ha_on_off}\n")
            sw.write("(please |) turn (all |) (the |) {ha_lights} {ha_on_off} (in | on | under | over | at |) (the |) {ha_area}\n")

        self._create_type_file(["light"], f"{self._file_lights}.entity")

    def _create_intents_from_map_locks(self):
        file_name = f"{self._file_locks}.intent"
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        with open(file_name, "w", encoding="UTF-8") as sw:
            sw.write("(please |) {ha_lock_unlock} (the |) {ha_locks}\n")

        self._create_type_file(["lock"], f"{self._file_locks}.entity")

    def _create_intents_from_map_covers(self):
        file_name = f"{self._file_covers}.intent"
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        with open(file_name, "w", encoding="UTF-8") as sw:
            sw.write("(please |) {ha_raise_lower} (the |) {ha_area} {ha_covers}\n")
            sw.write("(please |) {ha_raise_lower} (the |) {ha_covers} (in | on | under | at) the {ha_area}\n")

        self._create_type_file(["cover"], f"{self._file_covers}.entity")

    def handle_homeassistant_intent(self, message, context=None, **kwargs):
        """
        Primary function for intent matches.  Called by skill manager.

        Args:
            message (obj):  text that triggered the intent
            context (KContext): Context surrounding the request. (optional)

        Returns:
            (bool): True on success or False on failure
        """

        text = self.getMessageFromDialog("homeassistant.dialog")
        if (text != ""):
            return self.say(text, context=context)

        return False

    def handle_homeassistant_intent_list(self, message, context=None, **kwargs):
        entity = message.matches.get("ha_type", "").replace(".", "").lower()
        area = message.matches.get("ha_area", context.location).replace(".", "").lower()

        type_id = ""
        sub_type = ""
        if "light" in entity:
            type_id = "light"
            sub_type = "light"
        elif "lamp" in entity:
            type_id = "light"
            sub_type = "lamp"
        elif "fan" in entity:
            type_id = "light"
            sub_type = "fan"
        elif "lock" in entity:
            type_id = "lock"
            sub_type = "lock"
        else:
            type_id = "cover"
            sub_type = "cover"

        self.logger.debug("==< LIST >================================")
        self.logger.debug(f"TYPE: {type_id}")
        self.logger.debug(f"ENTITY: {sub_type}")
        self.logger.debug(f"AREA: {area}")

        entity_names = []
        for name in self._intent_map.get(type_id, {}).get(area, {}):
            if sub_type in name.lower() or (sub_type == "light" and "lamp" in name.lower()):
                entity_names.append(name)

        if len(entity_names) == 1:
            self.say(f"The device in the {area} is {entity_names[0]}.", context=context)
            return True
        elif len(entity_names) > 1:
            entity_names[-1] = f"and {entity_names[-1]}"
            text = ", ".join(entity_names)
            self.say(f"The devices in the {area} are {text}.", context=context)
            return True
        else:
            self.say(f"I did not find any {sub_type}s in the {area}.", context=context)
            return True

        return False

    def handle_homeassistant_intent_lights(self, message, context=None, **kwargs):
        self.logger.debug("==< LIGHTS >================================")
        self.logger.debug(f"{message}")

        action = message.matches.get("ha_on_off", "").replace(".", "").lower()
        entity = message.matches.get("ha_type", "").replace(".", "").lower()
        if entity is None or entity == "":
            entity = message.matches.get("ha_lights", "").replace(".", "").lower()

        area = message.matches.get("ha_area", context.location).replace(".", "").lower()

        type_id = "light"
        self.logger.debug(f"TYPE: {type_id}")
        self.logger.debug(f"ACTION: {action}")
        self.logger.debug(f"ENTITY: {entity}")
        self.logger.debug(f"AREA: {area}")

        action = strip_punctuation(action).strip()
        if action not in ["on", "off"]:
            self.say("I'm sorry, I didn't get it.", context=context)
            return True

        has_error = False
        error_response = " ".join([x for x in message.sent if x != "please"])

        is_all = False
        if "all" in message.sent:
            is_all = True

        entity_ids = []

        if not is_all:
            entity_id = self._intent_map.get(type_id, {}).get(area, {}).get(entity, {}).get("entity_id")

            if entity_id is not None:
                entity_ids.append(entity_id)
            else:
                if entity.endswith("s"):
                    is_all = True

        if is_all:
            if entity.lower().rstrip("s") == "light":
                for entity_name in self._intent_map.get(type_id, {}).get(area, {}):
                    if self._intent_map.get(type_id, {}).get(area, {}).get(entity_name, {}).get("entity_id").split(".", 1)[0] == "light":
                        entity_ids.append(self._intent_map.get(type_id, {}).get(area, {}).get(entity_name, {}).get("entity_id"))
            elif entity.lower().rstrip("s") == "fan":
                for entity_name in self._intent_map.get(type_id, {}).get(area, {}):
                    if self._intent_map.get(type_id, {}).get(area, {}).get(entity_name, {}).get("entity_id").split(".", 1)[0] == "fan":
                        entity_ids.append(self._intent_map.get(type_id, {}).get(area, {}).get(entity_name, {}).get("entity_id"))
            elif entity.lower().rstrip("s") == "lamp":
                for entity_name in self._intent_map.get(type_id, {}).get(area, {}):
                    if "lamp" in entity_name.lower():
                        entity_ids.append(self._intent_map.get(type_id, {}).get(area, {}).get(entity_name, {}).get("entity_id"))

        if len(entity_ids) == 0:
            self.say(f"I'm sorry, I couldn't find the {area} {entity}.", context=context)
            return True

        for entity_id in entity_ids:
            self.logger.debug(f"ENTITY_ID: {entity_id}")
            type_id = entity_id.split(".", 1)[0] if entity_id is not None and "." in entity_id else type_id

            resp = requests.post(f"{self.url}/api/services/{type_id}/turn_{action}", headers=self._headers, timeout=20, json={ "entity_id": entity_id })
            if resp.ok:
                self.logger.debug(f"{resp.text}")

                if not is_all:
                    if entity.endswith("lights") or entity.endswith("fans") or entity.endswith("lamps"):
                        self.say(f"{area} {entity} are now {action}.", context=context)
                    else:
                        self.say(f"{area} {entity} is now {action}.", context=context)
            else:
                self.logger.debug(f"{resp.text}")
                has_error = True

        if has_error:
            self.say(f"Something went wrong while I was trying to {error_response}.", context=context)
            return True

        if is_all:
            if entity.lower().rstrip("s") == "light":
                self.say(f"The lights in the {area} are now {action}.", context=context)
            elif entity.lower().rstrip("s") == "fan":
                self.say(f"The fans in the {area} are now {action}.", context=context)
            elif entity.lower().rstrip("s") == "lamp":
                self.say(f"The lamps in the {area} are now {action}.", context=context)

        return True

    def handle_homeassistant_intent_covers(self, message, context=None, **kwargs):
        self.logger.debug("==< COVERS >================================")
        self.logger.debug(f"{message}")

        action = message.matches.get("ha_raise_lower", "").replace(".", "").lower().strip()
        entity = message.matches.get("ha_type", "").replace(".", "").lower().strip()
        if entity is None or entity == "":
            entity = message.matches.get("ha_covers", "").replace(".", "").lower().strip()

        area = message.matches.get("ha_area", context.location).replace(".", "").lower().strip()

        type_id = "cover"
        self.logger.debug(f"TYPE: {type_id}")
        self.logger.debug(f"ACTION: {action}")
        self.logger.debug(f"ENTITY: {entity}")
        self.logger.debug(f"AREA: {area}")

        action = strip_punctuation(action).strip()
        if action not in ["open", "close", "raise", "lower"]:
            self.say("I'm sorry, I didn't get it.", context=context)
            return True

        daction = action
        if action == "raise":
            daction = "open"
        elif action == "lower":
            daction = "close"

        entity_id = self._intent_map.get(type_id, {}).get(area, {}).get(entity, {}).get("entity_id")
        if entity_id is None:
            entity_id = self._intent_map.get(type_id, {}).get(area, {}).get(f"{entity}s", {}).get("entity_id")

        if entity_id is None:
            self.say(f"I'm sorry, I couldn't find the {area} {entity}.", context=context)
            return True

        error_response = " ".join([x for x in message.sent if x != "please"])

        self.logger.debug(f"ENTITY_ID: {entity_id}")
        resp = requests.post(f"{self.url}/api/services/cover/{daction}_cover", headers=self._headers, timeout=20, json={ "entity_id": entity_id })
        if resp.ok:
            self.logger.debug(f"{resp.text}")
            if action in ["close", "raise"]:
                action = action[:-1]
            self.say(f"{area} {entity} {action}ed.", context=context)
        else:
            self.say(f"Something went wrong while I was trying to {error_response}.", context=context)

        return True

    def handle_homeassistant_intent_locks(self, message, context=None, **kwargs):
        self.logger.debug("==< LOCKS >================================")
        self.logger.debug(f"{message}")

        action = message.matches.get("ha_lock_unlock", "").replace(".", "")
        entity = message.matches.get("ha_type", "").replace(".", "")
        if entity is None or entity == "":
            entity = message.matches.get("ha_locks", "").replace(".", "")
        area = message.matches.get("ha_area")

        type_id = "lock"
        self.logger.debug(f"TYPE:      {type_id}")
        self.logger.debug(f"ACTION:    {action}")
        self.logger.debug(f"ENTITY:    {entity}")
        self.logger.debug(f"AREA:      {area}")

        action = strip_punctuation(action.lower()).strip()
        if action not in ["lock", "unlock"]:
            self.say("I'm sorry, I didn't get it.", context=context)
            return True

        entity_id = None
        for area in self._intent_map.get("lock", {}):
            item = self._intent_map.get("lock").get(area)
            if entity in item:
                entity_id = item.get(entity).get("entity_id")
                break

        if entity_id is None:
            self.say(f"I'm sorry, I couldn't find the {entity}.", context=context)
            return True

        error_response = " ".join([x for x in message.sent if x != "please"])

        self.logger.debug(f"ENTITY_ID: {entity_id}")
        resp = requests.post(f"{self.url}/api/services/lock/{action}", headers=self._headers, timeout=20, json={ "entity_id": entity_id })
        if resp.ok:
            self.logger.debug(f"{resp.text}")
            self.say(f"{entity} {action}ed.", context=context)
        else:
            self.say(f"Something went wrong while I was trying to {error_response}.", context=context)

        return True

    def _image_timer(self):
        self._timer_running.set()

        while self._timer_running.is_set():
            for dev_url in self._dev_timers:
                dev_name = self.device.service.remote_devices.get(dev_url, {}).get("name", "")
                for trg in self._triggers:
                    if trg.get("type", "") == "camera" and trg.get("source_name", "") == dev_name:
                        for item in self._dev_timers.get(dev_url):
                            if item not in trg.get("filters", []):
                                continue

                            d = self._dev_timers.get(dev_url).get(item)
                            if d.get("trigger") != d.get("status"):
                                if d.get("trigger", False) or time.time() > d.get("timestamp") + float(self._timer_delay):
                                    d["status"] = d.get("trigger")

                                    entity_id = trg.get('entity_id')
                                    self.logger.debug("==============================================")
                                    self.logger.debug(f"TRIGGER CHANGE {item}={d.get('status')} : {entity_id}")
                                    
                                    domain = entity_id.split(".", 1)[0]
                                    service = "turn_on" if d.get("status", False) else "turn_off"

                                    resp = requests.post(
                                        f"{self.url}/api/services/{domain}/{service}", 
                                        headers=self._headers, 
                                        timeout=20, 
                                        json={"entity_id": entity_id}
                                    )

                                    if resp.ok:
                                        self.logger.debug(f"{resp.text}")

            time.sleep(0.1)

    def handle_homeassistant_image_trigger(self, message, context=None, **kwargs):
        
        if self._triggers is None or len(self._triggers) == 0:
            return True

        if isinstance(message, dict):
            dev_url = context.url if context is not None else "unknown"
            dev = {}

            if dev_url not in self._dev_timers:
                self._dev_timers[dev_url] = {}

            for o in message.get("objects", []):
                o_nm = o.get("name")

                if o_nm is not None:
                    if o_nm not in self._dev_timers.get(dev_url):
                        self._dev_timers[dev_url][o_nm] = {
                            "trigger": True, 
                            "status": False, 
                            "timestamp": time.time()
                        }
                    else:
                        self._dev_timers[dev_url][o_nm]["trigger"] = True
                        self._dev_timers[dev_url][o_nm]["timestamp"] = time.time()

                    if o_nm not in dev:
                        dev[o_nm] = 1
                    else:
                        dev[o_nm] += 1

            for item in self._dev_timers.get(dev_url, {}):
                if item not in dev:
                    self._dev_timers[dev_url][item]["trigger"] = False
                    # self._dev_timers[dev_url][item]["timestamp"] = time.time() + self._timer_delay

            self.logger.debug(f"HOMEASSISTANTSKILL: {dev}")
            self.logger.debug(f"HOMEASSISTANTSKILL: {self._dev_timers[dev_url]}")

        return True

    def stop(self):
        """
        Method to stop any daemons created during startup/initialization for this skill.

        Returns:
            (bool):  True on success and False on failure
        """
        self._timer_running.clear()

        if self._timer_thread is not None:
            self._timer_thread.join()
        return True


def create_skill(**kwargs):
    """
    Method to create the instance of this skill for delivering to the skill manager

    Returns:
        (object): HomeAssistantSkill instantiated class object
    """

    return HomeAssistantSkill(**kwargs)
