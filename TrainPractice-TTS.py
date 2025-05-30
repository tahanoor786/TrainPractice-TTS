import os
import sys
import PyPDF2
import pyttsx3
from pathlib import Path
import re
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
import time
from tqdm import tqdm  # For progress bars


class MultilingualPDFToAudioConverter:
    def __init__(self, speech_rate=150):
        self.engine = pyttsx3.init()
        self.speech_rate = speech_rate
        self.available_voices = self.get_available_voices()
        self.setup_basic_properties()
        self.conversion_start_time = None

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
            print("\nAvailable voices by language:")
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
                return 'english'  # Default to English

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
                print(f"\nUsing {language} voice: {selected_voice['name']}")
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

                print(f"\nProcessing {total_pages} pages...")
                page_progress = tqdm(pdf_reader.pages, desc="Extracting text", unit="page")

                for page in page_progress:
                    page_text = page.extract_text()
                    text += page_text + "\n\n"

                print("✅ Text extraction completed!")
                return text

        except Exception as e:
            print(f"❌ Error reading PDF: {e}")
            return None

    def clean_text(self, text, language='english'):
        if not text:
            return ""

        print("\nCleaning text...")
        start_time = time.time()

        # Remove excessive whitespace and newlines
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'\s+', ' ', text)

        # Remove page numbers and headers/footers (basic cleanup)
        lines = text.split('\n')
        cleaned_lines = []

        for line in tqdm(lines, desc="Processing lines", unit="line"):
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
        else:
            # English character replacements
            cleaned_text = cleaned_text.replace('•', 'bullet point')
            cleaned_text = cleaned_text.replace('→', 'arrow')
            cleaned_text = cleaned_text.replace('—', ' - ')

        elapsed = time.time() - start_time
        print(f"✅ Text cleaning completed in {elapsed:.2f} seconds")
        print(f"🔠 Final text length: {len(cleaned_text)} characters")

        return cleaned_text

    def text_to_audio(self, text, output_path, language):
        """Convert text to audio using appropriate voice"""
        try:
            if not text.strip():
                print("❌ No text to convert!")
                return False

            print(f"\nConverting {language} text to audio...")
            print(f"🎧 Output file: {output_path}")

            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Set up voice for the language
            self.setup_voice_for_language(language)

            # Convert text to speech and save
            print("⏳ Starting audio conversion...")
            self.conversion_start_time = time.time()

            # Create a progress bar for the conversion process
            with tqdm(total=len(text), desc="Converting to audio", unit="char") as pbar:
                def update_progress(_, __, ___, chars):
                    pbar.update(chars)

                self.engine.connect('started-utterance', lambda: pbar.reset())
                self.engine.connect('started-word', update_progress)

                self.engine.save_to_file(text, output_path)
                self.engine.runAndWait()

            conversion_time = time.time() - self.conversion_start_time
            print(f"✅ Audio conversion completed in {conversion_time:.2f} seconds!")
            return True

        except Exception as e:
            print(f"❌ Error during audio conversion: {e}")
            return False

    def convert_pdf_to_audio(self, pdf_path, audio_format='mp3', clean_text_flag=True):
        """
        Convert a single PDF to audio with automatic language detection
        Output format: [filename]_output.mp3
        """
        # Start tracking total processing time
        start_time = time.time()

        print(f"\n{'=' * 50}")
        print(f"📂 Processing file: {os.path.basename(pdf_path)}")
        print(f"🔧 Full path: {pdf_path}")
        print(f"{'=' * 50}")

        # Validate input file
        if not os.path.exists(pdf_path):
            print(f"❌ Error: PDF file not found: {pdf_path}")
            # Additional debugging
            print(f"🔧 File exists check: {os.path.exists(pdf_path)}")
            print(f"🔧 Is absolute path: {os.path.isabs(pdf_path)}")
            return False, None

        # Extract text from PDF
        text = self.extract_text_from_pdf(pdf_path)

        if not text:
            print("❌ Failed to extract text from PDF")
            return False, None

        # Detect language automatically
        language = self.detect_language(text)
        print(f"\n🔤 Detected language: {language}")

        # Generate output path with _output suffix
        pdf_name = Path(pdf_path).stem
        output_path = f"{pdf_name}_output.{audio_format}"

        # Clean text if requested
        if clean_text_flag:
            text = self.clean_text(text, language)

        # Convert to audio
        success = self.text_to_audio(text, output_path, language)

        if success:
            file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            total_time = time.time() - start_time

            print(f"\n{'=' * 50}")
            print(f"🎉 Conversion completed successfully!")
            print(f"📁 Output file: {output_path}")
            print(f"📏 File size: {file_size:.2f} MB")
            print(f"⏱️ Total processing time: {total_time:.2f} seconds")
            print(f"🗣️ Language used: {language}")
            print(f"{'=' * 50}")

        return success, language

    def convert_pdf_to_audio_with_output(self, pdf_path, output_path, audio_format='mp3', clean_text_flag=True):
        """
        Convert a single PDF to audio with automatic language detection
        Uses specified output path
        """
        # Start tracking total processing time
        start_time = time.time()

        print(f"\n{'=' * 50}")
        print(f"📂 Processing file: {os.path.basename(pdf_path)}")
        print(f"🔧 Full path: {pdf_path}")
        print(f"🎧 Output path: {output_path}")
        print(f"{'=' * 50}")

        # Validate input file
        if not os.path.exists(pdf_path):
            print(f"❌ Error: PDF file not found: {pdf_path}")
            # Additional debugging
            print(f"🔧 File exists check: {os.path.exists(pdf_path)}")
            print(f"🔧 Is absolute path: {os.path.isabs(pdf_path)}")
            return False, None

        # Extract text from PDF
        text = self.extract_text_from_pdf(pdf_path)

        if not text:
            print("❌ Failed to extract text from PDF")
            return False, None

        # Detect language automatically
        language = self.detect_language(text)
        print(f"\n🔤 Detected language: {language}")

        # Clean text if requested
        if clean_text_flag:
            text = self.clean_text(text, language)

        # Convert to audio
        success = self.text_to_audio(text, output_path, language)

        if success:
            file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            total_time = time.time() - start_time

            print(f"\n{'=' * 50}")
            print(f"🎉 Conversion completed successfully!")
            print(f"📁 Output file: {output_path}")
            print(f"📏 File size: {file_size:.2f} MB")
            print(f"⏱️ Total processing time: {total_time:.2f} seconds")
            print(f"🗣️ Language used: {language}")
            print(f"{'=' * 50}")

        return success, language


def process_folder(input_folder, output_folder=None, audio_format='mp3', speech_rate=150, clean_text=True):
    """
    Process all PDF files in a folder and convert them to audio files
    Automatically detects language for each PDF and uses appropriate voice
    """
    # Debug information
    current_dir = os.getcwd()
    print(f"🔧 Current working directory: {current_dir}")
    print(f"🔧 Looking for input folder: {os.path.abspath(input_folder)}")

    # List contents of current directory
    try:
        current_contents = os.listdir(current_dir)
        print(f"🔧 Contents of current directory: {current_contents}")
    except Exception as e:
        print(f"🔧 Could not list current directory: {e}")

    if not os.path.isdir(input_folder):
        print(f"❌ Error: Input folder not found: {input_folder}")
        print(f"📁 Please ensure the '{input_folder}' folder exists in: {current_dir}")
        return False

    if output_folder is None:
        output_folder = input_folder
    else:
        os.makedirs(output_folder, exist_ok=True)

    converter = MultilingualPDFToAudioConverter(speech_rate=speech_rate)

    # Get all PDF files in the input folder
    pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.pdf')]

    if not pdf_files:
        print(f"❌ No PDF files found in: {input_folder}")
        # List what files are actually in the input folder
        try:
            all_files = os.listdir(input_folder)
            print(f"🔧 Files found in input folder: {all_files}")
        except Exception as e:
            print(f"🔧 Could not list input folder contents: {e}")
        return False

    print(f"\n📂 Found {len(pdf_files)} PDF files to process: {pdf_files}")
    print(f"🎯 Output folder: {output_folder}")
    print(f"🔊 Audio format: {audio_format}")
    print(f"🗣️ Speech rate: {speech_rate} wpm")
    print(f"🔄 Language detection: Automatic")
    print(f"{'=' * 50}")

    success_count = 0
    english_count = 0
    russian_count = 0
    file_progress = tqdm(pdf_files, desc="Processing files", unit="file")

    for pdf_file in file_progress:
        file_progress.set_postfix(file=pdf_file[:15] + "...")
        pdf_path = os.path.join(input_folder, pdf_file)

        # Create full output path
        pdf_name = Path(pdf_file).stem
        output_file = f"{pdf_name}_output.{audio_format}"
        full_output_path = os.path.join(output_folder, output_file)

        try:
            # Debug: print the full path being passed
            print(f"🔧 Full PDF path: {pdf_path}")
            print(f"🔧 Output will be: {full_output_path}")

            # Pass the full output path to the converter
            success, language = converter.convert_pdf_to_audio_with_output(
                pdf_path=pdf_path,
                output_path=full_output_path,
                audio_format=audio_format,
                clean_text_flag=clean_text
            )

            if success:
                success_count += 1
                if language == 'english':
                    english_count += 1
                elif language == 'russian':
                    russian_count += 1
        except Exception as e:
            print(f"❌ Error processing {pdf_file}: {e}")

    print(f"\n{'=' * 50}")
    print(f"🎉 Processing complete!")
    print(f"✅ Successfully converted {success_count} of {len(pdf_files)} files")
    print(f"🇺🇸 English files: {english_count}")
    print(f"🇷🇺 Russian files: {russian_count}")
    print(f"📁 All output files saved in: {output_folder}")
    print(f"📝 Output format: [filename]_output.{audio_format}")
    print(f"{'=' * 50}")
    return success_count > 0


def main():
    # Configuration
    input_folder = 'input'  # Folder containing PDF files (relative path)
    output_folder = 'output'  # Where to save audio files (relative path)
    audio_format = "mp3"  # Audio format
    speech_rate = 150  # Words per minute
    clean_text = True  # Whether to clean the text

    print("🎙️ Multilingual PDF to Audio Converter")
    print("🔍 Automatic language detection enabled")
    print("🎯 Supported languages: English, Russian")
    print("📝 Output format: [filename]_output.mp3")

    # Process all PDFs in the folder
    process_folder(
        input_folder=input_folder,
        output_folder=output_folder,
        audio_format=audio_format,
        speech_rate=speech_rate,
        clean_text=clean_text
    )


if __name__ == "__main__":
    main()
