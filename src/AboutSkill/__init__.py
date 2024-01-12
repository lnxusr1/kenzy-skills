from statistics import mean 
from kenzy import GenericSkill


class AboutSkill(GenericSkill):
    """
    Skill provide "About" Information
    """

    def __init__(self, **kwargs):
        """
        About Skill Initialization
        """

        super().__init__(**kwargs)

        self.name = "AboutSkill"
        self.description = "Q&A about KENZY"
        self._version = [1, 0, 0]

        self.logger.debug(f"{self.name} loaded successfully.")

    def initialize(self):
        """
        Load intent files for About Skill

        Returns:
            (bool): True on success else raises an exception
        """

        self.register_intent_file("who.intent", self.handle_who_intent)
        self.register_intent_file("status.intent", self.handle_status_intent)
        self.register_intent_file("real.intent", self.handle_real_intent)
        self.register_intent_file("human.intent", self.handle_human_intent)
        self.register_intent_file("maker.intent", self.handle_maker_intent)
        return True

    def handle_who_intent(self, message, context=None, **kwargs):
        """
        Primary function for intent matches.  Called by skill manager.
        
        Args:
            message (obj):  text that triggered the intent
            context (KContext): Context surrounding the request. (optional)
            
        Returns:
            (bool): True on success or False on failure
        """
        
        if message.conf == 1.0:
            
            text = self.getMessageFromDialog("who.dialog")
            if (text != ""):
                return self.say(text, context=context)
            
        return False

    def handle_status_intent(self, message, context=None, **kwargs):
        """
        Primary function for intent matches.  Called by skill manager.
        
        Args:
            message (obj):  text that triggered the intent
            context (KContext): Context surrounding the request. (optional)
            
        Returns:
            (bool): True on success or False on failure
        """
        
        status = self.device.status().data

        cpu_pcts = [status.get("info", {}).get("cpu", {}).get("percent")]
        mem_pcts = [status.get("info", {}).get("memory", {}).get("virtual", {}).get("percent")]

        devs = status.get("data", {}).get("devices", [])
        for item in devs:
            cpu_pcts.append(devs.get(item).get("info", {}).get("cpu", {}).get("percent"))
            mem_pcts.append(devs.get(item).get("info", {}).get("memory", {}).get("virtual", {}).get("percent"))


        high_cpu = False
        single_cpu = False
        cpu_pct = 0

        high_mem = False
        single_mem = False
        mem_pct = 0

        if mean(cpu_pcts) > 50:
            high_cpu = True
            cpu_pct = mean(cpu_pcts)
        elif max(cpu_pcts) > 85:
            single_cpu = True
            cpu_pct = max(cpu_pcts)

        if mean(mem_pcts) > 70:
            high_mem = True
            mem_pct = mean(mem_pcts)

        elif max(mem_pcts) > 90:
            single_mem = True
            mem_pct = max(mem_pcts)

        if high_cpu:
            if high_mem:
                return self.say("My Sea Pee You cores and memory utilization are both running higher than normal.", context=context)
            elif single_mem:
                return self.say("My Sea Pee You cores are running higher than usual, and I have a node that has higher than expected memory utilization.", context=context)
            else:
                return self.say("My Sea Pee You cores are running higher than usual, but otherwise I'm okay.", context=context)
        elif single_cpu:
            if high_mem:
                return self.say("My virtual memory is being used at a higher than normal rate and I have a node that has a higher than expected Sea Pee You utilization.", context=context)
            elif single_mem:
                return self.say("I have a node that seems to be over allocated.", context=context)
            else:
                return self.say("I have a node that is processing a significant amount of data, but otherwise I'm okay.", context=context)
        else:
            if high_mem:
                return self.say(f"My virtual memory seems to be over allocated as it has only {str(100 - int(mem_pct))} percent remaining.", context=context)
            elif single_mem:
                return self.say(f"I have a node that is using {str(int(mem_pct))} percent of its virtual memory.", context=context)

        text = self.getMessageFromDialog("status.dialog")
        if (text != ""):
            return self.say(text, context=context)

        return False

    def handle_real_intent(self, message, context=None, **kwargs):
        """
        Primary function for intent matches.  Called by skill manager.
        
        Args:
            message (obj):  text that triggered the intent
            context (KContext): Context surrounding the request. (optional)
            
        Returns:
            (bool): True on success or False on failure
        """
        
        if message.conf == 1.0:
            
            text = self.getMessageFromDialog("real.dialog")
            if (text != ""):
                return self.say(text, context=context)
            
        return False

    def handle_human_intent(self, message, context=None, **kwargs):
        """
        Primary function for intent matches.  Called by skill manager.
        
        Args:
            message (obj):  text that triggered the intent
            context (KContext): Context surrounding the request. (optional)
            
        Returns:
            (bool): True on success or False on failure
        """
        
        if message.conf == 1.0:
            
            text = self.getMessageFromDialog("human.dialog")
            if (text != ""):
                return self.say(text, context=context)
            
        return False

    def handle_maker_intent(self, message, context=None, **kwargs):
        """
        Primary function for intent matches.  Called by skill manager.
        
        Args:
            message (obj):  text that triggered the intent
            context (KContext): Context surrounding the request. (optional)
            
        Returns:
            (bool): True on success or False on failure
        """
        
        if message.conf == 1.0:
            
            text = self.getMessageFromDialog("maker.dialog")
            if (text != ""):
                return self.say(text, context=context)
            
        return False
    
    def stop(self):
        """
        Method to stop any daemons created during startup/initialization 
        
        Returns:
            (bool):  True on success and False on failure
        """
        return True
        
    
def create_skill(**kwargs):
    """
    Method to create the instance of this skill for the skill manager
    
    Returns:
        (object): HelloSkill instantiated class object
    """
    
    return AboutSkill(**kwargs)
