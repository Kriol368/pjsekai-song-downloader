# Sekaipedia Song Downloader

This Python project scrapes the Sekaipedia website to fetch metadata and download songs along with their cover images. It also updates the song metadata, including title, singers, and album art.

## Features

- Scrape song metadata from [Sekaipedia](https://www.sekaipedia.org)
- Excludes songs added in a set number of days
- Download song cover images and audio files
- Update ID3 metadata for MP3 files, including title, singers, and album art

## Requirements

- Python 3.9+
- FFmpeg (required for audio processing)
    - Install via package manager (see Installation section)
- Libraries:
    - `beautifulsoup4==4.12.3`
    - `requests==2.32.3`
    - `mutagen==1.47.0`
    - `pillow==11.1.0`
    - `soupsieve==2.6` (required by `beautifulsoup4`)
    - `certifi==2024.12.14` (required by `requests`)
    - `charset-normalizer==3.4.1` (required by `requests`)
    - `idna==3.10` (required by `requests`)
    - `urllib3==2.3.0` (required by `requests`)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/sekaipedia-song-downloader.git
   cd sekaipedia-song-downloader
   ```

2. Install FFmpeg:

    - **Linux (Debian/Ubuntu)**:
      ```bash
      sudo apt install ffmpeg
      ```
    - **Mac (Homebrew)**:
      ```bash
      brew install ffmpeg
      ```
    - **Windows**:
        - Download from the [FFmpeg official site](https://ffmpeg.org/download.html).
        - Follow instructions to add FFmpeg to your system PATH.

3. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script using Python:
```bash
python script.py
```

The script will:
1. Fetch the list of songs from Sekaipedia.
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
- **FFmpeg Not Found:** Ensure FFmpeg is installed and accessible via the system PATH.

## Limitations

- The script is designed to scrape data only from Sekaipedia and may not work if the website's structure changes.
- Only MP3 files with valid audio sources are downloaded.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Data source: [Sekaipedia](https://www.sekaipedia.org)
- Libraries: `beautifulsoup4==4.12.3`, `requests==2.32.3`, `mutagen==1.47.0`, `pillow==11.1.0`, `soupsieve==2.6`, `certifi==2024.12.14`, `charset-normalizer==3.4.1`, `idna==3.10`, `urllib3==2.3.0`
- Audio processing tool: `FFmpeg`
