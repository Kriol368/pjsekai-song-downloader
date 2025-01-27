import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from mutagen.id3 import ID3, TIT2, TPE1, APIC
from mutagen.mp3 import MP3
from io import BytesIO
from PIL import Image

BASE_URL = "https://www.sekaipedia.org"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com",
}

def fetch_song_links():
    URL = f"{BASE_URL}/wiki/List_of_songs"
    response = requests.get(URL, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch the main page. Status code: {response.status_code}")

    soup = BeautifulSoup(response.content, 'html.parser')
    tables = soup.find_all('table', class_='wikitable sortable')
    if not tables:
        raise Exception("No tables found on the main page.")

    cutoff_date = datetime.now() - timedelta(days=60)
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
    cover_image_tag = soup.find('meta', property="og:image")
    cover_image_url = cover_image_tag['content'] if cover_image_tag else "No cover image found"

    # Extracting audio details
    audio_details = []

    # Look for the second wikitable
    tables = soup.find_all('table', class_='wikitable')
    if len(tables) < 2:
        print("No second wikitable found.")
        return None

    # Get the second table
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


def download_audio(audio_url, song_folder, title, version_index):
    try:
        audio_response = requests.get(audio_url, headers=HEADERS)
        if audio_response.status_code == 200:
            # Add the version index to the audio file name to avoid overwriting
            audio_filename = f"{title}_{version_index}.mp3"
            audio_path = os.path.join(song_folder, audio_filename)
            with open(audio_path, "wb") as f:
                f.write(audio_response.content)
            return audio_path
        else:
            print(f"Failed to download audio: {audio_url}")
            return None
    except Exception as e:
        print(f"Error downloading audio: {e}")
        return None


def update_audio_metadata(audio_path, title, singers, cover_image_path):
    try:
        print(f"Attempting to update metadata for {title} at {audio_path}")
        audio_file = MP3(audio_path, ID3=ID3)
        audio_file.tags = ID3()

        # Add title and singer metadata
        audio_file.tags.add(TIT2(encoding=3, text=title))  # Title
        audio_file.tags.add(TPE1(encoding=3, text=", ".join(singers)))  # Singers

        if cover_image_path:
            # Add cover image if exists
            with open(cover_image_path, "rb") as img_file:
                audio_file.tags.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=img_file.read()))

        audio_file.save()
        print(f"Metadata updated for {title}")
    except Exception as e:
        print(f"Error updating audio metadata for {title} ({audio_path}): {e}")

def main():
    song_links = fetch_song_links()
    print(f"Found {len(song_links)} songs.")

    for idx, song_link in enumerate(song_links):  # Process first 5 songs
        print(f"Processing {idx + 1}/{len(song_links)}: {song_link}")
        metadata = fetch_song_metadata(song_link)
        if metadata:
            song_folder = os.path.join('out', metadata['title'])
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
                        print(f"No cover image for {metadata['title']}")
                else:
                    print(f"Failed to download audio for {metadata['title']}")


if __name__ == "__main__":
    main()
