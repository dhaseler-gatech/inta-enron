import os
import tarfile
import pandas as pd
import re

def extract_enron_dataset():
    unzipped_folder = 'Enron_dataset'
    zip_file = 'enron_mail_20150507.tar'

    if not os.path.exists(unzipped_folder):
        print(f"Folder '{unzipped_folder}' not found. Extracting '{zip_file}'.")
        if os.path.exists(zip_file):
            with tarfile.open(zip_file, 'r') as tar:
                os.makedirs(unzipped_folder, exist_ok=True)
                tar.extractall(path=unzipped_folder)
            print(f"Extraction done.")
        else:
            print(f"Error: zipfile '{zip_file}' not found")
    else:
        print(f"Folder '{unzipped_folder}' already exists. Skipping unzipping.")


def parse_email(content):
    headers = {
        'Message-ID': r'Message-ID:\s*(.*)',
        'Date': r'Date:\s*(.*)',
        'From': r'From:\s*(.*)',
        'To': r'To:\s*(.*)',
        'Subject': r'Subject:\s*(.*)',
        'Mime-Version': r'Mime-Version:\s*(.*)',
        'Content-Type': r'Content-Type:\s*(.*)',
        'Content-Transfer-Encoding': r'Content-Transfer-Encoding:\s*(.*)',
        'X-From': r'X-From:\s*(.*)',
        'X-To': r'X-To:\s*(.*)',
        'X-cc': r'X-cc:\s*(.*)',
        'X-bcc': r'X-bcc:\s*(.*)',
        'X-Folder': r'X-Folder:\s*(.*)',
        'X-Origin': r'X-Origin:\s*(.*)',
        'X-FileName': r'X-FileName:\s*(.*)'
    }
    extracted_data = {key: None for key in headers}

    for key, pattern in headers.items():
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            extracted_data[key] = match.group(1).strip()

    body_match = re.split(r'\n\n', content, maxsplit=1)
    extracted_data['Body'] = body_match[1].strip() if len(body_match) > 1 else None

    return extracted_data


def create_dataframe(document_type='all_documents'):
    dataset_folder = 'Enron_dataset'
    csv_file = f"{document_type}.csv"

    if os.path.exists(csv_file):
        print(f"Loading saved DataFrame from {csv_file} from last time!")
        return pd.read_csv(csv_file)
    print(f"Dataframe not made yet for  {document_type}, building now (will take a sec!)")

    data = []
    for root, dirs, files in os.walk(dataset_folder):
        if document_type in root:
            person_folder = os.path.basename(os.path.dirname(root))
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    email_data = parse_email(content)
                    email_data['Person'] = person_folder
                    data.append(email_data)
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")

    df = pd.DataFrame(data)
    df.to_csv(csv_file, index=False)
    print(f"Saved DataFrame to {csv_file}")
    return df

def filter_df_on_keyword(df, keyword, label='Body'):
    return df[df[label].str.contains(keyword, case=False, na=False)]

# extract dataset from zip if not previously done
extract_enron_dataset()
# create dataframes from extracted dataset if not already done
all_documents_df = create_dataframe(document_type='all_documents')
sent_items_df = create_dataframe(document_type='sent')
deleted_items_df = create_dataframe(document_type='deleted_items')

# filter on specific keywords/terms
emails_with_special_purpose_entities = filter_df_on_keyword(df=all_documents_df, keyword='special purpose entities')
emails_with_SPE = filter_df_on_keyword(df=all_documents_df, keyword=' SPE ')
emails_with_adjust_the_numbers = filter_df_on_keyword(df=all_documents_df, keyword='adjust the numbers')

# filter based on people
all_documents_df_skilling = filter_df_on_keyword(all_documents_df, keyword='skilling-j', label='Person')

print("Done")