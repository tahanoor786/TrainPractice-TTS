import os
import sys
import PyPDF2
import pyttsx3
from pathlib import Path
import re
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException


class MultilingualPDFToAudioConverter:
    def __init__(self, speech_rate=150):
        self.engine = pyttsx3.init()
        self.speech_rate = speech_rate
        self.available_voices = self.get_available_voices()
        self.setup_basic_properties()

    def setup_basic_properties(self):
        """Set basic TTS properties"""
        try:
            self.engine.setProperty('rate', self.speech_rate)
            self.engine.setProperty('volume', 0.9)
        except Exception as e:
            print(f"Warning: Could not configure basic settings: {e}")

    def get_available_voices(self):

        voices = {}
        try:
            available_voices = self.engine.getProperty('voices')
            for i, voice in enumerate(available_voices):
                voice_info = {
                    'id': voice.id,
                    'name': voice.name,
                    'index': i
                }

                # Try to detect language from voice name/id
                voice_name_lower = voice.name.lower()
                voice_id_lower = voice.id.lower()

                if any(keyword in voice_name_lower for keyword in ['russian', 'ru', 'russia']):
                    if 'russian' not in voices:
                        voices['russian'] = []
                    voices['russian'].append(voice_info)
                elif any(keyword in voice_name_lower for keyword in
                         ['english', 'en', 'us', 'uk', 'american', 'british']):
                    if 'english' not in voices:
                        voices['english'] = []
                    voices['english'].append(voice_info)
                else:
                    # Check voice ID for language indicators
                    if any(keyword in voice_id_lower for keyword in ['ru', 'russian']):
                        if 'russian' not in voices:
                            voices['russian'] = []
                        voices['russian'].append(voice_info)
                    elif any(keyword in voice_id_lower for keyword in ['en', 'us', 'uk']):
                        if 'english' not in voices:
                            voices['english'] = []
                        voices['english'].append(voice_info)
                    else:
                        # Default category for other voices
                        if 'other' not in voices:
                            voices['other'] = []
                        voices['other'].append(voice_info)

            # Print available voices
            print("Available voices by language:")
            for lang, voice_list in voices.items():
                print(f"\n{lang.upper()} voices:")
                for voice in voice_list:
                    print(f"  - {voice['name']} (Index: {voice['index']})")

        except Exception as e:
            print(f"Error getting voices: {e}")
            voices = {'english': [{'id': None, 'name': 'Default', 'index': 0}]}

        return voices

    def detect_language(self, text):
        try:
            # Take a sample of text for detection (first 1000 characters)
            sample_text = text[:1000].strip()

            if not sample_text:
                return 'en'  # Default to English

            detected_lang = detect(sample_text)

            # Map detected language codes to our supported languages
            if detected_lang == 'ru':
                return 'russian'
            elif detected_lang in ['en', 'en-us', 'en-gb']:
                return 'english'
            else:
                print(f"Detected language: {detected_lang}, defaulting to English")
                return 'english'

        except LangDetectException as e:
            print(f"Language detection failed: {e}")
            print("Defaulting to English")
            return 'english'
        except Exception as e:
            print(f"Error during language detection: {e}")
            print("Defaulting to English")
            return 'english'

    def setup_voice_for_language(self, language):
        """Set up the appropriate voice for the detected language"""
        try:
            if language in self.available_voices and self.available_voices[language]:
                # Use the first available voice for the language
                selected_voice = self.available_voices[language][0]
                self.engine.setProperty('voice', selected_voice['id'])
                print(f"Using {language} voice: {selected_voice['name']}")
                return True
            else:
                print(f"No {language} voice found, using default voice")
                # Try to use default voice
                voices = self.engine.getProperty('voices')
                if voices:
                    self.engine.setProperty('voice', voices[0].id)
                return False
        except Exception as e:
            print(f"Error setting up voice for {language}: {e}")
            return False

    def extract_text_from_pdf(self, pdf_path):
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)

                print(f"Processing {total_pages} pages...")

                for page_num, page in enumerate(pdf_reader.pages, 1):
                    print(f"Extracting text from page {page_num}/{total_pages}")
                    page_text = page.extract_text()
                    text += page_text + "\n\n"

                print("Text extraction completed!")
                return text

        except Exception as e:
            print(f"Error reading PDF: {e}")
            return None

    def clean_text(self, text, language='english'):
        if not text:
            return ""

        # Remove excessive whitespace and newlines
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'\s+', ' ', text)

        # Remove page numbers and headers/footers (basic cleanup)
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            # Skip very short lines that might be page numbers or artifacts
            if len(line) < 3:
                continue
            # Skip lines that are just numbers (likely page numbers)
            if line.isdigit():
                continue
            cleaned_lines.append(line)

        cleaned_text = ' '.join(cleaned_lines)

        # Replace problematic characters based on language
        if language == 'russian':
            # Russian-specific character replacements
            cleaned_text = cleaned_text.replace('•', 'маркер')
            cleaned_text = cleaned_text.replace('→', 'стрелка')
            cleaned_text = cleaned_text.replace('—', ' - ')
            # Add more Russian-specific replacements as needed
        else:
            # English character replacements
            cleaned_text = cleaned_text.replace('•', 'bullet point')
            cleaned_text = cleaned_text.replace('→', 'arrow')
            cleaned_text = cleaned_text.replace('—', ' - ')

        return cleaned_text

    def text_to_audio(self, text, output_path, language):
        """Convert text to audio using appropriate voice"""
        try:
            if not text.strip():
                print("No text to convert!")
                return False

            print(f"Converting {language} text to audio...")
            print(f"Output file: {output_path}")

            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Set up voice for the language
            self.setup_voice_for_language(language)

            # Convert text to speech and save
            self.engine.save_to_file(text, output_path)
            self.engine.runAndWait()

            print("Audio conversion completed successfully!")
            return True

        except Exception as e:
            print(f"Error during audio conversion: {e}")
            return False

    def convert_pdf_to_audio(self, pdf_path, output_path=None, audio_format='mp3',
                             clean_text_flag=True, force_language=None):

        # Validate input file
        if not os.path.exists(pdf_path):
            print(f"Error: PDF file not found: {pdf_path}")
            return False

        # Extract text from PDF
        print("Extracting text from PDF...")
        text = self.extract_text_from_pdf(pdf_path)

        if not text:
            print("Failed to extract text from PDF")
            return False

        print(f"Extracted {len(text)} characters of text")

        # Detect language or use forced language
        if force_language:
            language = force_language
            print(f"Using forced language: {language}")
        else:
            print("Detecting language...")
            language = self.detect_language(text)
            print(f"Detected language: {language}")

        # Generate output path if not provided
        if not output_path:
            pdf_name = Path(pdf_path).stem
            output_path = f"{pdf_name}_{language}.{audio_format}"

        # Clean text if requested
        if clean_text_flag:
            print("Cleaning text...")
            text = self.clean_text(text, language)
            print(f"Cleaned text: {len(text)} characters")

        # Convert to audio
        success = self.text_to_audio(text, output_path, language)

        if success:
            file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            print(f"\nConversion completed successfully!")
            print(f"Output file: {output_path}")
            print(f"File size: {file_size:.2f} MB")
            print(f"Language: {language}")

        return success


def main():
    # Configuration
    pdf_path = '/Users/faking/Desktop/Final cut pro/Books/PublishedPaper (1).pdf' # Replace with your PDF path
    output_path = "/Users/faking/Desktop/Final cut pro/Sound-Output/audiobook.mp3"  # Replace with your desired output path
    audio_format = "mp3"  # "mp3" or "wav"
    speech_rate = 150  # Words per minute
    clean_text = True  # Whether to clean the text
    force_language = None  # Set to 'russian' or 'english' to force a language, None for auto-detection

    # Create converter instance
    converter = MultilingualPDFToAudioConverter(speech_rate=speech_rate)

    # Perform conversion
    success = converter.convert_pdf_to_audio(
        pdf_path=pdf_path,
        output_path=output_path,
        audio_format=audio_format,
        clean_text_flag=clean_text,
        force_language=force_language
    )

    if not success:
        print("Error in conversion process.")


if __name__ == "__main__":
    main()