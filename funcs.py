import os
import requests
from tqdm import tqdm 
import numpy as np
import geopy.distance
import time
from pushbullet import Pushbullet

def notify_close_cars(loc, max_dis, api_key, sleep_time=5, max_time=1800):
    max_dis = float(max_dis)

    # Set initial notification 
    send_notification('car search has started', 'The flex-notifier has begun searching for you\'re car', api_key)

    # Begin search
    num_loops = round(max_time / sleep_time)

    for i in range(num_loops):
        if i != 0:
            time.sleep(sleep_time)

        r = requests.get('https://www.reservauto.net/WCF/LSI/LSIBookingServiceV3.svc/GetAvailableVehicles?BranchID=1&LanguageID=2')
        cars = r.json()

        car_list = np.array([])
        for car in cars['d']['Vehicles']:
            lat_long = [car['Latitude'], car['Longitude']]
            distance = geopy.distance.geodesic(loc, lat_long).km
            car_list = np.append(car_list, distance)

        num_cars = len(car_list[car_list < max_dis])
        
        if (num_cars > 0):
            break

    if num_cars==1:
        message = f'There is {num_cars} car that is {max_dis} km away'
        send_notification('Car Found', message, api_key)
    elif num_cars>1:
        message = f'There are {num_cars} cars that are {max_dis} km away'
        send_notification('Car Found', message, api_key)
    else:
        send_notification('Car not found', 'max time has been reached an not car was found', api_key)
    

def send_notification(title, message, api_key):
    pb = Pushbullet(api_key)
    pb.push_note(title, message)


if __name__ == '__main__':
    notify_close_cars(
        loc= [45.530330, -73.570650],
        api_key='o.p3eCoegV4yHnXASY6ln0eZgveLvqsF4t',
        max_dis=0.5 , # km
        max_time=1800 # seconds
        )