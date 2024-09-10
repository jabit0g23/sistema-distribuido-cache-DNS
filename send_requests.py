import requests
import random
import time
import pandas as pd

# Lee los dominios desde un archivo CSV tomando la primera columna sin importar su nombre
domains_df = pd.read_csv('3rd_lev_domains.csv', header=0)
domains = domains_df.iloc[:, 0].tolist()  # Toma la primera columna sin importar el nombre

# Lista de dominios conocidos

"""
domains = [
    'google.com', 'youtube.com', 'facebook.com', 'amazon.com', 'wikipedia.org', 'twitter.com', 
    'instagram.com', 'linkedin.com', 'apple.com', 'microsoft.com', 'netflix.com', 'reddit.com',
    'whatsapp.com', 'pinterest.com', 'yahoo.com', 'ebay.com', 'bing.com', 'paypal.com',
    'twitch.tv', 'weather.com', 'cnn.com', 'bbc.com', 'nytimes.com', 'espn.com', 
    'booking.com', 'dropbox.com', 'zoom.us', 'salesforce.com', 'spotify.com', 'adobe.com',
    'quora.com', 'medium.com', 'github.com', 'stackoverflow.com', 'etsy.com', 'aliexpress.com',
    'tesla.com', 'hulu.com', 'disneyplus.com', 'vimeo.com', 'airbnb.com', 'uber.com', 
    'lyft.com', 'target.com', 'walmart.com', 'homedepot.com', 'ikea.com', 'nasa.gov',
    'forbes.com', 'businessinsider.com', 'bloomberg.com', 'fifa.com', 'nba.com', 
    'kickstarter.com', 'coursera.org', 'udemy.com', 'edx.org', 'khanacademy.org', 
    'bbc.co.uk', 'guardian.co.uk', 'wired.com', 'reuters.com', 'buzzfeed.com', 'vice.com',
    'tumblr.com', 'wordpress.com', 'tiktok.com', 'slack.com', 'zoom.com', 'mailchimp.com'
]
"""

# URL de la API Flask
api_url = 'http://localhost:5001/dns'


while True:
    # Selecciona un dominio aleatorio
    domain = random.choice(domains)
    try:
        # Envía la solicitud GET a la API
        response = requests.get(api_url, params={'domain': domain})
        data = response.json()
        print(f"Request to {domain}: {data}")
    except requests.exceptions.RequestException as e:
        print(f"Error requesting {domain}: {e}")

    time.sleep(1)
