"""class for searching for bathrooms"""
import time
import googlemaps
import GoogleMapsAPIKey
import requests
import pprint
from urllib.parse import urlencode, urlparse, parse_qsl

API_KEY = GoogleMapsAPIKey.api_key

gmaps = googlemaps.Client(key=API_KEY)

class GoogleSearchClass(object):
    lat = None
    lng = None
    data_type = 'json'
    location_query = None
    api_key = None
    search_results = {}
    bathroom_type = ['restaurant', 'cafe', 'food', 'book_store', 'point_of_interest', 'supermarket', 'home_goods_store', 'movie_theater', 'library']
    place_ids = []
    detailed_list = []
    # page_2 = {}
    filtered=[]


    def __init__(self, api_key=None, address_or_postal_code=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if api_key == None:
            raise Exception("API key is required")
        self.api_key = api_key
        self.location_query = address_or_postal_code
        if self.location_query != None:
            self.extract_lat_lng()
    
    def extract_lat_lng(self, location=None):
        loc_query = self.location_query
        if location != None:
            loc_query = location
        endpoint = f"https://maps.googleapis.com/maps/api/geocode/{self.data_type}"
        params = {"address": loc_query, "key": self.api_key}
        url_params = urlencode(params)
        url = f"{endpoint}?{url_params}"
        r = requests.get(url)
        if r.status_code not in range(200, 299): 
            return {}
        latlng = {}
        try:
            latlng = r.json()['results'][0]['geometry']['location']
        except:
            pass
        lat,lng = latlng.get("lat"), latlng.get("lng")
        self.lat = lat
        self.lng = lng
        return lat, lng
    
    def search(self, keyword='food store', location=None, rankby='distance', pagetoken=None):
        lat, lng = self.lat, self.lng
        if location != None:
            lat, lng = self.extract_lat_lng(location=location)
        endpoint = f"https://maps.googleapis.com/maps/api/place/nearbysearch/{self.data_type}"
        params = {
            "key": self.api_key,
            "location": f"{lat},{lng}",
            "rankby": rankby,
            "keyword": keyword
        }
        params_encoded = urlencode(params)
        places_url = f"{endpoint}?{params_encoded}"
        r = requests.get(places_url)
        if r.status_code not in range(200, 250):
                    return {}
        results = r.json()


        self.search_results = results
        return results 
        
 
    def filter_results(self):
        results = self.search_results
        bathroom = self.bathroom_type
        filtered = self.filtered
        place_id_list = []

        for place in results['results']:
            if 'OPERATIONAL' in place.values() and any(item in bathroom for item in place['types']):
                filtered.append(place)
                place_id_list.append(place['place_id'])

        # for place in page_2['results']:
        #     if 'OPERATIONAL' in place.values() and any(item in bathroom for item in place['types']):
        #         # filtered.append(place)
        #         place_id_list.append(place['place_id'])
        
        
        self.place_ids = place_id_list
        self.search_results={}
        print(type(filtered))
        return filtered, place_id_list
        
    # Show details of place 
    def detail(self, place_id=id, fields=["name", "rating", "formatted_phone_number", "formatted_address", "place_id"]):
        place_id_list = self.place_ids
        detailed_list = []

        # for place in filtered:
        #     place_id = place.place_id
        #     detail_base_endpoint = f"https://maps.googleapis.com/maps/api/place/details/{self.data_type}"
        #     detail_params = {
        #     "place_id": f"{place_id}",
        #     "fields" : ",".join(fields),
        #     "key": self.api_key
        #     }

        for id in place_id_list:
            place_id = id
            detail_base_endpoint = f"https://maps.googleapis.com/maps/api/place/details/{self.data_type}"
            detail_params = {
            "place_id": f"{place_id}",
            "fields" : ",".join(fields),
            "key": self.api_key
            }
        
            detail_params_encoded = urlencode(detail_params)
            detail_url = f"{detail_base_endpoint}?{detail_params_encoded}"
            r = requests.get(detail_url)
            if r.status_code not in range(200, 250):
                return {}

            
            result = r.json()
            detailed_list.append(result['result'])

        self.detailed_list = detailed_list
        self.place_ids=[]
        return detailed_list
       
