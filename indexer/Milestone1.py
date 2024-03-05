from nltk.stem import PorterStemmer
from bs4 import BeautifulSoup
import numpy as np
import math
import os
import json
import re

"""
Making actual index:
    -dict where integer is mapped to a url
        Each document should be a different url, so just keep incrementing an integer and putting url to each
        Then json dump into a file

    -dict where stemmed token is the key, and a dict as the value
        - the dict in value has keys are document ID, values are lists
            - the list first has another list of the position of that term in the document
                - implicitly has the number of times the term occurs in the document (take len of lists of positions)
            - the second elem in the list is the number of docs token appears in
            - the third elem is the tf-idf score
                - when all files have been parsed, go through each term and calculate the idf score

    {
        "token": {
            docID: [
                [3, 4, 8, ... , position],
                number of docs token appears in,
                tf_idf_score -----------------# calculated in update_tf_idf_scores
            ],
            docID2: [
                [other positions],
                number of docs token appears in,
                tf_idf_score
            ]
        }
    }
"""
# TODO: text in bold, in headings, and in titles should be treated as more important

# TODO: IMPORTANT, MUST USE PARTIAL INDEX AT LEAST 3 TIMES, which are all merged in the end

# SEARCH ALSO CANNOT LOAD ALL INDEX INTO MAIN MEMORY


class Indexer:
    orig_dir = os.getcwd()

    stemmer = PorterStemmer()
    inv_index = dict()
    docID_map = dict()

    docID_count = 0
    index_count = 0

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

            # to find a specific url
            if url.strip() == "https://www.informatics.uci.edu/xmlrpc.php?rsd":
                print(file_path)
                print()

            text = BeautifulSoup(
                content, features="lxml"
            ).get_text()  # parse html contents

            text = re.sub(r"[\W_]+", " ", text)
            split_text = text.split()
            for i in range(len(split_text)):  # iterate the word in the text
                word = split_text[i].lower()

                one_file_word_freq.setdefault(word, list())

                posting = one_file_word_freq[word]

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

                if self.docID_count % 1000 == 0:
                    print(self.docID_count, url)

                self._update_inv_index(one_file_map)
                self._update_docID_map(url)

                self.docID_count += 1

                # dump current inv_index into json file and reset inv_index
                if self.docID_count % 30 == 0:
                    self._write_dict_to_file(self.inv_index, str(self.index_count) + ".json")
                    self.inv_index = {}
                    self.index_count += 1

        # self._update_tf_idf_scores()

        # one final partial index for anything left over
        self._write_dict_to_file(self.inv_index, str(self.index_count) + ".json")
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


def cosine_similarity(vec1, vec2):
    """
    Calculate the cosine similarity of two tf-idf score vector
    - vec1: this is a numpy array which means the first tf-idf score vector of one document
    - vec2: this is a numpy array which means the second tf-idf score vector of one document
    Returns:
    - cosine similarity as a float.
    For example:
    vec1 = np.array([1,2,3])
    vec2 = np.array([4,5,6])
    similarity = cosine_similarity(vec1, vec2)
    the docunment is the content in json after we run the M1 part code.
    """

    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    similarity = dot_product / (norm_vec1 * norm_vec2)
    return similarity


if __name__ == "__main__":
    is_test = True

    if is_test:
        directory = "ANALYST"
    else:
        directory = "DEV"

    indexer = Indexer(
        directory, directory + "_inv_index.json", directory + "_doc_ID_map.json"
    )
    import time

    past = time.time()

    indexer.create_index()
    # url, dic = indexer._get_one_file_token_freq("44a45c3cfd95b0299d3ac374bd3ec48a08d5402cdfda3d87cfb61ba55c37d74c.json")
    # print(dic)

    new = time.time()
    time_taken = new - past
    doc_count = indexer.get_document_count()
    print(time_taken, "seconds taken")
    print(time_taken / doc_count, "seconds per doc on average")
    print(doc_count, "documents parsed")

    # # Define a list of test queries
    # test_queries = [
    #     "cristina lopes",
    #     "machine learning",
    #     "ACM",
    #     "master of software engineering",
    # ]

    # # Process each query and print the results
    # for query in test_queries:
    #     print(f"Processing query: {query}")
    #     result_docs = indexer.process_query(query)
    #     print(f"Documents intersection found: {result_docs}\n")

    # TODO: does this need to be filtered out? http://computableplant.ics.uci.edu/models/Activator/WU-Activator-Update-2010/vertices.tsv
    # TODO: switch to pathlib instead
"""
Creating partial indexes:
- create a partial index file for every 30 documents

Merging:
- For each file, get a term and its posting dict
    - if the term is in the discovered set, move on to the next term

    - t1 = {
        0: {
            [3, 4, 5], the position of the term in the doc
            3,  # number of times the token appears in the doc
            9   # number of words in the doc
        },
        1: {
            [6, 7, 10], the position of the term in the doc
            3,  # number of times the token appears in the doc
            15   # number of words in the doc
        },
    }

- now for each file again except the current one and all ones previous to it, see if the term is in the file and get its posting, if not, continue to the next file
    - t2 = {
        3: {
            [3, 4, 5], the position of the term in the doc
            3,  # number of times the token appears in the doc
            9   # number of words in the doc
        },
        6: {
            [6, 7, 10], the position of the term in the doc
            3,  # number of times the token appears in the doc
            15   # number of words in the doc
        },
    }

- simply add all items from t2 into t1

- do this for every term for all files until we reach the end of the last file

- add t1 to discovered set.

- note that for each nested loop to find t2, you only need to look for every file onwards. 
    - ex. partial indexes 5, 4, 3, 2, 1
        if we are looking at 4 and t1 is in 4, we only need to look at 3, 2, 1

- _update_tf_idf_scores() will need to be run on each file after creating the inv index initially
        
- somehow have indexes for the indexes
    - like knowing that 1.json has terms from a-c, although everything is alphanumeric so idk
"""
