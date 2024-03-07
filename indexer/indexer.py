from nltk.stem import PorterStemmer
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import numpy as np
import math
import pathlib
import shutil
import orjson
import warnings

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

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
            - the third elem is the number of words in doc

"Before merging/index creation"
Partial Index 0: "
    {docID: [[3, 4, 8, ... , position],number of docs token appears in,number of words in doc],docID2: [[other positions],number of docs token appears in,number of words in doc2]}
    {docID: [[3, 4, 8, ... , position],number of docs token appears in,number of words in doc],docID2: [[other positions],number of docs token appears in,number of words in doc2]}
    "
- each line corresponds to a token's posting
- posting format is shown at bottom

Partial Index 0 positions: {
    "token": 0,
    "token2": 153,
    etc.
}

- after getting a token's position and seeking to it, read the whole line
- json.loads the line and do the normal things with it

{
    docID: [
        [3, 4, 8, ... , position of token in doc],
        number of times in doc token appears,
        number of words in doc2
    ],
    docID2: [
        [other positions],
        number of times in doc token appears,
        number of words in doc2
    ]
}


"Merging"
- 
"""
# TODO: text in bold, in headings, and in titles should be treated as more important


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
    inv_index = dict()
    docID_map = dict()

    docID_count = 0
    index_count = 0

    positions_dicts = []
    posting_files = []

    def __init__(self, dir_name):
        self._dir_name = dir_name
        self._docID_file_name = "docID_to_URL.json"

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
        with open(file_path, "rb") as fr:
            file_content = orjson.loads(fr.read())  # load json file
            url = file_content["url"]  # extract url
            if (
                url.endswith(".tsv")
                or url.endswith(".xml")
                or url.endswith(".txt")
                or url.endswith(".pdf")
                or url.endswith(".svg")
                or url.endswith(".png")
                or url.endswith(".jpg")
            ):
                return None, None

            content = file_content["content"]  # extract content
            if not content.startswith("<!DOCTYPE html"):
                return None, None

            soup = BeautifulSoup(content, features="lxml")

            # gets set of all words found in important tags
            important_words = set()
            important_tags = ["h1", "h2", "h3", "b", "strong", "title"]
            for tag in soup.find_all(important_tags):
                important_words.update({word.lower() for word in alnum_iter(tag.text.strip())})

            text = soup.get_text()  # get all text from webpage

            num_words = 0
            iterator = alnum_iter(text)
            for i, word in enumerate(iterator):  # iterate the word in the text
                word = word.lower()

                one_file_word_freq.setdefault(word, list())

                posting = one_file_word_freq[word]

                if len(posting) == 0:
                    posting.append(list())
                    posting.append(0)
                    posting.append(0)

                    # word is marked important with a 1 as the 3rd element
                    if word in important_words:
                        posting.append(1)

                posting[0].append(i)
                posting[1] += 1

                num_words += 1

            # initially make posting[2] the number of words in the text
            # This will be changed when update_tf_idf_scores is called
            for posting in one_file_word_freq.values():
                posting[2] = num_words

        return url, one_file_word_freq

    def _write_partial_index_to_file(self, posting_dict, index_num):
        """Note: also opens files and does not close them as they will be used in merging.
        The files must be closed with the close_partial_index_files function"""
        positions = {}
        index_f = open(f"./index/{index_num}.json", "wb+")
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
        with open("./index/" + file_name, "wb") as json_writer:
            json_writer.write(json_data)

    def create_index(self) -> None:
        # if index directory exists, delete it and all its contents, then create the empty directory again
        index_dir = pathlib.Path("./index/")
        if index_dir.exists():
            shutil.rmtree(index_dir)
        index_dir.mkdir()

        pages_path = pathlib.Path("./indexer/" + self._dir_name)
        for _dir in pages_path.iterdir():
            for file in pathlib.Path(_dir).iterdir():
                file_path = pathlib.Path(file)

                if pathlib.Path(file_path).stat().st_size > 5000000:
                    continue

                url, one_file_map = self._get_one_file_token_freq(file_path)

                if url is None:
                    continue

                if self.docID_count % 200 == 0:
                    print(f"Parsing doc # {self.docID_count}: {url}")

                self._update_inv_index(one_file_map)
                self._update_docID_map(url)

                self.docID_count += 1

                # dump current inv_index into json file and reset inv_index
                if self.docID_count % 64 == 0:
                    self._write_partial_index_to_file(self.inv_index, self.index_count)
                    self.inv_index = {}
                    self.index_count += 1

        # one final partial index write for anything left over
        self._write_partial_index_to_file(self.inv_index, self.index_count)
        self._write_dict_to_file(self.docID_map, self._docID_file_name)

    def merge_indexes(self) -> None:
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
                if token_count % 2048 == 0:
                    w_positions = {}
                    with open(
                        f"./index/{final_index_num}_merged.json", "wb"
                    ) as final_index_f:
                        for token, posting in final_index.items():
                            pos = final_index_f.tell()
                            w_positions[token] = pos

                            to_write = orjson.dumps(
                                posting, option=orjson.OPT_APPEND_NEWLINE
                            )
                            final_index_f.write(to_write)

                    with open(
                        f"./index/{final_index_num}_merged_positions.json", "wb+"
                    ) as final_positions_f:
                        to_write = orjson.dumps(w_positions)
                        final_positions_f.write(to_write)

                    final_index_num += 1

                    final_index = {}

        positions = {}
        with open(f"./index/{final_index_num}_merged.json", "wb") as final_index_f:
            for token, posting in final_index.items():
                pos = final_index_f.tell()
                positions[token] = pos

                to_write = orjson.dumps(posting, option=orjson.OPT_APPEND_NEWLINE)
                final_index_f.write(to_write)

        with open(
            f"./index/{final_index_num}_merged_positions.json", "wb+"
        ) as final_positions_f:
            to_write = orjson.dumps(positions)
            final_positions_f.write(to_write)

        with open("./index/token_to_index_num.json", "wb") as f:
            to_write = orjson.dumps(final_token_map)
            f.write(to_write)

    def close_partial_index_files(self) -> None:
        for file in self.posting_files:
            file.close()

    def delete_unsorted_partial_indexes(self) -> None:
        for i in range(len(self.posting_files)):
            pathlib.Path(f"./index/{i}.json").unlink()

    def get_document_count(self) -> int:
        """Counts through all files in each subdirectory"""
        counter = 0
        pages_path = pathlib.Path("./indexer/" + self._dir_name)
        for _dir in pages_path.iterdir():
            for _ in pathlib.Path(_dir).iterdir():
                counter += 1

        return counter

    def get_documents_parsed(self) -> int:
        return self.docID_count


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


# TODO: adding extra credit to postings
def main():
    """Creates the whole index"""
    indexer = Indexer("ANALYST")

    indexer.create_index()
    indexer.merge_indexes()
    indexer.close_partial_index_files()
    indexer.delete_unsorted_partial_indexes()

    total_num_docs = indexer.get_document_count()
    num_parsed_docs = indexer.get_documents_parsed()

    print("-" * 100)
    print(f"Indexed {num_parsed_docs} docs out of total {total_num_docs}.")
    print(
        "The number of indexed documents is smaller because they've been filtered from the total corpus."
    )
    print("-" * 100)


if __name__ == "__main__":
    main()
