from bs4 import BeautifulSoup
from xml.etree import ElementTree as ET


def load_and_parse_with_bs(content):
  soup = BeautifulSoup(content, 'xml')
  cleaned_content = str(soup)
  tree = ET.ElementTree(ET.fromstring(cleaned_content))
  return tree


def load_and_extract_text_with_bs(file_path):
  with open(file_path, 'r', encoding='utf-8') as file:
    content = file.read()
  tree = load_and_parse_with_bs(content)
  root = tree.getroot()
  text = ET.tostring(root, encoding='utf8', method='text').decode('utf8')
  return root, text, content


def transfer_data(source_root, target_root):
  for src_elem in source_root.iter():
    for trg_elem in target_root.iter():
      if src_elem.tag == trg_elem.tag:
        if (src_elem.text and src_elem.text.strip()) or src_elem.attrib:
          trg_elem.text = src_elem.text
          trg_elem.attrib = src_elem.attrib
        break


def remove_empty_elements(element):
  for child in list(element):
    remove_empty_elements(child)
    if not (child.text
            and child.text.strip()) and not child.attrib and not list(child):
      element.remove(child)


def save_xml(tree, file_path):
  tree.write(file_path, encoding='utf-8', xml_declaration=True)


source_file = "PLNR_0000000083_20240620_100600_1.XML"
target_file = "PLNR_8118230675_20240624_124608_.XML"

source_root, _, _ = load_and_extract_text_with_bs(source_file)
target_root, _, _ = load_and_extract_text_with_bs(target_file)

transfer_data(source_root, target_root)

remove_empty_elements(target_root)

new_file_path = "updated_PLNR_0000000083_20240620_100600_1.XML"
save_xml(ET.ElementTree(target_root), new_file_path)
