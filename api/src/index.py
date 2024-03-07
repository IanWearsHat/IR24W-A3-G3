from nltk.stem import PorterStemmer
import ijson
import json


class Index:
    def __init__(self, _index_path, _doc_id_map_path):
        self._index_path = _index_path
        self._doc_id_map_path = _doc_id_map_path

    def _get_term_doc_ids(self, term):
        stemmer = PorterStemmer()
        term = term.lower()
        term = stemmer.stem(term)
        doc_ids = set()

        with open(self._index_path, "rb") as f:
            parser = ijson.parse(f)
            # print(list(parser))

            started = False
            for prefix, event, value in parser:
                if (
                    prefix.startswith(term + ".") or prefix == term
                ) and event == "map_key":
                    print(prefix, event, value)
                    doc_ids.add(value)
                # if prefix.startswith(term):
                #     print(prefix, event, value)

                if prefix == term:
                    if started:
                        if event == "end_map":
                            break
                    else:
                        started = True

        return doc_ids

    def get_query_intersection(self, query_string):
        query_terms = query_string.lower().split()
        # stemmed_query_terms = [self.stemmer.stem(term) for term in query_terms]

        postings_lists = []
        for term in query_terms:
            docIDs = self._get_term_doc_ids(term)
            postings_lists.append(docIDs)

        common_doc_ids = set.intersection(*postings_lists) if postings_lists else set()

        return common_doc_ids

    def get_top_urls(self, doc_ids: set):
        urls = []
        with open(self._doc_id_map_path, "r") as f:
            d = json.load(f)
            for id in doc_ids:
                urls.append(d[id])
        return urls[:5]


if __name__ == "__main__":
    # index = Index("DEV_inv_index.json", "DEV_doc_ID_map.json")
    # input_str = input("Input a query: ")
    # while (input_str != "exit"):
    #     doc_ids = index.get_query_intersection(input_str)
    #     urls = index.get_top_urls(doc_ids)
    #     for url in urls[:5]:
    #         print(url)
    #     input_str = input("Input a query: ")
    
    for letter in ["a", "b", "c", "d"]:
        for i in range(10):
            if i > 3:
                continue
            print(i)
        print(letter)