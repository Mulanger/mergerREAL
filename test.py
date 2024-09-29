import psycopg2
import requests
import os
import logging
from datetime import datetime
import pytz

# Configure logging
logging.basicConfig(filename='stock_processing.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Dictionary mapping symbols to company names
symbol_to_name = {
    'TSLA': 'Tesla',
    'MSFT': 'Microsoft',
    'AAPL': 'Apple',
    'META': 'Meta',
    'GOOGL': 'Google',
    'AMZN': 'Amazon',
    'NVDA': 'Nvidia',
    'AMD': 'AMD',
    'INTC': 'Intel',
    'PLTR': 'Palantir Technologies'
}

# Unreal Speech API details
UNREAL_SPEECH_API_URL = "https://api.v7.unrealspeech.com/speech"
UNREAL_SPEECH_API_KEY = "Bearer 4DRugm2p3CkiNqtZyMZduBpHutfgcrZ14oMGRFPzo1MCdGS6118WgO"

# Function to save text as MP3 using Unreal Speech API
def save_text_to_mp3_unreal(text, filename, destination_directory, voice_id="Dan", bitrate="192k", speed="0",
                             pitch="1"):
    padded_text = text + "      "  # Add spaces as padding

    payload = {
        "Text": padded_text,
        "VoiceId": voice_id,
        "Bitrate": bitrate,
        "Speed": speed,
        "Pitch": pitch,
        "TimestampType": "sentence"
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": UNREAL_SPEECH_API_KEY
    }

    try:
        logging.debug(f"Sending request to Unreal Speech API for {filename} with text: {padded_text}")

        response = requests.post(UNREAL_SPEECH_API_URL, json=payload, headers=headers)
        response.raise_for_status()

        logging.debug(f"Response status: {response.status_code}, Response body: {response.text}")

        audio_uri = response.json().get('OutputUri')
        if not audio_uri:
            logging.error(f"Failed to get OutputUri for {filename}. Response body: {response.text}")
            return

        logging.debug(f"Audio URI received: {audio_uri}")

        # Download and save the audio file
        audio_response = requests.get(audio_uri)
        if audio_response.status_code == 200:
            file_path = os.path.join(destination_directory, filename)
            with open(file_path, 'wb') as f:
                f.write(audio_response.content)
            logging.info(f"Downloaded and saved {filename} to {file_path}")
        else:
            logging.error(f"Failed to download audio for {filename}. HTTP status: {audio_response.status_code}")

    except Exception as e:
        logging.error(f"Error generating MP3 for {filename}: {e}")


# Function to process and save stock data as MP3
def process_stocks():
    db_conn_str = "postgresql://retool:aOB15vnPYdMz@ep-misty-firefly-a6r0v691.us-west-2.retooldb.com/retool?sslmode=require"

    retries = 5
    for attempt in range(retries):
        try:
            conn = psycopg2.connect(db_conn_str)
            logging.info("Successfully connected to the database.")
            break
        except Exception as e:
            logging.error(f"Database connection attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(5)
            else:
                logging.critical("Failed to connect to the database after multiple attempts.")
                return

    try:
        cur = conn.cursor()

        # Fetch the stock entries from the "stocks" table
        cur.execute("SELECT id, symbol, open, high, low, close, volume, change, date FROM stocks LIMIT 10;")
        rows = cur.fetchall()
        logging.info("Fetched stock data from the database.")

        symbols = ['TSLA', 'MSFT', 'AAPL', 'META', 'GOOGL', 'AMZN', 'NVDA', 'AMD', 'INTC', 'PLTR']

        # Directory to move the MP3 files to
        destination_directory = r"/coding/out"
        os.makedirs(destination_directory, exist_ok=True)  # Create the directory if it doesn't exist

        for file in os.listdir(destination_directory):
            if file.endswith('.mp3'):
                os.remove(os.path.join(destination_directory, file))
                logging.info(f"Removed existing file: {file}")

        for row in rows:
            stock_id, symbol, open_price, high, low, close, volume, change, date = row
            if symbol in symbols:
                full_name = symbol_to_name[symbol]
                formatted_change = f"{change}"
                text = (f"{full_name} had an opening price of {open_price} today, reaching a daily high of {high}, "
                        f"followed by a daily low of {low} before closing up at {close}, leaving us with a {formatted_change} "
                        f"change from yesterday's closing price.")

                save_text_to_mp3_unreal(text, f"{symbol}_stock_report.mp3", destination_directory)

        cur.execute(
            "SELECT symbol, name, \"changesPercentage\" FROM gainers ORDER BY \"changesPercentage\" DESC LIMIT 9;")
        gainers = cur.fetchall()

        gainers_intro_text = "Here are today's top 9 gainers."
        save_text_to_mp3_unreal(gainers_intro_text, "gainers_intro.mp3", destination_directory)

        for i, (symbol, _, changesPercentage) in enumerate(reversed(gainers)):
            position = 9 - i
            text = f"Coming in at number {position}, we have {symbol} with a gain of {changesPercentage}% today."
            save_text_to_mp3_unreal(text, f"gainer_{position}.mp3", destination_directory)

        cur.execute(
            "SELECT symbol, name, \"changesPercentage\" FROM losers ORDER BY \"changesPercentage\" ASC LIMIT 9;")
        losers = cur.fetchall()

        losers_intro_text = "Here are today's top 9 losers."
        save_text_to_mp3_unreal(losers_intro_text, "losers_intro.mp3", destination_directory)

        for i, (symbol, _, changesPercentage) in enumerate(reversed(losers)):
            position = 9 - i
            text = f"Coming in at number {position}, we have {symbol} with a loss of {changesPercentage}% today."
            save_text_to_mp3_unreal(text, f"loser_{position}.mp3", destination_directory)

        losers_outro_text = "Thanks for watching today's video, don't forget to subscribe for daily stock videos."
        save_text_to_mp3_unreal(losers_outro_text, "losers_outro.mp3", destination_directory)

    except Exception as e:
        logging.error(f"An error occurred while processing stocks: {e}")
    finally:
        cur.close()
        conn.close()
        logging.info("Database connection has been closed.")

# Directly run the stock processing function
process_stocks()
