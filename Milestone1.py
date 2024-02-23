import os
import sys
import json
import warnings
from nltk.stem import PorterStemmer
from bs4 import BeautifulSoup


def handleOneFile(file_path):
    one_file_word_freq = {}
    with open(file_path, "r") as fr:
        file_content = json.load(fr)
        url = file_content["url"]
        content = file_content["content"]
        text = BeautifulSoup(content, 'html.parser').get_text()
        for word in text:
            token = porter_stemmer.stem(word)
            # set default value to 1 and this need be modified in the following milestones
            one_file_word_freq[token] = 1
    return url, one_file_word_freq, text


token_map_urls = {}
if __name__ == '__main__':
    warnings.filterwarnings("ignore")
    if len(sys.argv) != 2:
        print("Invalid argument\nRun Like: python Milestone1.py milestone1_out.json")
    else:
        output_file_name = sys.argv[1]
        porter_stemmer = PorterStemmer()
        os.chdir("DEV")
        counter = 0
        for _dir in os.listdir():
            for file in os.listdir(_dir):
                url, one_file_map, text = handleOneFile(os.path.join(_dir, file))
                counter += 1
                for key in one_file_map.keys():
                    token_map_urls.setdefault(key, []).append([url, 1.0])
        json_data = json.dumps(token_map_urls, indent=2, separators=(',', ': '))
        with open("../" + output_file_name, "w") as json_writer:
            json_writer.write(json_data)
        unique_token_counter = 0
        for token, urls in token_map_urls.items():
            if len(urls) == 1:
                unique_token_counter += 1
        print(f"The number of indexed documents: {counter}")
        print(f"The number of unique words: {unique_token_counter}")
