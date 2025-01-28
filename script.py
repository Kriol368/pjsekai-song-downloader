import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from mutagen.id3 import ID3, TIT2, TPE1, APIC, TALB
from mutagen.mp3 import MP3
from io import BytesIO
from PIL import Image
import subprocess
import shutil

# Base URL for Sekaipedia
BASE_URL = "https://www.sekaipedia.org"

# Headers for making HTTP requests appear like a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com",
}

# Fetch a list of song links from Sekaipedia's List of Songs page
def fetch_song_links():
    URL = f"{BASE_URL}/wiki/List_of_songs"
    response = requests.get(URL, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch the main page. Status code: {response.status_code}")

    soup = BeautifulSoup(response.content, 'html.parser')
    tables = soup.find_all('table', class_='wikitable sortable')
    if not tables:
        raise Exception("No tables found on the main page.")

    cutoff_date = datetime.now() - timedelta(days=60)  # Filter for songs added in the last 60 days
    song_links = []

    for table in tables:
        rows = table.find('tbody').find_all('tr')
        for row in rows[1:]:
            cells = row.find_all('td')
            if len(cells) < 7:
                continue
            link_tag = cells[0].find('a')
            if link_tag and 'href' in link_tag.attrs:
                song_link = BASE_URL + link_tag['href']
                try:
                    date_added = datetime.strptime(cells[6].text.strip(), "%Y/%m/%d")
                    if date_added < cutoff_date:
                        song_links.append(song_link)
                except ValueError:
                    print(f"Skipping row with invalid date: {cells[6].text.strip()}")
                    continue

    return song_links

# Fetch metadata for a specific song
def fetch_song_metadata(song_link):
    response = requests.get(song_link, headers=HEADERS)
    if response.status_code != 200:
        print(f"Failed to fetch page: {song_link}. Status code: {response.status_code}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')

    # Extracting song title
    title_tag = soup.title.string if soup.title else "Unknown Title"
    title = title_tag.replace(" - Sekaipedia", "").strip()

    # Extracting cover image URL
    cover_image_tag = soup.find('img', src=lambda value: value and 'Jacket' in value)
    cover_image_url = "https:" + cover_image_tag['src']
    # If the URL contains '/thumb/' and the resolution part (e.g., /220px), process it
    if "/thumb/" in cover_image_url:
        # Remove '/thumb/' and the part after the resolution (e.g., /220px)
        cover_image_url = cover_image_url.replace("/thumb/", "/").split("/220px-")[0]

    # Extracting audio details
    audio_details = []

    # Look for the second wikitable
    tables = soup.find_all('table', class_='wikitable')
    if len(tables) < 2:
        print("No second wikitable found.")
        return None

    # Get the second table containing audio details
    second_table = tables[1]
    rows = second_table.find_all('tr')[1:]  # Skip header row

    # Loop through each row to extract singer and audio details for each version
    for row in rows:
        cells = row.find_all('td')
        if len(cells) < 3:
            continue

        # Extract singers
        singer_cells = cells[1].find_all('a')
        singers = [singer.text.strip() for singer in singer_cells]

        # Extracting audio link
        audio_cell = cells[2]
        audio_tag = audio_cell.find('audio')

        if audio_tag:
            source_tag = None
            for source in audio_tag.find_all('source'):
                if source.get('src'):
                    source_tag = source
                    break

            if source_tag:
                audio_link = 'https:' + source_tag['src']
            else:
                audio_link = "No valid audio source found"
        else:
            audio_link = "No audio found"

        audio_details.append({
            "singers": singers,
            "audio_link": audio_link
        })

    return {
        "title": title,
        "cover_image": cover_image_url,
        "audio_details": audio_details,
    }

# Download the cover image and save it locally
def download_cover_image(cover_image_url, song_folder):
    try:
        img_response = requests.get(cover_image_url, headers=HEADERS)
        if img_response.status_code == 200:
            img_data = BytesIO(img_response.content)
            img = Image.open(img_data)
            img = img.convert('RGB')  # Convert RGBA to RGB
            img_path = os.path.join(song_folder, "cover.jpg")
            img.save(img_path)
            return img_path
        else:
            print(f"Failed to download cover image: {cover_image_url}")
            return None
    except Exception as e:
        print(f"Error downloading cover image: {e}")
        return None

# Download the audio file and save it locally
def download_audio(audio_url, song_folder, title, version_index):
    try:
        os.makedirs(song_folder, exist_ok=True)  # Ensure the folder exists
        sanitized_title = sanitize_filename(title)
        audio_filename = f"{sanitized_title}_{version_index}.mp3"
        audio_path = os.path.join(song_folder, audio_filename)

        audio_response = requests.get(audio_url, headers=HEADERS)
        if audio_response.status_code == 200:
            with open(audio_path, "wb") as f:
                f.write(audio_response.content)
            return audio_path
        else:
            print(f"Failed to download audio: {audio_url}")
            return None
    except Exception as e:
        print(f"Error downloading audio: {e}")
        return None

#Sanitize the filename to avoid errors
def sanitize_filename(filename):
    # Replace any invalid characters with underscores
    return re.sub(r'[<>:"/\\|?*]', '_', filename).strip()

# Check if the file is an MP3
def is_mp3(audio_path):
    """Check if the audio file is in MP3 format."""
    try:
        audio_file = MP3(audio_path, ID3=ID3)
        return True
    except:
        return False

# Convert audio files to MP3 format (if necessary)
def convert_to_mp3(audio_path):
    """Convert OGG or other formats to MP3 and clean up old files."""
    output_path = audio_path.replace('.ogg', '.mp3').replace('.wav', '.mp3').replace('.flac', '.mp3')  # Additional formats can be added

    # Check if the file already exists and adjust the name if necessary
    if os.path.exists(output_path):
        base, ext = os.path.splitext(output_path)
        counter = 1
        while os.path.exists(output_path):
            output_path = f"{base}_{counter}{ext}"
            counter += 1

    try:
        # Run the conversion command
        subprocess.run(['ffmpeg', '-i', audio_path, '-acodec', 'libmp3lame', '-ar', '44100', output_path], check=True)
        print(f"Converted {audio_path} to {output_path}")

        # Remove the original non-MP3 file after conversion
        if os.path.exists(audio_path):
            os.remove(audio_path)

        # Rename the new file to the original filename (if needed)
        os.rename(output_path, audio_path)

        return audio_path  # Return the renamed file path
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")
        return None

# Update metadata for the downloaded audio (e.g., title, singers, cover image)
def update_audio_metadata(audio_path, title, singers, cover_image_path):
    try:
        # Convert the file to MP3 if it's not already
        print(f"Converting {audio_path} to MP3 (if needed)...")
        converted_path = convert_to_mp3(audio_path)
        if not converted_path:
            print(f"Skipping {audio_path}, conversion failed.")
            return
        audio_path = converted_path  # Use the newly converted file (or the original if already MP3)

        print(f"Attempting to update metadata for {title} at {audio_path}")
        audio_file = MP3(audio_path, ID3=ID3)
        print(f"Initial Audio tags: {audio_file.tags}")  # Debugging line

        # Reset any existing tags
        audio_file.tags = ID3()

        # Add title and singer metadata
        print(f"Adding title: {title}")
        audio_file.tags.add(TIT2(encoding=3, text=title))  # Title
        print(f"Adding singers: {', '.join(singers)}")
        audio_file.tags.add(TPE1(encoding=3, text=", ".join(singers)))  # Singers

        # Add album metadata
        album_name = "Project SEKAI"
        print(f"Adding album: {album_name}")
        audio_file.tags.add(TALB(encoding=3, text=album_name))  # Album

        # Add cover image if provided
        if cover_image_path:
            print(f"Adding cover image from {cover_image_path}")
            with open(cover_image_path, "rb") as img_file:
                img_data = img_file.read()  # Read the image file
                audio_file.tags.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=img_data))
                print(f"Cover image added to metadata.")
        else:
            print("No cover image provided, skipping cover image metadata.")

        # Save the updated metadata
        audio_file.save()
        print(f"Metadata updated for {title}")
    except Exception as e:
        print(f"Error updating audio metadata for {title} ({audio_path}): {e}")

# Re-encode MP3 files to ensure compatibility
def reencode_mp3(audio_path):
    output_path = audio_path.replace('.mp3', '_reencoded.mp3')
    try:
        print(f"Attempting to re-encode {audio_path} to {output_path}")

        # Run ffmpeg command to re-encode the audio file
        subprocess.run(['ffmpeg', '-i', audio_path, '-acodec', 'libmp3lame', '-ar', '44100', output_path], check=True)

        # If re-encoding was successful, return the new path
        print(f"Re-encoding successful: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error during re-encoding {audio_path}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error during re-encoding {audio_path}: {e}")
        return None

# Function to clear the 'out' folder before execution
def clear_output_folder():
    out_folder = 'out'
    if os.path.exists(out_folder):
        shutil.rmtree(out_folder)  # Remove the folder and all its contents
        print(f"Cleared the {out_folder} folder.")
    else:
        print(f"{out_folder} folder does not exist. Creating a new one.")
        os.makedirs(out_folder)  # Create the folder if it doesn't exist

# Main function to execute the process
def main():
    clear_output_folder()
    song_links = fetch_song_links()  # Fetch song links
    print(f"Found {len(song_links)} songs.")

    for idx, song_link in enumerate(song_links):
        print(f"Processing {idx + 1}/{len(song_links)}: {song_link}")
        metadata = fetch_song_metadata(song_link)
        if metadata:
            # Replace special characters with a safe character like an underscore
            safe_title = re.sub(r'[<>:"/\\|?*,]', '_', metadata['title'])
            song_folder = os.path.join('out', safe_title)
            os.makedirs(song_folder, exist_ok=True)


            # Download cover image
            cover_image_path = download_cover_image(metadata['cover_image'], song_folder)

            # Download audio and update metadata
            for version_index, version in enumerate(metadata['audio_details']):
                audio_path = download_audio(version['audio_link'], song_folder, metadata['title'], version_index)
                if audio_path:
                    print(f"Audio downloaded: {audio_path}")
                    if cover_image_path:
                        update_audio_metadata(audio_path, metadata['title'], version['singers'], cover_image_path)
                    else:
                        print(f"No cover image to update for {audio_path}")

if __name__ == "__main__":
    main()
