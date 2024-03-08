"""
{
    "token1": {
        0: [[1, 2, 3, 4], term-freq, num-terms-in-doc],
        2: [[1, 2, 3, 4], term-freq, num-terms-in-doc, is-important]
    },
    "token2": {
        0: [[1, 2, 3, 4], term-freq, num-terms-in-doc, is-important],
        2: [[1, 2, 3, 4], term-freq, num-terms-in-doc]
    },

    in terms of scoring, if there is an is-important flag, then add like 10 to the overall score
}
"""

from nltk.stem import PorterStemmer
import numpy as np
import math


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

    vec_product = norm_vec1 * norm_vec2

    # in case any product results in a zero vector
    if not np.any(vec_product):
        return 0

    similarity = dot_product / vec_product
    return similarity


def initialize_scores(intersecting_postings):
    if len(intersecting_postings) == 0:
        return {}

    term = next(iter(intersecting_postings))

    scores = {}
    for docID in intersecting_postings[term]:
        scores[docID] = 0

    return scores


def add_tf_idf_scores(query, scores, postings, intersecting_postings, num_union_docs):
    stemmer = PorterStemmer()
    query = query.split()
    query = [stemmer.stem(term) for term in query]

    query_vector = []
    # make query vector
    for token in query:
        # tf score
        freq = query.count(token)
        tf = 1 + math.log(freq)

        # idf score
        num_docs = len(postings[token])
        idf = math.log(num_union_docs / num_docs)

        # multiply tf and idf
        tf_idf = tf * idf
        query_vector.append(tf_idf)

    tf_idf_vectors = {}
    for docID in scores:
        for token in intersecting_postings:
            # tf score
            freq = intersecting_postings[token][docID][1]
            tf = 1 + math.log(freq)

            # idf score
            num_docs = len(postings[token])
            idf = math.log(num_union_docs / num_docs)

            # multiply tf and idf
            tf_idf = tf * idf

            vec = tf_idf_vectors.setdefault(docID, list())
            vec.append(tf_idf)

    for docID in tf_idf_vectors:
        angle = cosine_similarity(
            np.array(query_vector), np.array(tf_idf_vectors[docID])
        )
        scores[docID] += angle


def add_importance_scores(scores, intersecting_postings):
    for docID in scores:
        for token in intersecting_postings:
            posting = intersecting_postings[token][docID]

            try:
                posting[3]
                scores[docID] += 10
            except:
                continue


def calculate_scores(query, postings, intersecting_postings, num_union_docs):
    # TODO: probably need to normalize score if we add more
    scores = initialize_scores(intersecting_postings)

    add_tf_idf_scores(query, scores, postings, intersecting_postings, num_union_docs)
    add_importance_scores(scores, intersecting_postings)

    # adapted from https://stackoverflow.com/questions/613183/how-do-i-sort-a-dictionary-by-value
    # sorting works because dictionaries remember insertion order
    scores = {k: v for k, v in sorted(scores.items(), key=lambda item: item[1])}
    return scores


# left off on 1. returning the urls to the frontend. 2. adding extra credit score calculations

if __name__ == "__main__":
    vec1 = np.array([0, 1])
    vec2 = np.array([0, -1])
    similarity = cosine_similarity(vec1, vec2)
    print(similarity)
