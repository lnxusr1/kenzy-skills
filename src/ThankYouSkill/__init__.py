from kenzy import GenericSkill


class ThankYouSkill(GenericSkill):
    """
    Skill to say "Thank You"
    """
    
    def __init__(self, **kwargs):
        """
        Thank You Skill Initialization
        """
        
        super().__init__(**kwargs)

        self.name = "ThankYouSkill"
        self.description = "Politely responds to Thank You"
        self._version = [1, 0, 1]
        
        self.logger.debug(f"{self.name} loaded successfully.")
    
    def initialize(self):
        """
        Load intent files for Thank You Skill
        
        Returns:
            (bool): True on success else raises an exception
        """

        self.register_intent_file("thankyou.intent", self.handle_thankyou_intent)
        return True
        
    def handle_thankyou_intent(self, message, context=None, **kwargs):
        """
        Primary function for intent matches.  Called by skill manager.
        
        Args:
            message (obj):  text that triggered the intent
            context (KContext): Context surrounding the request. (optional)
            
        Returns:
            (bool): True on success or False on failure
        """
        
        if message.conf == 1.0:
            text = self.getMessageFromDialog("thankyou.dialog")
            if (text != ""):
                return self.say(text, context=context)
        
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
        (object): ThankYouSkill instantiated class object
    """
    
    return ThankYouSkill(**kwargs)
