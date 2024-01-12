import os
import yaml
import requests
from kenzy import GenericSkill


class WeatherSkill(GenericSkill):
    """
    Skill to provide weather updates
    """

    def __init__(self, **kwargs):
        """
        Weather Skill Initialization
        """

        super().__init__(**kwargs)

        self.name = "WeatherSkill"
        self.description = "Get weather updates"
        self._version = [1, 0, 0]

        self.api_key = None
        self.lattitude = None
        self.longitude = None
        self.units = "imperial"
        self.condition_map = None

        self.logger.debug(f"{self.name} loaded successfully.")

    def initialize(self):
        """
        Load intent files for Weather Skill

        Returns:
            (bool): True on success else raises an exception
        """

        self.api_key = self.get_setting("api_key")
        self.lattitude = self.get_setting("lat")
        self.longitude = self.get_setting("lon")
        self.units = self.get_setting("units")

        if self.units is None:
            self.units = "imperial"

        if self.api_key is None \
                or self.lattitude is None \
                or self.longitude is None:
            
            self.logger.error("Unable to initialize weather skill.  Missing configuration.")
            return False
        
        with open(os.path.join(os.path.dirname(__file__), "weather_conditions.yml"), "r", encoding="UTF-8") as fp:
            self.condition_map = yaml.safe_load(fp)

        self.register_intent_file("weather.intent", self.handle_weather_intent)
        self.register_intent_file("temperature.intent", self.handle_temperature_intent)
        return True

    def get_data(self):
        resp = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={self.lattitude}&lon={self.longitude}&appid={self.api_key}&units={self.units}")
        if resp.ok:
            data = resp.json()

            self.logger.debug(f"{data}")
            return data

        return None

    def handle_temperature_intent(self, message, context=None, **kwargs):
        """
        Primary function for intent matches.  Called by skill manager.

        Args:
            message (obj):  text that triggered the intent
            context (KContext): Context surrounding the request. (optional)

        Returns:
            (bool): True on success or False on failure
        """

        data = self.get_data()

        if data is not None:
            temperature = data.get("main", {}).get("temp", None)
            if temperature is not None:
                temperature = int(temperature)
                return self.say(f"It is {temperature} degrees outside.", context=context)

        return self.say("I was unable to retrieve current weather data.", context=context)

    def handle_weather_intent(self, message, context=None, **kwargs):
        """
        Primary function for intent matches.  Called by skill manager.

        Args:
            message (obj):  text that triggered the intent
            context (KContext): Context surrounding the request. (optional)

        Returns:
            (bool): True on success or False on failure
        """

        data = self.get_data()

        if data is not None:
            temperature = data.get("main", {}).get("temp", None)
            if temperature is not None:
                temperature = int(temperature)
                conditions = ""
                if len(data.get("weather", [])) > 0 and data.get("weather", [])[0].get("id", "-1") in self.condition_map:
                    conditions = self.condition_map.get(data.get("weather", [])[0].get("id", "-1"))

                if conditions != "":
                    conditions = f"with {conditions}"

            wind_details = ""
            wind_speed = data.get("wind", {}).get("speed", 0)
            if self.units == "imperial":
                wind_speed = int(wind_speed)
                units = "miles per hour"
            else:
                units = "kilometers per hour"
                wind_speed = int(wind_speed * 3.6)

            if wind_speed >= 5:
                
                wind_details = f". The wind blowing at about {int(data.get('wind').get('speed', 0))} {units} "

                if data.get("wind", {}).get("deg", -1) <= 15 or data.get("wind", {}).get("deg", -1) > 345:
                    wind_details = f"{wind_details} from the north"
                elif data.get("wind", {}).get("deg", -1) <= 35:
                    wind_details = f"{wind_details} from the north/northeast"
                elif data.get("wind", {}).get("deg", -1) <= 55:
                    wind_details = f"{wind_details} from the northeast"
                elif data.get("wind", {}).get("deg", -1) <= 75:
                    wind_details = f"{wind_details} from the east/northeast"
                elif data.get("wind", {}).get("deg", -1) <= 105:
                    wind_details = f"{wind_details} from the east"
                elif data.get("wind", {}).get("deg", -1) <= 125:
                    wind_details = f"{wind_details} from the east/southeast"
                elif data.get("wind", {}).get("deg", -1) <= 145:
                    wind_details = f"{wind_details} from the southeast"
                elif data.get("wind", {}).get("deg", -1) <= 165:
                    wind_details = f"{wind_details} from the south/southeast"
                elif data.get("wind", {}).get("deg", -1) <= 195:
                    wind_details = f"{wind_details} from the south"
                elif data.get("wind", {}).get("deg", -1) <= 215:
                    wind_details = f"{wind_details} from the south/southwest"
                elif data.get("wind", {}).get("deg", -1) <= 235:
                    wind_details = f"{wind_details} from the southwest"
                elif data.get("wind", {}).get("deg", -1) <= 255:
                    wind_details = f"{wind_details} from the west/southwest"
                elif data.get("wind", {}).get("deg", -1) <= 285:
                    wind_details = f"{wind_details} from the west"
                elif data.get("wind", {}).get("deg", -1) <= 305:
                    wind_details = f"{wind_details} from the west/northwest"
                elif data.get("wind", {}).get("deg", -1) <= 325:
                    wind_details = f"{wind_details} from the northwest"
                elif data.get("wind", {}).get("deg", -1) <= 345:
                    wind_details = f"{wind_details} from the north/northwest"

                if data.get("wind", {}).get("gust", 0) > 20 \
                        and (data.get("wind", {}).get("gust", data.get("wind", {}).get("speed")) / data.get("wind", {}).get("speed", 1)) > 2:
                    wind_details = f"{wind_details} with gusts up to {data.get('wind', {}).get('gust')}"

            weather_line = f"The temperature is {temperature} degrees {conditions}{wind_details}."
            return self.say(weather_line, context=context)

        return self.say("I was unable to retrieve current weather data.", context=context)

    def stop(self):
        """
        Method to stop any daemons created during startup/initialization

        Returns:
            (bool):  True on success and False on failure
        """
        return True


def create_skill(**kwargs):
    """
    Method to create the instance of this skill for delivering
    to the skill manager

    Returns:
        (object): WeatherSkill instantiated class object
    """

    return WeatherSkill(**kwargs)
