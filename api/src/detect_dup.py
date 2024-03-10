from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


# The input tfidf_scores must be {
#   doc1: [0.1, 0.2, ...], tf-idf score of doc1
#   doc2: [0.15, 0.12, ...], tf-idf score of doc2
#   ...
# }
def detect_duplicates(tfidf_scores, threshold):
    num_docs = len(tfidf_scores)
    duplicate_pairs = []
    tfidf_matrix = np.array(list(tfidf_scores.values()))
    similarity_matrix = cosine_similarity(tfidf_matrix)
    for i in range(num_docs):
        for j in range(i + 1, num_docs):
            if similarity_matrix[i][j] > threshold:
                duplicate_pairs.append((list(tfidf_scores.keys())[i], list(tfidf_scores.keys())[j]))

    return duplicate_pairs


tfidf_scores = {
    "doc_ID1": [0.1, 0.2, 0.3],
    "doc_ID2": [0.1, 0.2, 0.35],
    "doc_ID3": [0.15, 0.25, 0.3]
}

if __name__ == '__main__':
    threshold = 0.9
    duplicate_pairs = detect_duplicates(tfidf_scores, threshold)
    print("Duplicate pairs:")
    for pair in duplicate_pairs:
        print(pair)
# Duplicate pairs:
# ('doc_ID1', 'doc_ID2')
# ('doc_ID1', 'doc_ID3')
# ('doc_ID2', 'doc_ID3')
