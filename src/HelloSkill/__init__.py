from kenzy import GenericSkill


class HelloSkill(GenericSkill):
    """
    Skill to say "Hello"
    """
    
    def __init__(self, **kwargs):
        """
        Hello Skill Initialization
        """
        
        super().__init__(**kwargs)

        self.name = "HelloSkill"
        self.description = "Generic greeting responses"
        self._version = [1, 0, 0]

        self.logger.debug(f"{self.name} loaded successfully.")
    
    def initialize(self):
        """
        Load intent files for Hello Skill
        self.logger = kwargs.get("logger", logging.getLogger("SKILL"))
        
        Returns:
            (bool): True on success else raises an exception
        """

        self.register_intent_file("hello.intent", self.handle_hello_intent)
        return True
        
    def handle_hello_intent(self, message, context=None, **kwargs):
        """
        Primary function for intent matches.  Called by skill manager.
        
        Args:
            message (obj):  text that triggered the intent
            context (KContext): Context surrounding the request. (optional)
            
        Returns:
            (bool): True on success or False on failure
        """
        
        text = self.getMessageFromDialog("hello.dialog")
        if (text != "") and (text.lower() != "good night"):
            return self.say(text, context=context)
        else:
            return self.say("Hello", context=context)
    
        return False
    
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
        (object): HelloSkill instantiated class object
    """
    
    return HelloSkill(**kwargs)
