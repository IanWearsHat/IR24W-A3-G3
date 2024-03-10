from nltk.stem import PorterStemmer
import pathlib
import orjson

from ranker import calculate_scores


class Index:
    """Represents the entire inverted index"""

    stemmer = PorterStemmer()
    posting_files = []
    positions_files = []

    master_token_map = None
    docID_to_file_map = None

    def __init__(self):
        self._open_index_files()

    def _open_index_files(self) -> None:
        """
        Opens all relevant index files, but does NOT load them all into memory

        Only loads token_to_index_num.json and docID_to_file.json as these are
        much smaller than the entire collection of postings.
        """
        index_num = 0
        index_path = pathlib.Path(f"../../index/{index_num}_merged.json")
        positions_path = pathlib.Path(f"../../index/{index_num}_merged_positions.json")
        while index_path.exists():
            postings_f = open(index_path, "rb")
            self.posting_files.append(postings_f)

            with open(positions_path, "rb") as f:
                positions_dict = orjson.loads(f.read())
            self.positions_files.append(positions_dict)

            index_num += 1
            index_path = pathlib.Path(f"../../index/{index_num}_merged.json")
            positions_path = pathlib.Path(
                f"../../index/{index_num}_merged_positions.json"
            )

        with open(pathlib.Path("../../index/token_to_index_num.json"), "rb") as f:
            self.master_token_map = orjson.loads(f.read())

        with open(pathlib.Path("../../index/docID_to_file.json"), "rb") as f:
            self.docID_to_file_map = orjson.loads(f.read())

    def close_index_files(self) -> None:
        for file in self.posting_files:
            file.close()

    def _get_posting(self, token) -> dict:
        """Gets a token's posting by only reading one line in index"""
        if token not in self.master_token_map:
            return dict()

        index_num = self.master_token_map[token]

        positions = self.positions_files[index_num]
        position_in_file = positions[token]

        index_file = self.posting_files[index_num]
        index_file.seek(position_in_file)

        line = index_file.readline()
        posting = orjson.loads(line)

        return posting

    def _is_key_in_all_postings(self, doc_id: int, postings: dict) -> bool:
        for posting in postings.values():
            if doc_id not in posting:
                return False

        return True

    def get_intersecting_postings(self, postings: dict) -> dict:
        """Returns postings, but only if the same docID appears for all tokens"""
        if len(postings) <= 1:
            return postings

        min_term = next(iter(postings))
        for posting in postings.values():
            if len(posting) < len(min_term):
                min_term = posting

        return_dict = {}
        for doc_id in postings[min_term].keys():
            if self._is_key_in_all_postings(doc_id, postings):
                for term in postings.keys():
                    inner_postings = return_dict.setdefault(term, dict())
                    inner_postings[doc_id] = postings[term][doc_id]

        return return_dict

    def get_postings_from_query(self, query_string: str) -> dict:
        """Splits a query string and gets the postings for each token"""
        query_terms = query_string.split()
        postings = {}
        for term in query_terms:
            term = self.stemmer.stem(term)

            posting = self._get_posting(term)
            postings[term] = posting

        return postings

    def get_doc_amount(self, postings: dict) -> int:
        """Gets the length of the union of all posting's docIDs"""
        all_docs = set()
        for posting in postings.values():
            all_docs.update(set(posting.keys()))

        return len(all_docs)

    def get_urls(self, doc_ids: list) -> list:
        """Reads from docID_to_file_map to get the mapped url"""
        urls = []
        for doc_id in doc_ids:
            urls.append(self.docID_to_file_map[doc_id][0])
        return urls
        # if using the filepath, add "indexer\\DEV\\" to the path


if __name__ == "__main__":
    import time

    index = Index()

    query = "html"

    past = time.time()

    postings = index.get_postings_from_query(query)
    intersecting = index.get_intersecting_postings(postings)
    num_docs = index.get_doc_amount(postings)

    scores = calculate_scores(query, postings, intersecting, num_docs)

    docs = [k for k in list(scores.keys())[-10:]]

    now = time.time()
    print(now - past, "seconds taken")

    index.close_index_files()

    # print(num_docs)
    # print(len(list(intersecting["acm"].keys())))
    print(scores)
    print(docs)

    # bad query probably uci bc it retrieves a lot more documents
