from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def eliminate_duplicates(tfidf_scores, threshold):
    num_docs = len(tfidf_scores)
    tfidf_matrix = np.array(list(tfidf_scores.values()))
    similarity_matrix = cosine_similarity(tfidf_matrix)
    to_remove = set()

    for i in range(num_docs):
        for j in range(i + 1, num_docs):
            if similarity_matrix[i][j] > threshold:
                to_remove.add(j)

    unique_docs = {doc_id: tfidf_scores[doc_id] for idx, doc_id in enumerate(tfidf_scores) if idx not in to_remove}
    return unique_docs

if __name__ == '__main__':
    tfidf_scores = {
        "doc_ID1": [0.1, 0.2, 0.3],
        "doc_ID2": [0.1, 0.2, 0.35],
        "doc_ID3": [0.15, 0.25, 0.3]
    }

    threshold = 0.9
    unique_docs = eliminate_duplicates(tfidf_scores, threshold)
    print("Unique documents:")
    for doc_id in unique_docs:
        print(doc_id)