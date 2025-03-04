from googletrans import Translator
import re

def translate_to_latin(text):
    """Translate text to Latin using Google Translate API."""
    translator = Translator()
    try:
        # Attempt to translate the text into Latin
        translated = translator.translate(text, src='en', dest='la')
        return translated.text
    except Exception as e:
        print(f"Error in translation: {e}")
        return text  # Return the original text if translation fails

def translate_strings_file(input_file, output_file):
    """Translate content inside a .strings file."""
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        translated_lines = []
        
        # Process each line to extract key-value pairs and translate values
        for line in lines:
            # Match key-value pairs (e.g., "KEY" = "Value";)
            match = re.match(r'^(.*?)(\s?=\s?)(.*?)(\s?;)?$', line.strip())
            if match:
                key = match.group(1).strip()  # Extract key
                value = match.group(3).strip()  # Extract value

                # Translate the value (text) to Latin
                translated_value = translate_to_latin(value)

                # Reconstruct the line with the translated value
                translated_lines.append(f'"{key}" = "{translated_value}";\n')
            else:
                # If no match, just add the line as is (for comments or non-translatable content)
                translated_lines.append(line)

        # Write the translated content back to the output file
        with open(output_file, 'w', encoding='utf-8') as file:
            file.writelines(translated_lines)
        
        print(f"Translated .strings file saved to: {output_file}")
    
    except Exception as e:
        print(f"Error processing the file: {e}")

# Example usage
input_strings = "input.strings"
output_strings = "translated_latin.strings"
translate_strings_file(input_strings, output_strings)
