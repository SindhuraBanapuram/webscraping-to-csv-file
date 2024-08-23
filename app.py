from flask import Flask, request, render_template, jsonify, send_file
from flask_cors import CORS
import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import pandas as pd
import os

app = Flask(__name__, template_folder='templates')
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/csv.html')
def serve_csv_html():
    return render_template('csv.html')

@app.route('/submit-url', methods=['POST'])
def submit_url():
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({'error': 'No URL provided in the form'}), 400

    try:
        response = requests.get(url)
        response.raise_for_status()
        scraped_data = scrape_data(url)
        if scraped_data:
            df = pd.DataFrame(scraped_data)
            csv_file_path = os.path.join(app.root_path, 'static', 'data.csv')
            df.to_csv(csv_file_path, index=False)
            return jsonify({'message': 'CSV generated successfully'}), 200
        else:
            return jsonify({'error': 'Failed to scrape data from the provided URL'}), 500
    except RequestException as e:
        return jsonify({'error': f'Failed to fetch data from the provided URL: {str(e)}'}), 500

@app.route('/download/csv')
def download_csv():
    csv_file_path = os.path.join(app.root_path, 'static', 'data.csv')
    if not os.path.exists(csv_file_path):
        return jsonify({'error': 'CSV file not found'}), 404
    response = send_file(csv_file_path, as_attachment=True)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

def scrape_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        data = []
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'a', 'img','rating','date-time']):
            text = tag.get_text(strip=True)
            tag_name = tag.name
            href = tag.get('href', '')
            tag_data = {
                'Tag': tag_name,
                'Text': text,
                'Href': href,
                'Src': tag.get('src', ''),           
                'Value': tag.get('value', ''),         
                'Date-Time': tag.get('datetime', '')  
            }
            data.append(tag_data)

        print(f'Scraped data: {data}')
        return data
    except requests.RequestException as e:
        print('RequestException:', e)
        return None
    except Exception as e:
        print('Error:', e)
        return None

if __name__ == "__main__":
    app.run(debug=True)
