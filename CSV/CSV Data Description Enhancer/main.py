import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import chardet


def detect_encoding(file_path):
  with open(file_path, 'rb') as f:
    result = chardet.detect(f.read())
    return result['encoding']


kaminopt_encoding = detect_encoding('kaminopt.csv')
features_encoding = detect_encoding('features.csv')

kaminopt_df = pd.read_csv('kaminopt.csv',
                          delimiter=';',
                          encoding=kaminopt_encoding,
                          low_memory=False)
features_df = pd.read_csv('features.csv',
                          delimiter=';',
                          encoding=features_encoding)

columns_to_exclude = features_df.iloc[:, 0].tolist()
columns_to_include = [
    col for col in kaminopt_df.columns if col not in columns_to_exclude
]

kaminopt_df.fillna('', inplace=True)


def combine_columns(dataframe, columns):

  def safe_join(row):
    html_items = []
    for col in columns:
      value = row[col]
      if pd.notna(value) and value != '':
        html_item = f'<li><span>{col}:</span><span>{value}</span></li>'
        html_items.append(html_item)
    return '\n'.join(html_items)

  dataframe['description'] = dataframe[columns].apply(safe_join, axis=1)


combine_columns(kaminopt_df, columns_to_include)

vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(kaminopt_df['description'])

valid_columns_to_exclude = [
    col for col in columns_to_exclude if col in kaminopt_df.columns
]

result_df = kaminopt_df[['description'] + valid_columns_to_exclude]
result_df.to_csv('kaminopt_modified.csv',
                 sep=';',
                 encoding=kaminopt_encoding,
                 index=False)

print("Файл успешно изменен и сохранен под именем 'kaminopt_modified.csv'")
