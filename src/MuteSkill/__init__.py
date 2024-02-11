from kenzy import GenericSkill
from kenzy.core import KenzyContext


class MuteSkill(GenericSkill):
    """
    Skill to deactivate Kenzy
    """
    
    def __init__(self, **kwargs):
        """
        Mute Skill Initialization
        """
        
        super().__init__(**kwargs)

        self.name = "MuteSkill"
        self.description = "Silences responses until a new command is received"
        self._version = [1, 0, 0]
        self._app_min_version = [2, 1, 4]

        self.logger.debug(f"{self.name} loaded successfully.")
    
    def initialize(self):
        """
        Load intent files for Mute Skill
        self.logger = kwargs.get("logger", logging.getLogger("SKILL"))
        
        Returns:
            (bool): True on success else raises an exception
        """

        self.register_intent_file("mute.intent", self.handle_mute_intent)
        return True
        
    def handle_mute_intent(self, message, context=None, **kwargs):
        """
        Primary function for intent matches.  Called by skill manager.
        
        Args:
            message (obj):  text that triggered the intent
            context (KContext): Context surrounding the request. (optional)
            
        Returns:
            (bool): True on success or False on failure
        """
        
        c_loc = "none"
        if isinstance(context, KenzyContext):
            c_loc = str(context.location).lower()

        if c_loc in self.device.skill_manager.activated:
            self.device.skill_manager.activated[c_loc] = 0
        
        self.logger.debug(f"{self.name}: Deactivated {c_loc}.")

        return True
    
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
        (object): MuteSkill instantiated class object
    """
    
    return MuteSkill(**kwargs)
