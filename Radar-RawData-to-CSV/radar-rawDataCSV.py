# Copyright (c) Acconeer AB, 2022-2023
# All rights reserved
# Copyright (c) Dylan Hoang, 2024.
# Based from the "plot.py" example found in Acconeer Exploration Tool.
# Exports Radar Readings to a CSV file.
# Use a CSV reader or extension to read file. 

import numpy as np

import acconeer.exptool as et
from acconeer.exptool import a121

import time
from datetime import datetime

class Radar:
    def __init__(self, subsweepConf: dict, serial_port, frameDelay: float, frameBuffer: int, UseSeconds: bool):
        self.subsweepConf   = subsweepConf
        self.serialP        = serial_port
        self.frameIndex     = 1
        self.frameDelay     = frameDelay
        self.CSV_Name       = str(datetime.now()).replace(":", ".")
        self.lastCheck      = time.time()
        self.frameBuffer    = frameBuffer

        self.useSeconds     = UseSeconds

    def initialize(self):
        args = a121.ExampleArgumentParser().parse_args()
        et.utils.config_logging(args)

        client = a121.Client.open(serial_port=self.serialP) #, **a121.get_client_args(args))

        session_config = a121.SessionConfig(
            [{
                1: a121.SensorConfig(
                    subsweeps=[
                        a121.SubsweepConfig(
                            start_point = self.subsweepConf["startPoint"],
                            step_length = self.subsweepConf["stepLength"],
                            num_points  = self.subsweepConf["numOfPoints"],
                            profile     = self.subsweepConf["profile"],
                            hwaas       = self.subsweepConf["HWAAS"],
                        ),
                    ],
                )
            }],
            extended=True,
        )

        client.setup_session(session_config)
        client.start_session()
        self.radarReadLoop(client)

    def radarReadLoop(self, client):

        interrupt_handler = et.utils.ExampleInterruptHandler()
        print("Press Ctrl-C to end session")

        text_buff = ""
        time_start = time.time()

        while not interrupt_handler.got_signal:
            result = client.get_next()

            if abs(time.time()-self.lastCheck) > self.frameDelay:
                for sensor_id, frame in result[0].items():
                    for sub_idx, subframe in enumerate(frame.subframes, 1):
                        subframe = np.abs(subframe).mean(axis=0)
                        subframe = np.round(subframe, 4)
                        text = f"{round(time.time()-time_start, 4)}, " if self.useSeconds else f"{self.frameIndex}, " 
                        text += ', '.join(map(str, subframe))
                        text += "\n"
                        
                        text_buff += text
                
                if self.frameIndex % frameBuffer == 0:
                    # write buff
                    self.writeToFile(text_buff)
                    # clear buff
                    text_buff = ""
                
                self.frameIndex += 1
                self.lastCheck = time.time()

            # return

        print("Disconnecting...")
        client.close()

    def init_CSV(self):
        # List comprehension
        measuredPositions = [round((x*self.subsweepConf["stepLength"] + self.subsweepConf["startPoint"])*2.5e-3, 4) for x in range(0, self.subsweepConf["numOfPoints"])]
        text = "d/t, " if self.useSeconds else "d/frame, "
        text += 'm, '.join(map(str, measuredPositions))
        text += 'm\n'
        self.writeToFile(text)

    def writeToFile(self, text):
        with open(f"{self.CSV_Name}.csv", "a") as f:
            f.write(text)

    # def getDistance(subsweepConf):
    #     range_p = np.arange(subsweepConf["numOfPoints"]) * subsweepConf["stepLength"] + subsweepConf["startPoint"]
    #     return range_p * 2.5e-3
            

if __name__ == "__main__":
    serial_port = "COM3"
    subsweepConf = {
        "startPoint": 80,       
        "stepLength": 1,        
        "numOfPoints": 180,     
        "profile": a121.Profile.PROFILE_3, # Profile (can also be PROFILE_1, PROFILE_2, PROFILE_4, PROFILE_5),
        "HWAAS": 8
    }
    frameDelay  = 0.1  # Delay between frames.
    frameBuffer = 100   # Buffer for lines in CSV before writing to file. 
    useSeconds  = True

    radar = Radar(subsweepConf, serial_port, frameDelay, frameBuffer, useSeconds)

    radar.init_CSV()
    radar.initialize()
    