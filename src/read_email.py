import re
import os
import glob
from datetime import datetime
from email import policy
from email.parser import BytesParser
from bs4 import BeautifulSoup, Comment
import pandas as pd

COLUMNS = ['Title', 'Source', 'Summary', 'Date', 'State', 'Website']

def extract_links_from_talkwalker(eml_file_path):
    with open(eml_file_path, 'rb') as file:
        # Parse the eml file
        msg = BytesParser(policy=policy.default).parse(file)
    html_content = msg.get_body(preferencelist=('plain', 'html')).get_content()
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the NEWS and TWITTER comments
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    news_index = None
    twitter_index = None

    for i, comment in enumerate(comments):
        if 'NEWS' in comment:
            news_index = i
        if 'TWITTER' in comment:
            twitter_index = i

    # Extract the content between NEWS and TWITTER
    if news_index and twitter_index:
        news_content = comments[news_index].find_next_sibling()
        elements = []
        while news_content and news_content != comments[twitter_index]:
            elements.append(news_content)
            news_content = news_content.find_next_sibling()

        # Prepare data for DataFrame
        data = []
        for element in elements:
            if element.name == 'tr':
                title = element.find('a').text if element.find('a') else None
                source = element.find('a')['href'] if element.find('a') else None
                summary = None
                date = None
                state = None
                website = None
                for td in element.find_all('td'):
                    date_state_website = td.text.strip().split(' | ')
                    if td.text.strip()[:3]=="..."  and  td.text.strip()[-3:]=="..." :
                        summary = td.text.strip()
                    elif len(date_state_website) == 3:
                        if len(date_state_website[0]) < 15:
                            date = datetime.strptime(date_state_website[0], '%d.%m.%y %H:%M')
                            state = date_state_website[1]
                            website = date_state_website[2]
                if title and "alerts.talkwalker.com" not in source and date:
                    data.append([title, source, summary, date, state, website])

        # Create DataFrame
        df = pd.DataFrame(data, columns=COLUMNS)
        return df
    return None

def remove_non_articles(df):
    #df = df.dropna(subset=['Title', 'Source', 'Summary'], how="all")
    #df = df[~df["Source"].str.contains()]
    #df = df[df["Title"]!="Delete Alert"]
    return df

def save_csv(df, output_csv_path):
    if os.path.exists(output_csv_path):
        df.to_csv(output_csv_path, mode='a', index=False, header=False)
    else:
        df.to_csv(output_csv_path, mode='w', index=False, header=True)

def extract_links_from_eml(eml_file_path):
    # Open the eml file in binary mode
    with open(eml_file_path, 'rb') as file:
        # Parse the eml file
        msg = BytesParser(policy=policy.default).parse(file)
    
    # Get the email body as a string
    body = msg.get_body(preferencelist=('plain', 'html')).get_content()
    
    # Define a regular expression pattern for URLs
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    
    # Find all URLs in the email body
    links = re.findall(url_pattern, body)
    
    return links

def main():# Call the function and print the extracted links
    output_file = "./output/alerts.csv"
    if os.path.exists(output_file):
        df = pd.read_csv(output_file)
    else:
        df = pd.DataFrame(columns=COLUMNS)
    input_folder = "./input"
    talkwalker_folder = os.path.join(input_folder, "talkwalker")
    print(talkwalker_folder)
    for eml_file_path in glob.glob(os.path.join(talkwalker_folder, "*")):
        print(eml_file_path)
        df_new = extract_links_from_talkwalker(eml_file_path)
        df_new = remove_non_articles(df_new)
        df = pd.concat([df, df_new], ignore_index=True)
        df = df.drop_duplicates()
    save_csv(df, "./output/alerts.csv")

    # TODO remove useless
    # TODO fix summary
    # TODO go into the website and check for the mention?? 

main()






