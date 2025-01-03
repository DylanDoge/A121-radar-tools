# Copyright (c) Acconeer AB, 2022-2023
# All rights reserved
# Copyright (c) Dylan Hoang, 2024.
# Based from the "plot.py" example found in Acconeer Exploration Tool.
# Sends actions to couple APIs depending on radar readings.

import numpy as np

import acconeer.exptool as et
from acconeer.exptool import a121

import hueAPI
import spotifyAPI
import time

def main(serialP, subsweepConf: list):
    args = a121.ExampleArgumentParser().parse_args()
    et.utils.config_logging(args)

    client = a121.Client.open(serial_port=serialP) #, **a121.get_client_args(args))

    session_config = a121.SessionConfig(
        [{
            1: a121.SensorConfig(
                subsweeps=[
                    a121.SubsweepConfig(
                        start_point = subsweepConf[0],
                        step_length = subsweepConf[1],
                        num_points = subsweepConf[2],
                        profile = subsweepConf[3],
                        hwaas = subsweepConf[4],
                    ),
                ],
            )
        }],
        extended=True,
    )

    client.setup_session(session_config)
    client.start_session()

    radarLoop(client)

def radarLoop(client):
    interrupt_handler = et.utils.ExampleInterruptHandler()
    print("Press Ctrl-C to end session")

    light = hueAPI.Lights()
    selectedLightID = 1
    spotifyOAuthRefreshToken = "OAUTH2_TOKEN"   # Required for Spotify API
    prevLightsAction_timestamp = time.time()

    while not interrupt_handler.got_signal:
        extended_result = client.get_next()
        
        for group_idx, group in enumerate(extended_result):
            for sensor_id, result in group.items():

                maxAmplitude = 0                
                for sub_idx, subframe in enumerate(result.subframes):
                    y = np.abs(subframe).mean(axis=0)
                    maxAmplitude = max(maxAmplitude, np.max(y))

                if maxAmplitude > 3000 and time.time() - prevLightsAction_timestamp > 0.25:
                    # Spotify API
                    # volumeVal = round(np.interp((np.argmax(y)+80)*2.5e-3, [0.25, 0.64], [100, 0]))
                    # res = spotifyAPI.changeVolume(spotifyOAuthRefreshToken, volumeVal)
                    # print(res)
                    # print(f"{volumeVal} {round((np.argmax(y)+80)*2.5e-3, 4)}")

                    # Philips Hue API
                    brightnessVal = round(np.interp((np.argmax(y)+80)*2.5e-3, [0.25, 0.6], [0, 255]))
                    if brightnessVal == 0:
                        light.changeOnState(selectedLightID, False)
                    elif light.checkStatus(selectedLightID):
                        light.changeBrightness(selectedLightID, brightnessVal)
                    else:
                        light.changeBrightnessAndOnState(selectedLightID, True, brightnessVal)

                    prevLightsAction_timestamp = time.time()


    print("Disconnecting...")
    client.close()

if __name__ == "__main__":
    serial_port = "COM3"
    subsweepConf = [
        80,                     # Start_point,
        1,                      # Step_length,
        180,                    # Num_points,
        a121.Profile.PROFILE_3, # Profile (can also be PROFILE_1, PROFILE_2, PROFILE_4, PROFILE_5),
        8                       # HWAAS
    ]
    main(serial_port, subsweepConf)