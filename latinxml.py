from googletrans import Translator
from lxml import etree

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

def translate_xml(input_file, output_file):
    """Translate text inside an XML file while preserving the structure."""
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(input_file, parser)
    root = tree.getroot()

    # Recursively translate text in elements
    def recursive_translate(element):
        if element.text and element.text.strip():
            element.text = translate_to_latin(element.text.strip())
        for child in element:
            recursive_translate(child)

    recursive_translate(root)

    # Save translated XML
    tree.write(output_file, encoding="utf-8", pretty_print=True, xml_declaration=True)
    print(f"Translated XML saved to: {output_file}")

# Example usage
input_xml = "input.xml"
output_xml = "translated_latin.xml"
translate_xml(input_xml, output_xml)
