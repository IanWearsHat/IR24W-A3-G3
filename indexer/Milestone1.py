import math
import os
import json
from nltk.stem import PorterStemmer
from bs4 import BeautifulSoup

"""
Making actual index:
    -dict where integer is mapped to a url
        Each document should be a different url, so just keep incrementing an integer and putting url to each
        Then json dump into a file

    -dict where stemmed token is the key, and a dict as the value
        - the dict in value has keys are document ID, values are lists
            - the list first has another list of the position of that term in the document
                - implicitly has the number of times the term occurs in the document (take len of lists of positions)
            - the second elem in the list is the tf score for the document
            - the third elem is the tf-idf score
                - when all files have been parsed, go through each term and calculate the idf score

    {
        "token": {
            docID: [
                [3, 4, 8, ... , position],
                term_frequency,
                tf_idf_score -----------------# calculated in update_tf_idf_scores
            ],
            docID2: [
                [other positions],
                term_frequency,
                tf_idf_score
            ]
        }
    }
"""


class Indexer:
    orig_dir = os.getcwd()

    stemmer = PorterStemmer()
    inv_index = dict()
    docID_map = dict()

    docID_count = 0

    def __init__(self, dir_name, index_file_name, docID_file_name):
        self._dir_name = dir_name
        self._index_file_name = index_file_name
        self._docID_file_name = docID_file_name

        self._total_doc_count = self.get_document_count()

    def _update_docID_map(self, url):
        self.docID_map[self.docID_count] = url

    def _update_inv_index(self, one_file_map):
        for token, posting in one_file_map.items():
            token_doc_dict = self.inv_index.setdefault(token, dict())
            posting_list = token_doc_dict.setdefault(self.docID_count, list())
            for elem in posting:
                posting_list.append(elem)

    def _update_tf_idf_scores(self):
        for posting_dict in self.inv_index.values():
            num_docs = len(posting_dict.values())
            idf_score = math.log(self._total_doc_count / num_docs)
            for posting_list in posting_dict.values():
                # posting_list[2] is initially the total number of words in the document
                tf_score = posting_list[1] / posting_list[2]
                tf_idf_score = tf_score * idf_score
                posting_list[2] = tf_idf_score

    def _get_one_file_token_freq(self, file_path):
        """
        Parse one file
        :param file_path: the input file path
        :return: the url, word frequency in the file
        """
        one_file_word_freq = {}
        with open(file_path, "r") as fr:
            file_content = json.load(fr)  # load json file
            url = file_content["url"]  # extract url
            content = file_content["content"]  # extract content
            text = BeautifulSoup(
                content, features="lxml"
            ).get_text()  # parse html contents

            # TODO: potential optimization: removing hyphens, periods, paranthese, etc.
            # keep in mind the complexities involved. ex. co-chair needs to be together and can't be split
            split_text = text.split()
            for i in range(len(split_text)):  # iterate the word in the text
                word = split_text[i]
                token = self.stemmer.stem(word)

                one_file_word_freq.setdefault(token, list())

                posting = one_file_word_freq[token]

                if len(posting) == 0:
                    posting.append(list())
                    posting.append(0)
                    # initially make posting[2] the number of words in the text
                    # This will be changed when update_tf_idf_scores is called
                    posting.append(len(split_text))

                posting[0].append(i)
                posting[1] += 1

        return url, one_file_word_freq

    def _write_dict_to_file(self, data_dict, file_name):
        """Writes a dict to a file as json"""
        json_data = json.dumps(data_dict, indent=None, separators=(",", ":"))
        with open("../" + file_name, "w") as json_writer:
            json_writer.write(json_data)

    def create_index(self) -> None:
        os.chdir(self._dir_name)

        for _dir in os.listdir():
            for file in os.listdir(_dir):
                file_path = os.path.join(_dir, file)

                url, one_file_map = self._get_one_file_token_freq(file_path)

                self._update_inv_index(one_file_map)
                self._update_docID_map(url)

                self.docID_count += 1

        self._update_tf_idf_scores()

        self._write_dict_to_file(self.inv_index, self._index_file_name)
        self._write_dict_to_file(self.docID_map, self._docID_file_name)

        os.chdir(self.orig_dir)

    def get_document_count(self) -> int:
        """Counts through all files in each subdirectory"""
        os.chdir(self._dir_name)

        counter = 0
        for _dir in os.listdir():
            for _ in os.listdir(_dir):
                counter += 1

        os.chdir(self.orig_dir)
        return counter


if __name__ == "__main__":
    is_test = True

    if is_test:
        directory = "TEST"
    else:
        directory = "DEV"

    indexer = Indexer(
        directory, directory + "_inv_index.json", directory + "_doc_ID_map.json"
    )
    indexer.create_index()
    print("Document Count:", indexer.get_document_count())
