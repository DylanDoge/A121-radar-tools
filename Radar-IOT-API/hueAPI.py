# Copyright (c) Dylan Hoang, 2024.
# Local HTTP Requests in Philips Hue API.
# Requires Philips Hue Hub to get an authenticated username.  

import requests
import json

class Lights:
    def __init__(self):
        self.HUBIP = "HUE_HUB_IP"                   # Required
        self.rootURL = f"http://{self.HUBIP}/api/"
        self.username = "USER_AUTH"                 # Required
        self.lights = f'{self.rootURL}{self.username}/lights/'
    
    def checkStatus(self, lightID):
        # Check if light 1 is on 
        light_URL = f'{self.lights}{lightID}/'
        res = requests.get(light_URL).text
        parsed_data = json.loads(res)
        return parsed_data["state"]["on"]

    def toggleLight(self, lightID):
        isOn = self.checkStatus(lightID)
        self.changeOnState(lightID, not(isOn))

    def toggleLightWithBrightness(self, lightID, brightnessValue):
        isOn = self.checkStatus(lightID)
        self.changeBrightnessAndOnState(lightID, not(isOn), brightnessValue)

    def changeOnState(self, lightID, newState):
        light_URL = f'{self.lights}{lightID}/state'
        body = {
            "on": newState
        }
        res = requests.put(light_URL, data=json.dumps(body)).text
        print(res)
        return newState
    
    def changeBrightness(self, lightID, brightnessValue):
        light_URL = f'{self.lights}{lightID}/state'
        body = {
            "bri": brightnessValue
        }
        res = requests.put(light_URL, data=json.dumps(body)).text
        print(res)

    def changeBrightnessAndOnState(self, lightID, newState, brightnessValue):
        light_URL = f'{self.lights}{lightID}/state'
        body = {
            "on": newState,
            "bri": brightnessValue
        }
        res = requests.put(light_URL, data=json.dumps(body)).text
        print(res)


if __name__ == "__main__":
    x = Lights()
    x.toggleLightWithBrightness(1, 24)