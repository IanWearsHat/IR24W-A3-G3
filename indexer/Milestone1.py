from nltk.stem import PorterStemmer
from bs4 import BeautifulSoup
import numpy as np
import math
import os
import pathlib
import shutil
import json
import orjson
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

"Before merging/index creation"
Partial Index 0: "
    {docID: [[3, 4, 8, ... , position],number of docs token appears in,tf_idf_score],docID2: [[other positions],number of docs token appears in,tf_idf_score]}
    {docID: [[3, 4, 8, ... , position],number of docs token appears in,tf_idf_score],docID2: [[other positions],number of docs token appears in,tf_idf_score]}
    "
- each line corresponds to a token's posting
- each posting is prettified at the bottom

Partial Index 0 positions: {
    "token": 0,
    "token2": 153,
    etc.
}

- after getting a token's position and seeking to it, read the whole line
- json.loads the line and do the normal things with it, hopefully making the thing faster


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

"Merging"

"""
# TODO: text in bold, in headings, and in titles should be treated as more important

# TODO: IMPORTANT, MUST USE PARTIAL INDEX AT LEAST 3 TIMES, which are all merged in the end

# SEARCH ALSO CANNOT LOAD ALL INDEX INTO MAIN MEMORY


def alnum_iter(input_string):
    current_sequence = ""
    for char in input_string:
        if char.isalnum():
            current_sequence += char
        elif current_sequence:
            yield current_sequence
            current_sequence = ""
    if current_sequence:
        yield current_sequence


class Indexer:
    orig_dir = os.getcwd()

    stemmer = PorterStemmer()
    inv_index = dict()
    docID_map = dict()

    docID_count = 0
    index_count = 0

    positions_dicts = []
    posting_files = []

    def __init__(self, dir_name, index_file_name, docID_file_name):
        self._dir_name = dir_name
        self._index_file_name = index_file_name
        self._docID_file_name = docID_file_name

        self._total_doc_count = self.get_document_count()

    def _update_docID_map(self, url):
        self.docID_map[str(self.docID_count)] = url

    def _update_inv_index(self, one_file_map):
        for token, posting in one_file_map.items():
            token_doc_dict = self.inv_index.setdefault(token, dict())
            posting_list = token_doc_dict.setdefault(str(self.docID_count), list())
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

            last_i = 0
            iterator = alnum_iter(text)
            for i, word in enumerate(iterator):  # iterate the word in the text
                word = word.lower()

                one_file_word_freq.setdefault(word, list())

                posting = one_file_word_freq[word]

                if len(posting) == 0:
                    posting.append(list())
                    posting.append(0)

                posting[0].append(i)
                posting[1] += 1

                last_i += 1

            # initially make posting[2] the number of words in the text
            # This will be changed when update_tf_idf_scores is called
            for posting in one_file_word_freq.values():
                posting.append(last_i)

        return url, one_file_word_freq

    def _write_partial_index_to_file(self, posting_dict, index_num):
        """Note: also opens files and does not close them as they will be used in merging.
        The files must be closed with the close_partial_index_files function"""
        positions = {}
        index_f = open(f"../index/{index_num}.json", "wb+")
        for token, posting in posting_dict.items():
            pos = index_f.tell()
            positions[token] = pos

            to_write = orjson.dumps(posting, option=orjson.OPT_APPEND_NEWLINE)
            index_f.write(to_write)

        self.positions_dicts.append(positions)
        self.posting_files.append(index_f)

    def _write_dict_to_file(self, data_dict, file_name):
        """Writes a dict to a file as json"""
        json_data = orjson.dumps(data_dict)
        with open("../index/" + file_name, "wb") as json_writer:
            json_writer.write(json_data)

    def create_index(self) -> None:
        os.chdir(self._dir_name)

        # if index directory exists, delete it and all its contents, then create the empty directory again
        index_dir = pathlib.Path("../index/")
        if index_dir.exists():
            shutil.rmtree(index_dir)
        index_dir.mkdir()

        for _dir in os.listdir():
            for file in os.listdir(_dir):
                file_path = os.path.join(_dir, file)

                url, one_file_map = self._get_one_file_token_freq(file_path)

                if self.docID_count % 200 == 0:
                    print(self.docID_count, url)

                self._update_inv_index(one_file_map)
                self._update_docID_map(url)

                self.docID_count += 1

                # dump current inv_index into json file and reset inv_index
                if self.docID_count % 30 == 0:
                    self._write_partial_index_to_file(self.inv_index, self.index_count)
                    self.inv_index = {}
                    self.index_count += 1
                    # os.chdir(self.orig_dir)
                    # return

        # self._update_tf_idf_scores()

        # one final partial index write for anything left over
        self._write_partial_index_to_file(self.inv_index, self.index_count)
        self._write_dict_to_file(self.docID_map, self._docID_file_name)

        os.chdir(self.orig_dir)

    def merge_indexes(self) -> None:
        os.chdir("index/")
        seen = set()

        final_index_num = 0
        final_token_map = {}
        final_index = {}

        token_count = 0
        for curr_index in range(len(self.positions_dicts)):
            positions = self.positions_dicts[curr_index]
            index_f = self.posting_files[curr_index]

            index_f.seek(0)

            for token in positions.keys():
                # if token has already been merged, skip the token
                if token in seen:
                    continue
                seen.add(token)

                token_pos = positions[token]

                index_f.seek(token_pos)

                line = index_f.readline()
                token_posting = orjson.loads(line)

                for next_index_num in range(curr_index + 1, len(self.positions_dicts)):
                    next_pos_dict = self.positions_dicts[next_index_num]
                    next_index_f = self.posting_files[next_index_num]

                    next_index_f.seek(0)

                    if token in next_pos_dict:
                        next_token_pos = next_pos_dict[token]

                        next_index_f.seek(next_token_pos)

                        line = next_index_f.readline()
                        next_token_posting = orjson.loads(line)

                        token_posting.update(next_token_posting)

                final_token_map[token] = final_index_num
                final_index.update({token: token_posting})

                token_count += 1
                if token_count % 512 == 0:
                    w_positions = {}
                    with open(f"{final_index_num}_merged.json", "wb") as final_index_f:
                        for token, posting in final_index.items():
                            pos = final_index_f.tell()
                            w_positions[token] = pos

                            to_write = orjson.dumps(
                                posting, option=orjson.OPT_APPEND_NEWLINE
                            )
                            final_index_f.write(to_write)

                    with open(
                        f"{final_index_num}_merged_positions.json", "wb+"
                    ) as final_positions_f:
                        to_write = orjson.dumps(w_positions)
                        final_positions_f.write(to_write)

                    final_index_num += 1

                    final_index = {}

        positions = {}
        with open(f"{final_index_num}_merged.json", "wb") as final_index_f:
            for token, posting in final_index.items():
                pos = final_index_f.tell()
                positions[token] = pos

                to_write = orjson.dumps(posting, option=orjson.OPT_APPEND_NEWLINE)
                final_index_f.write(to_write)

        with open(
            f"{final_index_num}_merged_positions.json", "wb+"
        ) as final_positions_f:
            to_write = orjson.dumps(positions)
            final_positions_f.write(to_write)

        with open("final_token_map.json", "wb") as f:
            to_write = orjson.dumps(final_token_map)
            f.write(to_write)

        os.chdir(self.orig_dir)

    def close_partial_index_files(self) -> None:
        for file in self.posting_files:
            file.close()

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

    def time_taken(callable):
        past = time.time()

        callable()

        new = time.time()
        time_taken = new - past

        return time_taken

    index_time = time_taken(indexer.create_index)
    merge_time = time_taken(indexer.merge_indexes)

    doc_count = indexer.get_document_count()
    print()
    print(index_time, "s to index")
    print(merge_time, "s to merge")
    print()
    print(index_time + merge_time, "s total")
    print((index_time + merge_time) / doc_count, "seconds per doc on average")
    print(doc_count, "documents parsed")

    def retrieve():
        query = "computable"
        with open("index/final_token_map.json", "rb") as token_f:
            tokens = orjson.loads(token_f.read())
            index_number = tokens[query]

        with open(f"index/{index_number}_merged_positions.json", "rb") as pos_f:
            positions = orjson.loads(pos_f.read())
            token_pos = positions[query]

        with open(f"index/{index_number}_merged.json", "rb") as index_f:
            index_f.seek(token_pos)

            line = index_f.readline()
            posting = orjson.loads(line)
            # print(posting)

    indexer.close_partial_index_files()

    retrieve_time = time_taken(retrieve)
    print()
    print(retrieve_time, "s to retrieve one word's posting")
    """
    Current time:

    1.2464182376861572 s to index
    7.046298503875732 s to merge

    8.29271674156189 s total
    0.08549192517074113 seconds per doc on average
    97 documents parsed

    0.03386831283569336 s to retrieve one word's posting

    ----

    101.7853627204895 s to index
    64.61580681800842 s to merge

    166.40116953849792 s total
    0.11444372045288716 seconds per doc on average
    1454 documents parsed
    """
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

    # TODO: Filter out xml and other non-html files http://computableplant.ics.uci.edu/models/Activator/WU-Activator-Update-2010/vertices.tsv
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

- _update_tf_idf_scores() will need to be run on each file after creating all partial inv indexes initially

- somehow have indexes for the indexes

"""
