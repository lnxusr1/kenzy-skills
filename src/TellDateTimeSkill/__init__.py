import time
from kenzy import GenericSkill
from kenzy.extras import dayPart, number_to_words


class TellDateTimeSkill(GenericSkill):
    """
    Skill to give the date and time.
    """
    
    def __init__(self, **kwargs):
        """
        Tell Date and Time Skill Initialization
        """
        
        super().__init__(**kwargs)

        self.name = "TellDateTimeSkill"
        self.description = "Tells date and time when asked"
        self._version = [1, 0, 1]

        self.logger.debug(f"{self.name} loaded successfully.")
    
    def initialize(self):
        """
        Load intent files for Tell Date Time Skill
        
        Returns:
            (bool): True on success else raises an exception
        """
        
        self.register_intent_file("telltime.intent", self.handle_telltime_intent)
        self.register_intent_file("telldate.intent", self.handle_telldate_intent)
        return True

    def handle_telltime_intent(self, message, context=None, **kwargs):
        """
        Primary function for intent matches when a TIME intent is detected.  Called by skill manager.
        
        Args:
            message (obj):  text that triggered the intent
            context (KContext): Context surrounding the request. (optional)
            
        Returns:
            (bool): True on success or False on failure
        """
        
        if message.conf == 1.0:
            
            dp = dayPart().lower()
            if dp == "night":
                dp = " P M"
            else:
                dp = " in the " + dp

            hours = time.strftime("%l")
            minutes = time.strftime("%M")

            hour_part = number_to_words(int(hours))
                                         
            if minutes == "00":
                minute_part = "o'clock"
            elif minutes.startswith("0"):
                minute_part = f"oh {number_to_words(int(minutes))}"
            else:
                minute_part = f"{number_to_words(int(minutes))}"

            text = f"It is {hour_part} {minute_part} {dp}"
             
            return self.say(text, context=context)
                    
        return False
    
    def handle_telldate_intent(self, message, context=None, **kwargs):
        """
        Primary function for intent matches when a DATE intent is detected.  Called by skill manager.
        
        Args:
            message (str):  text that triggered the intent
            context (KContext): Context surrounding the request. (optional)
            
        Returns:
            (bool): True on success or False on failure
        """

        text = "It is " + time.strftime("%A, %B %d")
        return self.say(text, context=context)
    
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
        (object): TellDateTimeSkill instantiated class object
    """
    
    return TellDateTimeSkill(**kwargs)
