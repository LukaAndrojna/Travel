import re
import pandas as pd

from time import sleep
from random import randint

from bs4 import BeautifulSoup

from pprint import pprint

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class FlightScraper:

    def __init__(self, nr_passengers, first_date_str, second_date_str, cityDeparture,
                 cityArrival, takeoff_after, takeoff_until, return_after, return_until):
        self._driver = None
        self._url = None
        self._classes = [
            'gws-flights-results__result-item gws-flights__flex-box gws-flights-results__collapsed',
            'gws-flights-results__result-item gws-flights__flex-box gws-flights-results__collapsed gws-flights-results__dominated'
        ]

        self._nr_passengers = nr_passengers
        self._first_date_str = first_date_str
        self._second_date_str = second_date_str
        self._cityDeparture = cityDeparture
        self._cityArrival = cityArrival
        self._takeoff_after = takeoff_after
        self._takeoff_until = takeoff_until
        self._return_after = return_after
        self._return_until = return_until

    def set_driver(self):
        self._driver = webdriver.Chrome()

    def get_driver(self):
        return self._driver

    def set_url(self):
        self._url = ''.join([f"https://www.google.com/flights?hl=en#flt={self._cityDeparture}",
                             f".{self._cityArrival}.{self._first_date_str}*{self._cityArrival}.{self._cityDeparture}",
                             f".{self._second_date_str};c:EUR;e:1;px:{self._nr_passengers};sd:1;t:f;dt:",
                             f"{self._takeoff_after}-{self._takeoff_until}*{self._return_after}-{self._return_until}"])

    def parse_flight_info(self, flight_info):
        info_dict = dict()
        for i in flight_info:
            if 'Arrival time' in i:
                info_dict['arrival_time'] = i.replace('Arrival time: ','')
            elif 'Departure time' in i:
                info_dict['departure_time'] = i.replace('Departure time: ','')
            elif 'From' in i:
                info_dict['price'] = float(re.findall(r'€[0-9,\.]*', i)[0].replace('€', '').replace(',', ''))
            elif 'Trip duration' in i:
                tmp = i.replace('Trip duration: ','').split(' h ')
                info_dict['duration'] = float(tmp[0]) + float(tmp[1].replace(' m', ''))/60
            elif 'stopover' in i:
                stopover_info = i.split(' stopover in ')
                if 'stopover' in info_dict:
                    info_dict['stopover'].append({'time': stopover_info[0], 'airport':stopover_info[1]})
                else:
                    info_dict['stopover'] = [{'time': stopover_info[0], 'airport':stopover_info[1]}]
            elif 'Departs from' in i:
                info_dict['departure'] = i.replace('Departs from ','')
            elif 'Arrives at' in i:
                info_dict['arrival'] = i.replace('Arrives at ','')
            elif 'flight' in i:
                flight_info = i.split(' flight by ')
                info_dict['company'] = flight_info[1]
                info_dict['stopovers'] = flight_info[0]
        return info_dict

    def get_data(self):
        self._driver.get(self._url)
        myElem = WebDriverWait(self._driver, 10).until(
            EC.presence_of_element_located((
                By.CLASS_NAME,
                'gws-flights-results__dominated-link')))
        myElem.click()
        sleep(15)
        soup = BeautifulSoup(self._driver.page_source, "lxml")
        flights = list()
        for c in self._classes:
            for li in soup.findAll('li', c):
                info = li.find('jsl').getText().split('.')
                try:
                    flights.append(self.parse_flight_info(info))
                except:
                    print('Couldn\'t parse:', li.find('jsl').getText())
        self._driver.quit()
        return flights

    def run(self):
        self.set_driver()
        self.set_url()
        return self.get_data()

def main():
    nr_passengers = 2
    first_date_str = '2020-09-24'
    second_date_str = '2020-10-01'
    cityDeparture = 'LJU'
    cityArrival = '/m/04jpl'
    takeoff_after = '0000'
    takeoff_until = '2359'
    return_after = '0000'
    return_until = '2359'

    fs = FlightScraper(nr_passengers, first_date_str,
                       second_date_str, cityDeparture,
                       cityArrival, takeoff_after,
                       takeoff_until, return_after,
                       return_until)

    tmp = fs.run()
    df = pd.DataFrame(tmp)
    print(df.price.min())
    print(df.price.median())
    print(df.price.max())
    print(df.duration.min())
    print(df.duration.median())
    print(df.duration.max())
    print(len(tmp))


if __name__ == "__main__":
    main()

#https://gitlab.com/cintibrus/scrap_flights