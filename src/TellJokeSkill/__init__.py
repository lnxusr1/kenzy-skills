import random
from kenzy import GenericSkill


class TellJokeSkill(GenericSkill):
    """
    Skill to tell a joke
    """
    
    def __init__(self, **kwargs):
        """
        Tell Joke Skill Initialization
        """

        super().__init__(**kwargs)

        self.name = "TellJokeSkill"
        self.description = "Tells a random joke"
        self._version = [1, 0, 0]
        
        self.logger.debug(f"{self.name} loaded successfully.")
        
        self.kk_context = {}        
        self.kk_jokes = [
            {
                "prompt": "Nobel.",
                "punch": "No­ bell, so I knock knocked."
            },
            {
            	"prompt": "Ayatollah.",
            	"punch": "Ayatollah you already."
            },
            {
            	"prompt": "Boo.",
            	"punch": "Don't cry it's only a joke."
            },
            {
            	"prompt": "Radio.",
            	"punch": "Radio not, here I come."
            },
            {
            	"prompt": "A little old lady.",
            	"punch": "I didn't know you could yodel."
            },
            {
            	"prompt": "Dozen.",
            	"punch": "Dozen anybody want to let me in."
            }
        ]
    
    def initialize(self):
        """
        Load intent files for Tell Joke Skill
        
        Returns:
            (bool): True on success else raises an exception
        """

        self.register_intent_file("telljoke.intent", self.handle_telljoke_intent)
        self.register_intent_file("knockknockjoke.intent", self.handle_telljoke_knockknock_intent)
        return True
        
    def handle_telljoke_intent(self, message, context=None, **kwargs):
        """
        Primary function for intent matches.  Called by skill manager.
        
        Args:
            message (obj):  text that triggered the intent
            context (KContext): Context surrounding the request. (optional)
            
        Returns:
            (bool): True on success or False on failure
        """
        
        
        text = self.getMessageFromDialog("telljoke.dialog")
        if (text != ""):
            return self.say(text, context=context)
    
        return False
        
        
    def handle_telljoke_knockknock_r1(self, message, context=None, **kwargs):
        url = "none"
        if context is not None:
            if isinstance(context, dict):
                url = context.get("url")
            else:
                url = context.url
            
        joke = {}

        joke = random.choice(self.kk_jokes) 
        
        if isinstance(joke, dict) and "there" in message.lower():
            self.kk_context[url] = joke.get("punch")
            self.ask(joke.get("prompt"), self.handle_telljoke_knockknock_r2, context=context)

    def handle_telljoke_knockknock_r2(self, message, context=None, **kwargs):
        url = "none"
        if context is not None:
            if isinstance(context, dict):
                url = context.get("url")
            else:
                url = context.url
                
            if url is None:
                url = "none"
           
        if self.kk_context.get(url) is not None:
            self.say(self.kk_context.get(url), context=context)

    def handle_telljoke_knockknock_intent(self, message, context=None, **kwargs):
        """
        Primary function for intent matches.  Called by skill manager.
        
        Args:
            message (obj):  text that triggered the intent
            context (KContext): Context surrounding the request. (optional)
            
        Returns:
            (bool): True on success or False on failure
        """
        
        
        return self.ask("Knock knock", self.handle_telljoke_knockknock_r1, context=context)
    
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
        (object): TellJokeSkill instantiated class object
    """
    
    return TellJokeSkill(**kwargs)
