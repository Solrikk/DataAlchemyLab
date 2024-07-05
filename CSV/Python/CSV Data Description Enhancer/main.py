import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import chardet
from tkinter import Tk, filedialog
import os


def detect_encoding(file_path):
  with open(file_path, 'rb') as f:
    result = chardet.detect(f.read())
    return result['encoding']


def select_file(title):
  root = Tk()
  root.withdraw()
  file_path = filedialog.askopenfilename(title=title,
                                         filetypes=[("CSV files", "*.csv")])
  root.destroy()
  return file_path


data_file_path = select_file('Select the main CSV file for processing')
features_file_path = select_file('Select the file with columns to exclude')

data_file_encoding = detect_encoding(data_file_path)
features_encoding = detect_encoding(features_file_path)

data_df = pd.read_csv(data_file_path,
                      delimiter=';',
                      encoding=data_file_encoding,
                      low_memory=False)
features_df = pd.read_csv(features_file_path,
                          delimiter=';',
                          encoding=features_encoding)

columns_to_exclude = features_df.iloc[:, 0].tolist()
columns_to_include = [
    col for col in data_df.columns
    if col not in columns_to_exclude and col != 'description'
]

data_df.fillna('', inplace=True)


def combine_columns(dataframe, columns):

  def safe_join(row):
    html_items = []
    for col in columns:
      value = row[col]
      if pd.notna(value) and value != '':
        html_item = f'<li><span>{col}:</span><span>{value}</span></li>'
        html_items.append(html_item)
    existing_description = row['description']
    new_description = existing_description + '\n' + '\n'.join(
        html_items) if existing_description else '\n'.join(html_items)
    return new_description

  dataframe['description'] = dataframe.apply(safe_join, axis=1)


combine_columns(data_df, columns_to_include)

vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(data_df['description'])

valid_columns_to_exclude = [
    col for col in columns_to_exclude if col in data_df.columns
]

result_df = data_df[['description'] + valid_columns_to_exclude]
base_name = os.path.splitext(os.path.basename(data_file_path))[0]
output_file_path = f"{base_name}_modified.csv"
result_df.to_csv(output_file_path, sep=';', encoding='utf-8-sig', index=False)

print(f"File successfully modified and saved as '{output_file_path}'")
