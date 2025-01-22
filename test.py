import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

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

    # Extracting song title (removing "- Sekaipedia" from title)
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

        # Extract singers (text only from column 2, no href)
        singer_cells = cells[1].find_all('a')
        singers = [singer.text.strip() for singer in singer_cells]

        # Extract audio link (href from column 3)
        audio_cell = cells[2]
        audio_tag = audio_cell.find('a', href=True)
        if audio_tag:
            audio_link = audio_tag['href']  # Just use the href as the full URL
        else:
            audio_link = "No audio found"

        # Append the data for each version
        audio_details.append({
            "singers": singers,
            "audio_link": audio_link
        })

    return {
        "title": title,
        "cover_image": cover_image_url,
        "audio_details": audio_details,
        "singers_info": audio_details,  # Add the singers and audio details
    }


def main():
    song_links = fetch_song_links()
    print(f"Found {len(song_links)} songs.")

    all_song_data = []
    for idx, song_link in enumerate(song_links[:5]):
        print(f"Processing {idx + 1}/{len(song_links)}: {song_link}")
        metadata = fetch_song_metadata(song_link)
        if metadata:
            all_song_data.append(metadata)

    # Output all data
    for song_data in all_song_data:
        print("\n--- Song Data ---")
        print(f"Title: {song_data['title']}")
        print(f"Cover Image: {song_data['cover_image']}")
        if song_data['singers_info']:
            for singer_info in song_data['singers_info']:
                print(f"  Singers: {', '.join(singer_info['singers'])}")
                print(f"  Audio Link: {singer_info['audio_link']}")
        else:
            print("  No singer or audio details found.")


if __name__ == "__main__":
    main()
