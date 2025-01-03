# Copyright (c) Acconeer AB, 2022-2023
# All rights reserved
# Copyright (c) Dylan Hoang, 2024.
# Based from the "plot.py" example found in Acconeer Exploration Tool.
# Measure the mean/average max peak over several frames.
# Configure your sensorconfig/subsweep and other parameters at the bottom of the code.
# Make sure to have the proper USB driver to comunicate to the radar via Serial, try it out first on the Acconeer Explorer Tool.

from __future__ import annotations

import sys
import numpy as np
import time

import acconeer.exptool as et
from acconeer.exptool import a121

def main(stop_frame, frame_duration, serialP, subsweepConf: list):
    args = a121.ExampleArgumentParser().parse_args()
    et.utils.config_logging(args)

    client = a121.Client.open(serial_port=serialP) #, **a121.get_client_args(args))

    session_config = a121.SessionConfig(
        [
            {
                1: a121.SensorConfig(
                    subsweeps=[
                        a121.SubsweepConfig(
                            start_point = subsweepConf[0],
                            # start_point=80,
                            step_length = subsweepConf[1],
                            # step_length=1,
                            num_points = subsweepConf[2],
                            # num_points=361,
                            profile = subsweepConf[3],
                            # profile=a121.Profile.PROFILE_3,
                            hwaas = subsweepConf[4],
                            #hwaas=8,
                        ),
                    ],
                )
            }#,
            #{
            #    1: a121.SensorConfig(
            #        receiver_gain=20,
            #    ),
            #},
        ],
        extended=True,
    )

    extended_metadata = client.setup_session(session_config)

    pg_updater = PGUpdater(session_config, extended_metadata, stop_frame, frame_duration)
    pg_process = et.PGProcess(pg_updater)
    pg_process.start()

    client.start_session()

    interrupt_handler = et.utils.ExampleInterruptHandler()
    print("Press Ctrl-C to end session")

    while not interrupt_handler.got_signal:
        extended_result = client.get_next()

        try:
            pg_process.put_data(extended_result)
        except et.PGProccessDiedException:
            break

    print("Disconnecting...")
    pg_process.close()
    client.close()

    entry = HInterface(stop_frame, frame_duration, serialP, subsweepConf)
    return entry.userInput()

class PGUpdater:
    def __init__(
        self,
        session_config: a121.SessionConfig,
        extended_metadata: list[dict[int, a121.Metadata]],
        stop_frame: int,
        frame_duration: float
    ) -> None:
        self.session_config = session_config
        self.extended_metadata = extended_metadata
        self.frame_index = 1
        self.sum_max = 0
        self.points = list()

        self.stop_frame = stop_frame
        self.frame_duration = frame_duration

    def setup(self, win):
        self.all_plots = []
        self.all_curves = []
        self.all_smooth_maxs = []

        for group_idx, group in enumerate(self.session_config.groups):
            group_plots = {}
            group_curves = {}
            group_smooth_maxs = {}

            for sensor_id, sensor_config in group.items():
                title = f"Amplitude Lens Test / Sensor {sensor_id}"
                plot = win.addPlot(title=title)
                plot.setMenuEnabled(False)
                plot.setMouseEnabled(x=False, y=False)
                plot.hideButtons()
                plot.showGrid(x=True, y=True)

                plot.setLabel("bottom", "Depth (m)")
                plot.setLabel("left", "Amplitude")

                curves = []
                for i in range(sensor_config.num_subsweeps):
                    curve = plot.plot(pen=et.utils.pg_pen_cycler(i))
                    curves.append(curve)

                group_plots[sensor_id] = plot
                group_curves[sensor_id] = curves

                smooth_max = et.utils.SmoothMax(self.session_config.update_rate)
                group_smooth_maxs[sensor_id] = smooth_max

            self.all_plots.append(group_plots)
            self.all_curves.append(group_curves)
            self.all_smooth_maxs.append(group_smooth_maxs)

    def update(self, extended_result: list[dict[int, a121.Result]]) -> None:
        for group_idx, group in enumerate(extended_result):
            for sensor_id, result in group.items():
                plot = self.all_plots[group_idx][sensor_id]
                curves = self.all_curves[group_idx][sensor_id]
                
                _max = 0
                
                for sub_idx, subframe in enumerate(result.subframes):
                    x = get_distances_m(
                        self.session_config.groups[group_idx][sensor_id].subsweeps[sub_idx]
                    )
                    y = np.abs(subframe).mean(axis=0)
                    curves[sub_idx].setData(x, y)

                    _max = max(_max, np.max(y))

                smooth_max = self.all_smooth_maxs[group_idx][sensor_id]
                
                #print(smooth_max)
                if self.frame_index <= self.stop_frame:
                    self.sum_max += _max
                    avg_max = self.sum_max / self.frame_index

                    print(f'Frame:   {self.frame_index}')
                    print(f'Average: {avg_max}')
                    print(f'Cur max: {_max}\n')
                    sys.stdout.flush() # flush stdout buffer for some "terminals".

                    self.frame_index += 1

                    plot.setYRange(0, smooth_max.update(_max))
                    self.points.append(_max)

                    time.sleep(self.frame_duration) 
                else:
                    import matplotlib.pyplot as plt
                    y = self.points
                    x = [i/10 for i in range(0, 50, 1)]

                    plt.plot(x, y)
                    plt.show()
                    return    
                
                # if self.frame_index == 51:

def get_distances_m(config):
    range_p = np.arange(config.num_points) * config.step_length + config.start_point
    return range_p * 2.5e-3

def clearOutput() -> None: 
    for i in range(10):
        print("\n")
    return

class HInterface:
    def __init__(self, stop_frame: int, frame_duration: float, serial_port: str, subsweepConf):
        self.stop_frame = stop_frame
        self.frame_duration = frame_duration
        self.serial_port = serial_port
        self.subsweepConf = subsweepConf

    def userInput(self):
        while True:
            print(f"Mean/Average Extractor (MAX) for A121 Acconeer Radar, \nThe default the duration is {self.stop_frame} frames with a duration of {self.frame_duration}s per frame.")
            print(f"The default settings can be changed at the bottom of the code, including the serial port (COM3 default).\n")
            print(f"Additional parameters such as the subsweep/sensor configuration can be modified in the bottom of the program, including the serial port (COM3 default).\n")
            print(f"CTRL+C to interrupt (stop) the program, while it's running.\n")

            inp = input("Enter 'r' to start, \nEnter 'm' to modify settings\nEnter 'e' to exit program \n: ")

            if inp.lower() == "e":
                quit()

            if inp.lower() == "r":
                return main(self.stop_frame, self.frame_duration, self.serial_port, self.subsweepConf)
            
            if inp.lower() == "m":
                clearOutput()
                inp = input("Enter Frames (integer number): ")
                self.stop_frame = int(inp)
                
                inp = input("Enter Frame duration (float number, in seconds): ")
                self.frame_duration = float(inp)
                
                print(f"\nUpdated to: \n\nFrames: {self.stop_frame} \nFrame duration: {self.frame_duration} s \nTotal duration: {round(self.stop_frame*self.frame_duration, 2)} s\n")

def startup():
    stop_frame = 50
    frame_duration = 0.1
    serial_port = "COM3"
    subsweepConf = [
        80,                     # Start_point,
        1,                      # Step_length,
        361,                    # Num_points,
        a121.Profile.PROFILE_3, # Profile (can also be PROFILE_1, PROFILE_2, PROFILE_4, PROFILE_5),
        8                       # HWAAS
    ]
    entry = HInterface(stop_frame, frame_duration, serial_port, subsweepConf)
    entry.userInput()

if __name__ == "__main__":
    startup()
