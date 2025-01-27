# Sekaipedia Song Downloader

This Python project scrapes the Sekaipedia website to fetch metadata and download songs along with their cover images. It also updates the song metadata, including title, singers, and album art.

## Project under construction!!!

## Features

- Scrape song metadata from [Sekaipedia](https://www.sekaipedia.org)
- Filter songs added in the last 60 days
- Download song cover images and audio files
- Update ID3 metadata for MP3 files, including title, singers, and album art

## Requirements

- Python 3.9+
- Libraries:
  - `requests`
  - `BeautifulSoup4`
  - `mutagen`
  - `Pillow`

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/sekaipedia-song-downloader.git
   cd sekaipedia-song-downloader
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Create an output directory for the downloaded files:
   ```bash
   mkdir out
   ```

## Usage

Run the script using Python:
```bash
python script.py
```

The script will:
1. Fetch the list of songs from Sekaipedia added in the last 60 days.
2. Scrape metadata for each song, including:
   - Title
   - Singers
   - Cover image URL
   - Audio file links
3. Download the cover image and audio files for each song.
4. Update the MP3 files with title, singers, and album art metadata.

### Output
Downloaded songs and their metadata are saved in the `out` directory, with a subfolder for each song.

## Example Directory Structure

```
out/
├── Song Title 1/
│   ├── cover.jpg
│   ├── Song Title 1_0.mp3
│   └── Song Title 1_1.mp3
└── Song Title 2/
    ├── cover.jpg
    └── Song Title 2_0.mp3
```

## Configuration

- **Base URL:** The script uses `https://www.sekaipedia.org` as the base URL for scraping.
- **User-Agent:** Custom headers are used to mimic a browser request.

## Troubleshooting

- **No Songs Found:** Ensure that the URL structure of Sekaipedia has not changed.
- **Invalid Dates:** The script skips rows with invalid dates in the table.
- **Failed Downloads:** Check your internet connection and verify the URLs being fetched.

## Limitations

- The script is designed to scrape data only from Sekaipedia and may not work if the website's structure changes.
- Only MP3 files with valid audio sources are downloaded.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Data source: [Sekaipedia](https://www.sekaipedia.org)
- Libraries: `requests`, `BeautifulSoup`, `mutagen`, `Pillow`
