import numpy as np


def calculate_link_matrix(doc_dict):
    num_docs = len(doc_dict)
    link_matrix = np.zeros((num_docs, num_docs))
    for i, doc1_id in enumerate(doc_dict.keys()):
        for j, doc2_id in enumerate(doc_dict.keys()):
            if doc2_id in doc_dict[doc1_id]:  # Assuming the values in doc_dict represent linked document IDs
                link_matrix[j][i] = 1  # Set the corresponding link in the matrix
    return link_matrix


def page_rank(doc_dict, damping_factor=0.85, iterations=100):
    num_docs = len(doc_dict)
    link_matrix = calculate_link_matrix(doc_dict)
    tfidf_matrix = np.array(list(doc_dict.values())).T  # Transpose the values of doc_dict to get TF-IDF matrix
    page_rank = np.ones((num_docs, 1))

    for _ in range(iterations):
        new_page_rank = np.zeros_like(page_rank)
        for j in range(num_docs):
            for k in range(num_docs):
                if link_matrix[k][j] == 1:
                    new_page_rank[j] += (1 / np.sum(link_matrix[k])) * page_rank[k]
        page_rank = damping_factor * new_page_rank + (1 - damping_factor) * tfidf_matrix.dot(page_rank)

    return page_rank


# Supposing that the three docs are linked
doc_dict = {
    "doc_ID1": [0.1, 0.2, 0.3],
    "doc_ID2": [0.1, 0.2, 0.35],
    "doc_ID3": [0.15, 0.34, 0.13],
}

result = page_rank(doc_dict)
print("Final PageRank values:")
print(result)
