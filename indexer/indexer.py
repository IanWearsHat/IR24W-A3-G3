from nltk.stem import PorterStemmer
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
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
- posting format is shown here:
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

Partial Index 0 positions: {
    "token": 0,
    "token2": 153,
    etc.
}

- after getting a token's position and seeking to it, read the whole line
- this gets that token's posting
"""


def alnum_iter(input_string):
    """Generator that yields the next alphanumeric sequence in an input_string"""
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
    """
    For creating the index.

    From Assignment 3 spec for Algorithms and Data Structures Developer (pg 3):
        "Your index should be stored in one or more files in the file system (no databases!)."
    
    Thus, the index is comprised of multiple files.
    """

    stemmer = PorterStemmer()

    inv_index = dict()
    docID_map = dict()

    docID_count = 0
    index_count = 0

    positions_dicts = []
    posting_files = []

    def __init__(self, dir_name):
        self._dir_name = dir_name
        self._docID_file_name = "docID_to_file.json"

    def _update_docID_map(self, url: str, file_path: pathlib.Path) -> None:
        """Maps the current docID to its url and file_path"""
        self.docID_map[str(self.docID_count)] = (url, str(file_path.name))

    def _update_inv_index(self, one_file_map: dict) -> None:
        """
        Updates a token's posting in the inverted index given
        a token to posting mapping from one file.

        If the token does not exist in the inverted index,
        the token will be initialized with an empty dict
        and an empty list for its posting.
        """
        for token, posting in one_file_map.items():
            token_doc_dict = self.inv_index.setdefault(token, dict())
            posting_list = token_doc_dict.setdefault(str(self.docID_count), list())
            for elem in posting:
                posting_list.append(elem)

    def _get_one_file_token_freq(self, file_path: pathlib.Path) -> dict:
        """
        Parses one file for its alphanumeric tokens and their postings.
        Also marks whether or not a word is in an important tag like
        title or h1.

        If the webpage is not html, the function will return None.

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
            leading = content[:20].lower()
            if "html" not in leading:
                return None, None

            soup = BeautifulSoup(content, features="lxml")

            # gets set of all words found in important tags
            important_words = set()
            important_tags = ["h1", "h2", "h3", "b", "strong", "title"]
            for tag in soup.find_all(important_tags):
                important_words.update(
                    {self.stemmer.stem(word) for word in alnum_iter(tag.text.strip())}
                )

            text = soup.get_text()  # get all text from webpage

            tokens = [self.stemmer.stem(word) for word in alnum_iter(text)]

            num_words = 0
            iterator = alnum_iter(text)
            bigrams = [' '.join(tokens[i:i+2]) for i in range(len(tokens)-1)]
            trigrams = [' '.join(tokens[i:i+3]) for i in range(len(tokens)-2)]
            with open("bigrams_trigrams.txt", "a", encoding="utf-8") as bt_file:
                bt_file.write(f"Bigrams: {bigrams}\n")
                bt_file.write(f"Trigrams: {trigrams}\n")

            all_tokens = tokens + bigrams + trigrams
            for i, token in enumerate(all_tokens):  # iterate the word in the text
                token = self.stemmer.stem(token)

                one_file_word_freq.setdefault(token, list())

                posting = one_file_word_freq[token]


                if len(posting) == 0:
                    posting.append(list())
                    posting.append(0)
                    posting.append(0)

                    # word is marked important with a 1 as the 3rd element
                    if any(part in important_words for part in token.split()):
                        posting.append(1)
                    else:
                        posting.append(0)

                if i < len(tokens):  # Only count positions for unigrams
                    posting[0].append(i)
                posting[1] += 1

                num_words += 1

            for posting in one_file_word_freq.values():
                posting[2] = num_words

        return url, one_file_word_freq

    def _write_partial_index_to_file(self, posting_dict: dict, index_num: int) -> None:
        """
        Writes an entire index's postings to one file.
        Also writes the seek position of each token's posting to another file for
        future bookkeeping.

        Note: also opens files and does not close them as they will be used in merging.
        The files must be closed with the close_partial_index_files function
        """
        positions = {}
        index_f = open(f"./index/{index_num}.json", "wb+")
        for token, posting in posting_dict.items():
            pos = index_f.tell()
            positions[token] = pos

            to_write = orjson.dumps(posting, option=orjson.OPT_APPEND_NEWLINE)
            index_f.write(to_write)

        self.positions_dicts.append(positions)
        self.posting_files.append(index_f)

    def _write_dict_to_file(self, data_dict: dict, file_name: str) -> None:
        """Writes a dict to a file as json"""
        json_data = orjson.dumps(data_dict)
        with open("./index/" + file_name, "wb") as json_writer:
            json_writer.write(json_data)

    def create_index(self) -> None:
        """
        Creates all unmerged partial indexes by looking at entire corpus

        Will not open a file if its size is too big.
        """
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
                self._update_docID_map(url, file_path)

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
        """Merges all unmerged partial indexes."""
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

                # If a certain number of tokens reached, write to a merged partial index
                # and write postions to a merged positions index.
                # Then, clear final_index to free memory
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

        # Final write to file for any leftover postings
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

        # Create a mapping of tokens to their merged partial index for bookkeeping
        with open("./index/token_to_index_num.json", "wb") as f:
            to_write = orjson.dumps(final_token_map)
            f.write(to_write)

    def close_partial_index_files(self) -> None:
        """Closes all open files from _write_partial_index_to_file"""
        for file in self.posting_files:
            file.close()

    def delete_unsorted_partial_indexes(self) -> None:
        """Deletes all unmerged partial indexes. Should be called after merging."""
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
