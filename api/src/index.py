import ijson


class Index:
    def __init__(self, _index_path):
        self._index_path = _index_path
        
    
    def _get_term_doc_ids(self, term):
        doc_ids = set()

        with open(self._index_path, "rb") as f:
            parser = ijson.parse(f)
            # print(list(parser))

            started = False
            for prefix, event, value in parser:

                if (prefix.startswith(term + '.') or prefix == term) and event == "map_key":
                    # print(prefix, event, value)
                    doc_ids.add(value)
                
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


if __name__ == "__main__":
    index = Index("DEV_inv_index.json")
    print(index.get_query_intersection("cert seed"))
    # print(index._get_term_doc_ids("ACM"))
    # issue: ACM returns nothing