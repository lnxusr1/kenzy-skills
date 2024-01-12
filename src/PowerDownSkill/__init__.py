from kenzy import GenericSkill


class PowerDownSkill(GenericSkill):
    """
    Skill to shut down the services
    """
    
    def __init__(self, **kwargs):
        """
        Power Down Skill Initialization
        """
        
        super().__init__(**kwargs)

        self.name = "PowerDownSkill"
        self.description = "Shutdown all services"
        self._version = [1, 0, 0]

        self.logger.debug(f"{self.name} loaded successfully.")
    
    def initialize(self):
        """
        Load intent files for Power Down Skill
        
        Returns:
            (bool): True on success else raises an exception
        """

        self.register_intent_file("powerdown.intent", self.handle_powerdown_intent)
        return True

    def handle_powerdown_confirm(self, message, context=None, **kwargs):
        """
        Confirmation for PowerDownSkill
        
        Args:
            message (str): The text triggering this step.
            context (KContext): Context surrounding the request. (optional)
            
        Returns:
            (bool):  True on success or False on failure
        """

        text = self.getMessageFromDialog("powerdown_confirm.dialog")
        if str(message).lower().strip().strip("?.!") in ["yes","confirm","confirmed","ok"] and self.say(text, context) and self.service.shutdown():
            return True
        
        return False

        
    def handle_powerdown_intent(self, message, context=None, **kwargs):
        """
        Primary function for intent matches.  Called by skill manager.
        
        Args:
            message (obj):  text that triggered the intent
            context (KContext): Context surrounding the request. (optional)
            
        Returns:
            (bool): True on success or False on failure
        """
        
        text = self.getMessageFromDialog("powerdown.dialog")
        return self.ask(text, self.handle_powerdown_confirm, context=context)
            
    def stop(self):
        """
        Method to stop any daemons created during st
        artup/initialization for this skill.
        
        Returns:
            (bool):  True on success and False on failure
        """
        return True
        
    
def create_skill(**kwargs):
    """
    Method to create the instance of this skill for delivering to the skill manager
    
    Returns:
        (object): PowerDownSkill instantiated class object
    """
    
    return PowerDownSkill(**kwargs)
