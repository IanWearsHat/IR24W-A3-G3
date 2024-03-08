import pathlib
from nltk.stem import PorterStemmer
import orjson

from ranker import calculate_scores


class Index:
    stemmer = PorterStemmer()
    posting_files = []
    positions_files = []

    master_token_map = None
    docID_to_file_map = None

    def __init__(self):
        self._open_index_files()

    def _open_index_files(self):
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

    def _get_posting(self, query):
        if query not in self.master_token_map:
            return dict()

        index_num = self.master_token_map[query]

        positions = self.positions_files[index_num]
        position_in_file = positions[query]

        index_file = self.posting_files[index_num]
        index_file.seek(position_in_file)

        line = index_file.readline()
        posting = orjson.loads(line)

        return posting
    
    def _key_in_all_postings(self, doc_id: int, postings: dict):
        for posting in postings.values():
            if doc_id not in posting:
                return False
            
        return True

    def _get_intersecting_postings(self, postings: dict):
        if len(postings) <= 1:
            return postings

        min_term = next(iter(postings))
        for posting in postings.values():
            if len(posting) < len(min_term):
                min_term = posting

        return_dict = {}
        for doc_id in postings[min_term].keys():
            if self._key_in_all_postings(doc_id, postings):
                for term in postings.keys():
                    inner_postings = return_dict.setdefault(term, dict())
                    inner_postings[doc_id] = postings[term][doc_id]
        
        return return_dict

    def get_postings_from_query(self, query_string: str):
        query_terms = query_string.split()
        postings = {}
        for term in query_terms:
            term = self.stemmer.stem(term)

            posting = self._get_posting(term)
            postings[term] = posting
        
        return postings

    def get_doc_amount(self, postings):
        all_docs = set()
        for posting in postings.values():
            all_docs.update(set(posting.keys()))

        return len(all_docs)

    def get_urls(self, doc_ids):
        urls = []
        i = 0
        for doc_id in doc_ids:
            if i == 10:
                break
            path = pathlib.Path(f"..\\..\\{self.docID_to_file_map[doc_id]}")
            with open(path, "rb") as f:
                content = orjson.loads(f.read())
                urls.append(content["url"])
            i += 1
            # print(len(content["content"]))
        return urls


if __name__ == "__main__":
    import time

    index = Index()

    query = "artifici ahmed"


    past = time.time()

    postings = index.get_postings_from_query(query)
    intersecting = index._get_intersecting_postings(postings)
    num_docs = index.get_doc_amount(postings)

    scores = calculate_scores(postings, intersecting, num_docs)

    docs = []
    i = 0
    for docID in scores:
        if i == 10:
            break
        docs.append(docID)
        i += 1

    now = time.time()
    print(now - past, "seconds taken")

    index.close_index_files()

    # print(num_docs)
    # print(len(list(intersecting["acm"].keys())))
    print(scores)
    print(docs)

    

    # bad query probably uci bc it retrieves a lot more documents
