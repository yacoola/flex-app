# Draw Cicle on map:
# https://www.mapdevelopers.com/draw-circle-tool.php

import os
import requests
from tqdm import tqdm 
import numpy as np
import geopy.distance
import time
from dotenv import load_dotenv

from pushbullet import Pushbullet

load_dotenv()

def count_close_cars(max_dis, pause_time=5, max_time=1800):
    num_loops = round(max_time / pause_time)

    print('Searching for a car:')
    for i in tqdm(range(num_loops)):
        if i != 0:
            time.sleep(pause_time)

        home_latitude = float(os.getenv('home_latitude'))
        home_longitude = float(os.getenv('home_longitude'))
        home_lat_long = [home_latitude, home_longitude]

        r = requests.get('https://www.reservauto.net/WCF/LSI/LSIBookingServiceV3.svc/GetAvailableVehicles?BranchID=1&LanguageID=2')
        cars = r.json()

        car_list = np.array([])
        for car in cars['d']['Vehicles']:
            lat_long = [car['Latitude'], car['Longitude']]
            distance = geopy.distance.geodesic(home_lat_long, lat_long).km
            car_list = np.append(car_list, distance)

        num_cars = len(car_list[car_list < max_dis])
        
        if (num_cars > 0):
            break

    if i==0:
        print('there is already a car there dummy')
    elif num_cars==1:
        message = f'There is {num_cars} car that is {max_dis} km away'
        send_notification('Car Found', message)
    elif num_cars>1:
        message = f'There are {num_cars} cars that are {max_dis} km away'
        send_notification('Car Found', message)
    else:
        send_notification('Car not found', 'max time has been reached an not car was found')
    

def send_notification(title, message):
    api_key = os.getenv('pushbullet_apiKey')
    pb = Pushbullet(api_key)
    pb.push_note(title, message)


if __name__ == '__main__':
    count_close_cars(
        max_dis=0.5 , # km
        max_time=1800 # seconds
        )