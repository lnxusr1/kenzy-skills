import os
import yaml
import copy
from kenzy import GenericSkill


class WatcherSkill(GenericSkill):
    """
    Skill to leverage kenzy.image devices
    """
    
    def __init__(self, **kwargs):
        """
        Watcher Skill Initialization
        """
        
        super().__init__(**kwargs)

        self.plurals = {}
        self.name = "WatcherSkill"
        self.description = "Query kenzy.image devices"
        self._version = [1, 0, 2]
        
        self.logger.debug(f"{self.name} loaded successfully.")
    
    def initialize(self):
        """
        Load intent files for Thank You Skill
        
        Returns:
            (bool): True on success else raises an exception
        """

        with open(os.path.join(os.path.dirname(__file__), "plurals.yml"), "r", encoding="UTF-8") as fp:
            self.plurals = yaml.safe_load(fp)

        self.register_intent_file("watcher.intent", self.handle_watcher_general_intent)
        return True
        
    def handle_watcher_general_intent(self, message, context=None, **kwargs):
        """
        Primary function for intent matches.  Called by skill manager.
        
        Args:
            message (obj):  text that triggered the intent
            context (KContext): Context surrounding the request. (optional)
            
        Returns:
            (bool): True on success or False on failure
        """

        data = copy.deepcopy(self.device.data.get("kenzy.image"))

        motion = []
        objects = {}
        for dev_url in data:
            d = data.get(dev_url)
            for o in d.get("objects", []):
                objects[o.get("name")] = objects.get(o.get("name"), 0) + 1

            if dev_url in self.device.service.remote_devices:
                location = self.device.service.remote_devices.get(dev_url).get("location")

            if location is not None:
                if d.get("motion", False):
                    motion.append(location)

        if len(objects) > 0:
            text_arr = []
            for x in objects:
                t = x if objects.get(x) == 1 else self.plurals.get(x, f"{x}s")
                text_arr.append(str(f"{objects.get(x)} {t}"))

            if len(text_arr) > 1:
                text_arr[-1] = f"and {text_arr[-1]}"

            text = ", ".join(text_arr)

            text2 = ""
            if len(motion) > 0:
                area = "areas" if len(motion) > 1 else "area"
                text2 = f" with motion in {len(motion)} {area}"

            return self.say(f"I see {text}{text2}.", context=context)
        elif len(motion) > 0:
            area = "areas" if len(motion) > 1 else "area"
            return self.say(f"I see motion in {len(motion)} {area}.", context=context)
        
        return self.say("I don't see anything at the moment.", context=context)

    def stop(self):
        """
        Method to stop any daemons created during startup/initialization for this skill.
        
        Returns:
            (bool):  True on success and False on failure
        """
        return True
        
    
def create_skill(**kwargs):
    """
    Method to create the instance of this skill for delivering to the skill manager
    
    Returns:
        (object): ThankYouSkill instantiated class object
    """
    
    return WatcherSkill(**kwargs)
