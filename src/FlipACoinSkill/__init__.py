import random
from kenzy import GenericSkill


class FlipACoinSkill(GenericSkill):
    """
    Skill to flip a coin
    """
    
    def __init__(self, **kwargs):
        """
        Flip A Coin Skill Initialization
        """
        
        super().__init__(**kwargs)

        self.name = "FlipACoinSkill"
        self.description = "Flips a coin for heads or tails"
        self._version = [1, 0, 0]

        self.logger.debug(f"{self.name} loaded successfully.")
    
    def initialize(self):
        """
        Load intent files for Flip a Coin Skill
        
        Returns:
            (bool): True on success else raises an exception
        """

        self.register_intent_file("flipacoin.intent", self.handle_flipacoin_intent)
        return True
        
    def handle_flipacoin_intent(self, message, context=None, **kwargs):
        """
        Primary function for intent matches.  Called by skill manager.
        
        Args:
            message (obj):  text that triggered the intent
            context (KContext): Context surrounding the request. (optional)
            
        Returns:
            (bool): True on success or False on failure
        """
        
        if random.randint(1, 2) == 1:
            text = self.getMessageFromDialog("flipacoin_heads.dialog")
            return self.say(text, context=context)
        else:
            text = self.getMessageFromDialog("flipacoin_tails.dialog")
            return self.say(text, context=context)

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
    
    return FlipACoinSkill(**kwargs)
