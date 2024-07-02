from urllib.parse import urlparse
import requests
import xml.etree.ElementTree as ET
import csv
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import spacy
import re
import aiohttp
import asyncio

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
nlp = spacy.load("ru_core_news_sm")


class LinkData(BaseModel):
  link_url: str
  return_url: str = ""
  preset_id: str = ""


def remove_unwanted_tags(description):
  if description:
    description = re.sub(r'<[^>]+>', '', description)
    description = description.replace('•', '')
    description = re.sub(r'\s*<br>\s*', '\n', description, flags=re.IGNORECASE)
    description = re.sub(r'(\n\s*)+', '\n', description)
    description = f'<p>{description.strip()}</p>'.replace('\n', '<br>')
  else:
    description = ''
  return description


async def fetch_url(link_url):
  async with aiohttp.ClientSession() as session:
    async with session.get(link_url) as response:
      response.raise_for_status()
      return await response.text()


async def process_offer(offer_elem, build_category_path):
  offer_id = offer_elem.get('id', '0')
  offer_data = {'id': offer_id}
  category_id = offer_elem.find('.//categoryId').text
  category_path = build_category_path(category_id)
  offer_data['category_path'] = category_path

  for category_elem in offer_elem:
    if category_elem.tag not in ['picture', 'param']:
      category_name = category_elem.tag
      category_value = category_elem.text
      if category_value and category_value.replace('.', '', 1).isdigit():
        category_value = category_value.replace('.', ',')
      offer_data[category_name] = category_value

  picture_elems = offer_elem.findall('.//picture')
  pictures = "///".join(
      picture_elem.text
      for picture_elem in picture_elems) if picture_elems else ""
  if pictures:
    offer_data['pictures'] = pictures

  param_elems = offer_elem.findall('.//param')
  params = {
      param_elem.get('name'): param_elem.text
      for param_elem in param_elems
  } if param_elems else {}
  offer_data.update(params)

  if 'description' in offer_data and offer_data['description']:
    offer_data['description'] = remove_unwanted_tags(offer_data['description'])

  return offer_data


async def process_link(link_url):
  try:
    xml_data = await fetch_url(link_url)
    root = ET.fromstring(xml_data)

    categories = {}
    category_parents = {}
    for category in root.findall('.//category'):
      category_id = category.get('id')
      parent_id = category.get('parentId')
      categories[category_id] = category.text
      if parent_id:
        category_parents[category_id] = parent_id

    def build_category_path(category_id):
      path = []
      while category_id:
        path.append(categories.get(category_id, 'Undefined'))
        category_id = category_parents.get(category_id)
      return '///'.join(reversed(path))

    tasks = [
        process_offer(offer_elem, build_category_path)
        for offer_elem in root.findall('.//offer')
    ]
    data = await asyncio.gather(*tasks)

    save_path = "data_files"
    os.makedirs(save_path, exist_ok=True)
    domain_name = urlparse(link_url).netloc.replace("www.", "")
    safe_filename = domain_name.replace(".", "_")
    unique_filename = f"{safe_filename}.csv"
    file_path = os.path.join(save_path, unique_filename)

    category_names = set()
    for row in data:
      category_names.update(row.keys())

    with open(file_path, 'w', newline='', encoding='utf-8-sig') as file:
      writer = csv.DictWriter(file,
                              fieldnames=sorted(category_names),
                              delimiter=';')
      writer.writeheader()
      writer.writerows(data)

    print(f"Файл сохранен: {file_path}")
    return file_path
  except Exception as e:
    print(f"Произошла ошибка: {str(e)}")
    return None


@app.get("/")
def read_index(request: Request):
  return templates.TemplateResponse("index.html", {"request": request})


@app.post("/process_link")
async def process_link_post(link_data: LinkData):
  link_url = link_data.link_url
  preset_id = link_data.preset_id
  result = await process_link(link_url)
  if result:
    downloaded_file_name = os.path.basename(result)
    file_url = f"https://solarxml.replit.app/download/data_files/{downloaded_file_name}"

    print(f"Файл создан и доступен по URL: {file_url}")
    return {"file_url": file_url, "preset_id": preset_id}
  else:
    raise HTTPException(status_code=500,
                        detail="Во время обработки ссылки произошла ошибка")


@app.get("/download/data_files/{filename}")
async def download_csv(filename: str):
  file_path = os.path.join("data_files", filename)
  print(f"Попытка загрузки файла: {file_path}")
  if os.path.isfile(file_path):
    print("Файл найден, начинаю загрузку.")
    return FileResponse(path=file_path,
                        filename=filename,
                        media_type='application/octet-stream')
  else:
    print("Файл не найден.")
    raise HTTPException(status_code=404, detail="Файл не найден.")
