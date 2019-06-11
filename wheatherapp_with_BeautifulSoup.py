"""'weatherapp.py' can find the condition of the weather
 and the temperature of the air from a given web site"""

from pathlib import Path
import configparser
import html
import sys
import argparse
from bs4 import BeautifulSoup
from urllib.request import urlopen, Request

RP5_BROWSER_LOCATIONS = 'https://rp5.ua/%D0%9F%D0%BE%D0%B3%D0%BE%D0%B4%D0%B0_%D0%B2_%D1%81%D0%B2%D1%96%D1%82%D1%96'
ACCU_BROWSER_LOCATIONS = "https://www.accuweather.com/uk/browse-locations"
CONFIG_LOCATION = 'Location'
CONFIG_FILE = 'weatherapp.ini'
DEFAULT_NAME ='Kyiv'
DEFAULT_URL_ACCU = 'https://www.accuweather.com/uk/ua/kyiv/324505/weather-forecast/324505'
DEFAULT_URL_RP5 = 'https://rp5.ua/%D0%9F%D0%BE%D0%B3%D0%BE%D0%B4%D0%B0_%D0%B2_%D0%9A%D0%B8%D1%94%D0%B2%D1%96,_%D0%96%D1%83%D0%BB%D1%8F%D0%BD%D0%B0%D1%85_(%D0%B0%D0%B5%D1%80%D0%BE%D0%BF%D0%BE%D1%80%D1%82)'

def get_page_sourse(url):
    """ Function, that helps get all code from web-site"""
    headers = {'User-Agent': 'Mozilla/5.0(X11; Fedora; Linux x86_64;)'}
    request = Request(url, headers=headers)
    page = urlopen(request).read()
    content = str(page.decode("utf-8"))
    return content


def get_weather_info_accu(content):
    """ Function, that parses through each of the given tags"""
    city_page = BeautifulSoup(content, 'html.parser')
    weather_info = {}
    select_current_town = city_page.find("li", class_="last")
    if select_current_town:
        weather_info['site_name'] = 'AccuWeather'
        weather_info['name_town'] = select_current_town.text
        current_town_url = city_page.find('a').get('href')
        if current_town_url:
            current_town_page = get_page_sourse(current_town_url)
            if current_town_page:
                current_town = BeautifulSoup(current_town_page,'html.parser')
                weather_detail = current_town.find('div', class_="info")
                condition = current_town.find('span', class_='cond' )
                if condition:
                    weather_info['cond'] = condition.text
                temp = weather_detail.find('span',class_='large-temp')
                if temp:
                    weather_info['temp'] = temp.text
                feel_temp = weather_detail.find('span', class_='real-feel')
                if feel_temp:
                    weather_info['real-feel'] = feel_temp.text
    return weather_info


def get_locations_accu(browser_locator):
    """Function helps find list of all country and town in the world"""
    location_page = get_page_sourse(browser_locator)
    soup = BeautifulSoup(location_page, 'html.parser')
    locators = []
    for locator in soup.find_all('li', class_="drilldown cl"):
        url_div = locator.find('div', class_='info')
        for link in url_div.find_all('a'):
            url = link.get('href')
            location = locator.find('em').text
            locators.append((location, url))
    return(locators)


def get_configuration_accu():
    """ Function saves necessary information in user_file"""
    url = DEFAULT_URL_ACCU
    name = DEFAULT_NAME

    parser = configparser.ConfigParser()
    parser.read(get_configuration_file())

    if CONFIG_LOCATION in parser.sections():
        config = parser[CONFIG_LOCATION]
        name, url = config['name'], config['url']
    return name, url


def get_accu_weather_info():
    """Function can find name and url of founded city, and show weather of that city"""
    city_name, city_url = get_configuration_accu()
    content = get_page_sourse(city_url)
    weather_on_accu = get_weather_info_accu(content)
    produce_output(city_name, weather_on_accu)


def configurate():
    """Function can show list of the country and city, and can propose choose any country or city"""
    locations = get_locations_accu(ACCU_BROWSER_LOCATIONS)
    while locations:
        for index, location in enumerate(locations):
            print(f'{index+1}.{location[0]}')
        selected_index = int(input('Please select location: '))
        location = locations[selected_index-1]
        locations = get_locations_accu(location[1])
    save_configuration(*location)


def get_configuration_file():
    """Function return path to user_file"""
    return (Path.home() / CONFIG_FILE)


def save_configuration(name, url):
    """Function saves founded information from command "config" in user_file"""
    parser = configparser.ConfigParser()
    parser[CONFIG_LOCATION] = {'name' : name, 'url': url}
    with open(get_configuration_file(),'w') as configfile:
        parser.write(configfile)


def get_weather_info_rp5(content):
    """ Function, that parses through each of the given tags"""
    city_page = BeautifulSoup(content, 'html.parser')
    # print(city_page,"****")
    weather_info = {}
    select_town = city_page.find("div", id="FheaderContent")
    if select_town:
        weather_info['site_name'] = 'RP5'
        select_current_town = select_town.find("div", id="pointNavi")
        weather_info['name_town'] = select_current_town.text
        temp = city_page.find('div', id="ArchTemp")
        if temp:
            weather_info['temp'] = temp.get_text(', ')
        condition_town = city_page.find('div', class_='ArchiveInfo')
        condition = condition_town.find('span', class_="t_1")
        if condition:
            weather_info['cond'] = condition_town.text
    return weather_info


def get_rp5_weather_info():
    """Function returns information from site rp5, by default city"""
    city_name, city_url = DEFAULT_NAME, DEFAULT_URL_RP5
    content = get_page_sourse(city_url)
    weather_on_rp5 = get_weather_info_rp5(content)
    produce_output(city_name, weather_on_rp5)


def produce_output(city_name, info):
    """Function, that can dis lkaplay information, that were founded before"""
    print(f'{city_name}')
    print('_'*20)
    for key, value in info.items():
        print(f'{key}: {html.unescape(value)}')


def main(argv):
    """ main function, where you can call up the required functions """

    weather_command = {"accu": get_accu_weather_info, "config": configurate, "rp5": get_rp5_weather_info}
    parser = argparse.ArgumentParser()
    parser.add_argument("command",
                        help="Enter command, which help you to open weather in your town", nargs = 1)
    param = parser.parse_args(argv)
    if param.command:
        command = param.command[0]
        if command in weather_command:
            weather_command[command]()
        else:
            print("Could not find the appropriate command")
            sys.exit(1)

if __name__ == "__main__":
    main(sys.argv[1:])
