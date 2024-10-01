import time
from datetime import datetime, timedelta
import os
import logging
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
import pytz

# Define log directory
log_dir = '/coding/logs'

# Ensure the log directory exists
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Setup logging
log_file = os.path.join(log_dir, 'process_video.log')
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Directories
video_dir = r"/coding/out"
mp3_dir = r"/coding/out"

# Define the timezone for Sweden
swedish_tz = pytz.timezone('Europe/Stockholm')

# Function to find the first MP4 file in the video directory
def find_mp4_file(directory):
    for file_name in os.listdir(directory):
        if file_name.endswith('.mp4'):
            return os.path.join(directory, file_name)
    return None

# Function to calculate the time until the next 00:15 AM Swedish time
def time_until_next_run():
    now = datetime.now(swedish_tz)
    next_run = now.replace(hour=0, minute=15, second=0, microsecond=0)

    if now > next_run:
        next_run += timedelta(days=1)

    return (next_run - now).total_seconds()

# Function to check if today is between Tuesday and Saturday
def should_run_today():
    today = datetime.now(swedish_tz).weekday()  # Monday is 0, Sunday is 6
    return 1 <= today <= 5  # Tuesday (1) to Saturday (5)

# Main function to process the video and audio
def process_video_and_audio():
    try:
        # Find the MP4 file in the directory
        mp4_path = find_mp4_file(video_dir)

        if mp4_path is None:
            logging.error(f"No MP4 file found in the directory: {video_dir}")
            return

        # List of audio files and their respective start times
        audio_timing = {
            'AAPL_stock_report.mp3': '00:00',
            'GOOGL_stock_report.mp3': '00:21',
            'META_stock_report.mp3': '00:44',
            'MSFT_stock_report.mp3': '01:06',
            'TSLA_stock_report.mp3': '01:28',
            'PLTR_stock_report.mp3': '01:50',
            'INTC_stock_report.mp3': '02:14',
            'NVDA_stock_report.mp3': '02:36',
            'AMD_stock_report.mp3': '02:57',
            'AMZN_stock_report.mp3': '03:20',
            'gainers_intro.mp3': '03:41',
            'gainer_9.mp3': '03:43',
            'gainer_8.mp3': '03:48',
            'gainer_7.mp3': '03:57',
            'gainer_6.mp3': '04:04',
            'gainer_5.mp3': '04:11',
            'gainer_4.mp3': '04:19',
            'gainer_3.mp3': '04:26',
            'gainer_2.mp3': '04:32',
            'gainer_1.mp3': '04:39',
            'losers_intro.mp3': '04:45',
            'loser_9.mp3': '04:47',
            'loser_8.mp3': '04:54',
            'loser_7.mp3': '05:01',
            'loser_6.mp3': '05:08',
            'loser_5.mp3': '05:15',
            'loser_4.mp3': '05:23',
            'loser_3.mp3': '05:30',
            'loser_2.mp3': '05:37',
            'loser_1.mp3': '05:44',
            'losers_outro.mp3': '05:50'
        }

        def time_str_to_seconds(time_str):
            """Convert a time string (HH:MM:SS or MM:SS) to seconds."""
            parts = list(map(int, time_str.split(':')))
            
            if len(parts) == 3:  # HH:MM:SS format
                h, m, s = parts
            elif len(parts) == 2:  # MM:SS format
                h = 0
                m, s = parts
            else:
                raise ValueError(f"Invalid time format: {time_str}")

            return h * 3600 + m * 60 + s

        # Load video file
        video = VideoFileClip(mp4_path)

        # Prepare a list of audio clips to overlay on the video
        audio_clips = []
        for mp3_file, start_time in audio_timing.items():
            audio_path = os.path.join(mp3_dir, mp3_file)
            if os.path.exists(audio_path):
                start_time_sec = time_str_to_seconds(start_time)
                audio = AudioFileClip(audio_path).set_start(start_time_sec)
                audio_clips.append(audio)
            else:
                logging.warning(f"Audio file {mp3_file} not found in the directory.")

        # Combine the audio clips
        composite_audio = CompositeAudioClip([video.audio] + audio_clips)

        # Set the composite audio to the video
        final_video = video.set_audio(composite_audio)

        # Export the final video
        output_path = os.path.join(video_dir, "final_output.mp4")
        final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")

        logging.info(f"Video successfully created at {output_path}")

    except Exception as e:
        logging.error(f"An error occurred while processing video and audio: {e}")

# Scheduler to run the task every day at 00:15 AM
while True:
    try:
        # Calculate the time until the next 00:15 AM
        time_to_sleep = time_until_next_run()

        # Wait until the next scheduled time
        logging.info(f"Sleeping for {time_to_sleep // 3600} hours and {(time_to_sleep % 3600) // 60} minutes...")
        time.sleep(time_to_sleep)

        # Check if today is a day we should run the task
        if should_run_today():
            logging.info("Running scheduled task...")
            process_video_and_audio()
        else:
            logging.info("Skipping task for today (Sunday/Monday).")

        # Wait 24 hours before checking again
        time.sleep(24 * 3600)
    
    except Exception as e:
        logging.error(f"An error occurred in the scheduler loop: {e}")
        time.sleep(60 * 15)  # Wait 15 minutes before retrying if there's an error
