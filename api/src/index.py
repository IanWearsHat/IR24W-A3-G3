import pathlib
from nltk.stem import PorterStemmer
import orjson

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
            positions_path = pathlib.Path(f"../../index/{index_num}_merged_positions.json")
        
        with open("../../index/token_to_index_num.json", "rb") as f:
            self.master_token_map = orjson.loads(f.read())
        
        with open("../../index/docID_to_URL.json", "rb") as f:
            self.docID_to_file_map = orjson.loads(f.read())

    def close_index_files(self) -> None:
        for file in self.posting_files:
            file.close()
    
    def _get_term_doc_ids(self, query):
        if query not in self.master_token_map:
            return set()

        index_num = self.master_token_map[query]

        positions = self.positions_files[index_num]
        position_in_file = positions[query]

        index_file = self.posting_files[index_num]
        index_file.seek(position_in_file)

        line = index_file.readline()
        posting = orjson.loads(line)

        return set(posting.keys())

    def get_query_intersection(self, query_string):
        query_terms = query_string.split()
        # stemmed_query_terms = [self.stemmer.stem(term) for term in query_terms]

        postings_lists = []
        for term in query_terms:
            term = self.stemmer.stem(term)

            docIDs = self._get_term_doc_ids(term)
            postings_lists.append(docIDs)

        common_doc_ids = set.intersection(*postings_lists) if postings_lists else set()

        return common_doc_ids

    def get_urls(self, doc_ids):
        urls = []
        for doc_id in doc_ids:
            url = self.docID_to_file_map[doc_id]
            urls.append(url)
        return urls


if __name__ == "__main__":
    # index = Index("DEV_inv_index.json", "DEV_doc_ID_map.json")
    # input_str = input("Input a query: ")
    # while (input_str != "exit"):
    #     doc_ids = index.get_query_intersection(input_str)
    #     urls = index.get_top_urls(doc_ids)
    #     for url in urls[:5]:
    #         print(url)
    #     input_str = input("Input a query: ")

    query = "machine learning"

    index = Index()
    doc_ids = index.get_query_intersection(query)
    urls = index.get_urls(doc_ids)
    index.close_index_files()

    print(urls)
