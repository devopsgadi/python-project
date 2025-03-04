from googletrans import Translator
from lxml import etree

def translate_text(text, target_lang="es"):
    """Translate text using Google Translate."""
    translator = Translator()
    return translator.translate(text, dest=target_lang).text

def translate_xml(input_file, output_file, target_lang="es"):
    """Translate text inside an XML file while preserving the structure."""
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(input_file, parser)
    root = tree.getroot()

    # Recursively translate text in elements
    def recursive_translate(element):
        if element.text and element.text.strip():
            element.text = translate_text(element.text.strip(), target_lang)
        for child in element:
            recursive_translate(child)

    recursive_translate(root)

    # Save translated XML
    tree.write(output_file, encoding="utf-8", pretty_print=True, xml_declaration=True)
    print(f"Translated XML saved to: {output_file}")

# Example usage
input_xml = "input.xml"
output_xml = "translated.xml"
translate_xml(input_xml, output_xml)
