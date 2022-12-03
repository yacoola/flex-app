import os
import requests
from tqdm import tqdm 
import numpy as np
import geopy.distance
import time
from pushbullet import Pushbullet

def notify_close_cars(loc, max_dis, api_key, sleep_time=5, max_time=1800):
    try:
        max_dis = float(max_dis)

        # Set initial notification 
        send_notification('Car search has started', 'The flex-app has begun searching for your car', api_key)

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
            message = f'There is 1 car that is {max_dis} km away'
            send_notification('Car Found', message, api_key)
        elif num_cars>1:
            message = f'There are {num_cars} cars that are {max_dis} km away'
            send_notification('Car Found', message, api_key)
        else:
            send_notification('Car not found', 'Max time has been reached and no car was found', api_key)

    except Exception as e:
        message = f'The search has stopped. Please try again.\n\nThe script crashed for reason:\n\t{e}'
        send_notification('Script crashed', message, api_key)        
    

def send_notification(title, message, api_key):
    pb = Pushbullet(api_key)
    pb.push_note('[Flex-app] ' + title, message)
