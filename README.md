README for Multilingual PDF to Audio Converter
Overview

This Python script converts PDF files to audio files (MP3 format) with automatic language detection (English and Russian supported). It uses text-to-speech synthesis with appropriate voices for each detected language.
Prerequisites

    Python 3.6 or higher - Download Python

    Required Python packages:

        PyPDF2

        pyttsx3

        langdetect

        tqdm

Installation

    Install Python if you haven't already

    Install required packages by running the following command in your terminal/command prompt:

bash

pip install PyPDF2 pyttsx3 langdetect tqdm

    Download the script (TrainPractice-TTS.py) and save it to your preferred directory

Setup

    Create an input folder in the same directory as the script

    Place your PDF files in the input folder

    (Optional) Create an output folder for the audio files (if not created, one will be made automatically)

Usage
Basic Usage

    Open a terminal/command prompt in the directory containing the script

    Run the script with:

bash

python TrainPractice-TTS.py

Custom Options

You can modify these settings in the main() function of the script:

    input_folder: Change the input folder name (default: 'input')

    output_folder: Change the output folder name (default: 'output')

    audio_format: Change output format (default: 'mp3')

    speech_rate: Adjust speaking rate in words per minute (default: 150)

    clean_text: Enable/disable text cleaning (default: True)

Expected Output

    The script will process all PDF files in the input folder

    For each PDF, it will:

        Extract text

        Detect language

        Clean the text (if enabled)

        Convert to audio using an appropriate voice

    Output files will be named [original_filename]_output.mp3 and saved in the output folder

Troubleshooting

    No PDF files found:

        Ensure PDF files are in the input folder

        Check that files have .pdf extension (case insensitive)

    Text extraction issues:

        Some PDFs with scanned images won't work (requires OCR)

        Try with simpler PDFs first

    Voice not available:

        The script will use default voice if preferred language voice isn't found

        Install additional voices through your operating system's text-to-speech settings

    File not found errors:

        Use absolute paths if relative paths don't work

        Check current working directory matches script location

Notes

    The script currently supports English and Russian best

    Processing time depends on PDF length and system performance

    Output quality depends on installed text-to-speech voices

License

This script is provided as-is without warranty. Feel free to modify for your needs.
