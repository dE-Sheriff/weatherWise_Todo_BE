import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()
API_key = os.getenv("API_KEY")
if not API_key:
    raise ValueError("API key not found. Make sure the .env file is correctly configured.")

app = Flask(__name__)
CORS(app) 

@app.route('/', methods=['GET'])
def home () -> dict:
    return {"success":True}

@app.route('/create', methods=['POST', 'GET'])
def create_task():
    if request.method == 'POST':
        # Use request.get_json() to parse JSON data from the request
        form_data = request.get_json()  
        return jsonify({"data": form_data})  # Return the data as a JSON response
    return jsonify({"message": "method is not post"})  # Handle GET request if needed

###########################################################

url_template = "https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}"

def check_availability(lat: float, lon: float, task_cat:str):
    url = url_template.format(lat=lat, lon=lon, api_key=API_key)
    res = requests.get(url)
    data_array = res.json().get('list')

    # Get the current UTC time
    current_time = datetime.now(timezone.utc)

    best_weather = None  # Variable to store the best forecast
    min_cloud_cover = float('inf')  # Initialize with a very large number to compare with

    for ele in data_array:
        # Extract necessary information
        clouds_all = ele.get('clouds', {}).get('all', 100)  # Default cloud cover to 100 if not present
        tod = ele.get('sys', {}).get('pod')  # 'd' for day, 'n' for night
        day_time = ele.get('dt_txt')  # Forecast timestamp as a string

        # Convert the day_time string to a datetime object
        forecast_time = datetime.strptime(day_time, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

        # Check if the forecast is in the future (greater than the current time)
        if forecast_time > current_time:
            # We're looking for the forecast with the least cloud cover
            if clouds_all < min_cloud_cover:
                min_cloud_cover = clouds_all
                # Prepare the forecast message based on time of day
                if tod == "d":
                    best_weather = {
                        "remark": f"This is good a perfect time for {task_cat}",
                        "closest forecast day": f'{forecast_time.strftime("%A")}',#day_time,
                        "closest forecast time": f'{forecast_time.strftime("%H:%M:%S")}'
                        # "clouds": clouds_all
                    }
                else:
                    best_weather = {
                        "remark": f"This is night time, might not be perfect for {task_cat}\n but you may wait a bit and reschedule.",
                        "day": f'{forecast_time.strftime("%A")}',#day_time,
                        "time": f'{forecast_time.strftime("%H:%M:%S")}'
                        # "date": day_time,
                        # "clouds": clouds_all
                    }
                    # print(f"best: {best_weather}")

    # If we found a valid forecast
    if best_weather:
        return best_weather
    else:
        return {"remark": "No suitable forecast found", "date": None}

@app.route('/weather', methods=['GET'])
def weather():
    # Extract lat and lon from query parameters
    lat = request.args.get('lat', type=float) 
    lon = request.args.get('lon', type=float)
    task_cat = request.args.get('taskcat', type=str)
    # print(f"task category: {task_cat}")

    if lat is None or lon is None:
        return jsonify({"error": "Latitude and Longitude are required."}), 400

    try:
        # Call the function to get the weather data
        result = check_availability(lat, lon, task_cat=task_cat)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# @app.route('/tasks/add', methods=['POST'])
# def add_task():

if __name__ == '__main__':
    app.run(debug=True)