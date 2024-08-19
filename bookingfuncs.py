import requests
import numpy as np
import geopy.distance
import time
from pushbullet import Pushbullet
import subprocess

from seleniumbase import SB
import json

def notify_close_cars(loc, max_dis, api_key, book_car_enable, communauto_cred, ethical_mode, sleep_time=5, max_time=1800):
    try:
        # Process inputs
        book_car_enable = True if book_car_enable is not None else False
        communauto_cred = [item for item in communauto_cred.split(',')]

        if communauto_cred == ['']:
            book_car_enable = False

        max_dis = float(max_dis)

        # Set initial notification
        if book_car_enable:
            send_notification('Car search has started', 'The flex-app has begun searching for your car, you will be notified when a car is booked', api_key)
        else:
            send_notification('Car search has started', 'The flex-app has begun searching for your car, you will be notified when a car is close', api_key)

        # Log in
        if book_car_enable:
            customer_ID, session_ID = get_valid_session(communauto_cred)

        # Begin search
        num_loops = round(max_time / sleep_time)

        for i in range(num_loops):
            if i != 0:
                time.sleep(sleep_time)

            r = requests.get('https://www.reservauto.net/WCF/LSI/LSIBookingServiceV3.svc/GetAvailableVehicles?BranchID=1&LanguageID=2')
            cars = r.json()

            n = len(cars['d']['Vehicles'])
            car_list = np.empty((n,2))
            for i, car in enumerate(cars['d']['Vehicles']):
                lat_long = [car['Latitude'], car['Longitude']]
                carNo = car['CarId']
                distance = geopy.distance.geodesic(loc, lat_long).km
                car_list[i,:] = np.array([distance, carNo])

            car_list_filtered = car_list[car_list[:,0] < max_dis]
            car_list_filtered = car_list_filtered[car_list_filtered[:,0].argsort()] 
            num_cars = car_list_filtered.shape[0]

            ignore_list = []
            if (num_cars > 0):
                if book_car_enable == False:
                    if num_cars > 0:
                        if book_car_enable:
                            message = f'''A car was booked sucessfully'''
                            send_notification('Car booked', message, api_key)
                        else:
                            if num_cars==1:
                                message = f'There is 1 car that is {max_dis} km away'
                                send_notification('Car Found', message, api_key)
                            elif num_cars>1:
                                message = f'There are {num_cars} cars that are {max_dis} km away'
                                send_notification('Car Found', message, api_key)
                        return
                else:
                    if ethical_mode:
                        time.sleep(5)
                    for car in car_list_filtered[:,1]:
                        if car not in ignore_list:
                            booking_result, booking_message = book_car(int(car), customer_ID, session_ID)
                            if booking_result:
                                message = f'''A car was booked sucessfully'''
                                send_notification('Car booked', message, api_key)
                                return
                            elif booking_message == 'The booking limit on this vehicle has been reached.':
                                message = f'A booking was attempted but failed for the reason below. The search has is continuing.\n\n{booking_message}'
                                send_notification('Unsucessful booking', message, api_key) 
                                ignore_list.append(car)
                                time.sleep(.25)
                            elif booking_message == 'The vehicle is unavailable.':
                                message = f'A booking was attempted but failed for the reason below. The search is continuing.\n\n{booking_message}'
                                send_notification('Unsucessful booking', message, api_key) 
                            else:
                                message = f'A booking was attempted but failed for the reason below. The search has stopped.\n\n{booking_message}'
                                send_notification('search stopped', message, api_key) 
                                return

        send_notification('Car not found', 'Max time has been reached and no car was found', api_key)

    except Exception as e:
        message = f'The search has stopped. Please try again.\n\nThe script crashed for reason:\n\t{e}'
        send_notification('Script crashed', message, api_key)


def send_notification(title, message, api_key):
    pb = Pushbullet(api_key)
    pb.push_note('[Flex-app] ' + title, message)


def get_valid_session(communauto_cred):
    customer_ID, USER, PASS = communauto_cred

    LOGIN_URL = 'https://securityservice.reservauto.net/Account/Login?returnUrl=%2Fconnect%2Fauthorize%2Fcallback%3Fclient_id%3DCustomerSpaceV2Client%26redirect_uri%3Dhttps%253A%252F%252Fquebec.client.reservauto.net%252Fsignin-callback%26response_type%3Dcode%26scope%3Dopenid%2520profile%2520reservautofrontofficerestapi%2520communautorestapi%2520offline_access%26state%3D822a20f902424990988f76aea1218724%26code_challenge%3DGn39oR_skXJHjIL5um3Zv1iTt8ErcK5iid9EsIJgUo8%26code_challenge_method%3DS256%26ui_locales%3Den-ca%26acr_values%3Dtenant%253A1%26response_mode%3Dquery%26branch_id%3D1&ui_locales=en-ca&BranchId=1'

    with SB(uc=True, incognito=True, headless=False) as sb:
            # Open the login page
            sb.uc_open_with_reconnect(LOGIN_URL, reconnect_time=5)
            sb.uc_gui_click_captcha()
            sb.sleep(0.25)
            sb.type('input[name="Username"]', USER)
            sb.sleep(0.25)
            sb.type('input[name="Password"]', PASS)
            sb.uc_click('button.MuiButton-root.MuiButton-contained.MuiButton-containedPrimary')
            # Wait for the page to load completely
            sb.wait_for_ready_state_complete()
            # Navigate to the booking page
            sb.get('https://quebec.client.reservauto.net/bookCar')
            sb.wait_for_ready_state_complete()
    
            # Load the iframe form directly to extract the token
            sb.get('https://www.reservauto.net/Scripts/Client/ReservationAdd.asp?ReactIframe=true&CurrentLanguageID=2')
            sb.wait_for_ready_state_complete()
    
            # Extract the session ID from the cookies
            cookies = sb.get_cookies()
            session_ID = [f"{c['name']}={c['value']}" for c in cookies if c['name'] in 'mySession'][0]

    return customer_ID, session_ID

def book_car(car_ID, customer_ID, session_ID):

    url = f'https://www.reservauto.net/WCF/LSI/LSIBookingServiceV3.svc/CreateBooking?CustomerID={customer_ID}&CarID={car_ID}'

    header = {'Cookie': session_ID}
    r = requests.get(url, headers=header)

    if r.status_code == 200:
        if json.loads(r.content)['d']['Success']:
            return True, ''
        else:
            return False, json.loads(r.content)['d']['ErrorMessage']
    else:
        return False, f'Received response [{r.status_code}] expected [200]' 
