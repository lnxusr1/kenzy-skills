import threading
import time
import logging
import requests
import xml.etree.ElementTree as ET
from email.utils import parsedate_tz
import datetime
from kenzy import GenericSkill


class NewsSkill(GenericSkill):
    """
    Skill to read the news headlines
    """
    
    def __init__(self, **kwargs):
        """
        News Skill Initialization
        """
        
        super().__init__(**kwargs)

        self.name = "NewsSkill"
        self.description = "RSS feed reader"
        self._version = [1, 0, 0]

        self._is_running = threading.Event()
        self.thread = None

        self.feeds = []
        self.news = []

        self.logger.debug(f"{self.name} loaded successfully.")
    
    def initialize(self):
        """
        Load intent files for News Skill
        
        Returns:
            (bool): True on success else raises an exception
        """

        self.feeds = self.get_setting("feeds", ["https://feeds.a.dj.com/rss/RSSWorldNews.xml"])

        self.get_news()

        self._is_running.set()
        self.thread = threading.Thread(target=self.start_reader, daemon=True)
        self.thread.start()
        
        self.register_intent_file("latestnews.intent", self.handle_latestnews_intent)
        
        return True
    
    def get_news(self):
        try:
            entries = []
            for feed in self.feeds:
                resp = requests.get(feed)
                if resp.ok:
                    root = ET.fromstring(resp.content)
                    post_items = root.findall(".//item")
                    for item in range(0, len(post_items)):
                        post_item = root.findall(".//item")[item]

                        post_title = post_item.find("title").text
                        post_date = post_item.find("pubDate").text
                        post_link = post_item.find("link").text
                        post_description = post_item.find("description").text
                        struct_time = parsedate_tz(post_date)
                        timestamp = datetime.datetime(*struct_time[:6]).timestamp()

                        post = { "title": post_title, "timestamp": timestamp, "url": post_link, "description": post_description }

                        entries.append(post)

                        if item > 5:
                            break

            sorted_entries = sorted(entries, key=lambda x: x.get("timestamp"), reverse=True)
            self.entries = sorted_entries

        except:
            pass
    
    def start_reader(self):

        i = 0
        while self._is_running.is_set():
            i = i + 1
            if i % 9000 == 0:
                # Check for new news once every 15 minutes (900 seconds).
                self.get_news()

            time.sleep(0.1)

    def handle_latestnews_continue(self, message, context=None, **kwargs):
        if str(message).lower().strip().strip("?.!") in ["yes", "please", "continue", "okay", "ok"]:

            if len(self.entries) > 2:
                entry3 = self.entries[2].get("title")
                self.say(entry3, context=context)

            if len(self.entries) > 4:
                entry3 = self.entries[3].get("title")
                self.say(entry3, context=context)

            if len(self.entries) > 5:
                entry3 = self.entries[4].get("title")
                self.say(entry3, context=context)

    def handle_latestnews_intent(self, message, context=None, **kwargs):
        """
        Primary function for intent matches.  Called by skill manager.
        
        Args:
            message (obj):  text that triggered the intent
            context (KContext): Context surrounding the request. (optional)
            
        Returns:
            (bool): True on success or False on failure
        """
        
        if len(self.entries) >= 2:
            self.say("The latest two headlines are", context=context)

            entry1 = self.entries[0].get("title")
            entry2 = self.entries[1].get("title")

            self.say(entry1, context=context)
            self.say(entry2, context=context)
        
            if len(self.entries) > 2:
                return self.ask("Would you like to continue?", self.handle_latestnews_continue, context=context)
            else:
                return True

        return False
    
    def stop(self):
        """
        Method to stop any daemons created during startup/initialization for this skill.
        
        Returns:
            (bool):  True on success and False on failure
        """
        
        self._is_running.clear()
        return True
        
    
def create_skill(**kwargs):
    """
    Method to create the instance of this skill for delivering to the skill manager
    
    Returns:
        (object): HelloSkill instantiated class object
    """
    
    return NewsSkill(**kwargs)
