"""
Postings structure:
{
    "token1": {
        0: [[1, 2, 3, 4], term-freq, num-terms-in-doc],
        2: [[1, 2, 3, 4], term-freq, num-terms-in-doc, is-important]
    },
    "token2": {
        0: [[1, 2, 3, 4], term-freq, num-terms-in-doc, is-important],
        2: [[1, 2, 3, 4], term-freq, num-terms-in-doc]
    },

    in terms of scoring, if there is an is-important flag, then add a large amount to the overall score
}
"""

from nltk.stem import PorterStemmer
import numpy as np
import math


def cosine_similarity(vec1, vec2):
    """
    Calculate the cosine similarity of two tf-idf score vector
    - vec1: numpy array containing the tf-idf score vector of one document
    - vec2: numpy array containing the tf-idf score vector of another document
    Returns:
    - cosine similarity as a float.

    Example usage:
        vec1 = np.array([1,2,3])
        vec2 = np.array([4,5,6])
        similarity = cosine_similarity(vec1, vec2)
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


def initialize_scores(intersecting_postings: dict) -> dict:
    """Initializes all docIDs to have a score of 0"""
    if len(intersecting_postings) == 0:
        return {}

    term = next(iter(intersecting_postings))

    scores = {}
    for docID in intersecting_postings[term]:
        scores[docID] = 0

    return scores


def _create_query_tf_idf_vector(
    query: list, postings: dict, num_union_docs: int
) -> list:
    query_vector = []
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

    return query_vector


def _create_tf_idf_vectors(
    scores: dict, postings: dict, intersecting_postings: dict, num_union_docs: int
) -> dict:
    """Creates tf-idf vectors for each doc"""
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

    return tf_idf_vectors


def _add_tf_idf_scores(
    query: str,
    scores: dict,
    postings: dict,
    intersecting_postings: dict,
    num_union_docs: int,
) -> None:
    """Adds tf-idf scores according to their cosine similarity to the query"""
    stemmer = PorterStemmer()
    query = query.split()
    query = [stemmer.stem(term) for term in query]

    query_vector = _create_query_tf_idf_vector(query, postings, num_union_docs)
    tf_idf_vectors = _create_tf_idf_vectors(
        scores, postings, intersecting_postings, num_union_docs
    )

    for docID in tf_idf_vectors:
        doc_vec = tf_idf_vectors[docID]
        angle = cosine_similarity(np.array(query_vector), np.array(doc_vec))
        scores[docID] += angle


def _add_importance_scores(scores: dict, intersecting_postings: dict) -> None:
    """Adds more score to docs that have an important token"""
    for docID in scores:
        for token in intersecting_postings:
            posting = intersecting_postings[token][docID]

            try:
                posting[3]
                scores[docID] += 10
            except:
                continue


def calculate_scores(
    query: str, postings: dict, intersecting_postings: dict, num_union_docs: int
) -> dict:
    """Calculates scores for all docIDs"""
    # TODO: probably need to normalize score if we add more
    scores = initialize_scores(intersecting_postings)

    _add_tf_idf_scores(query, scores, postings, intersecting_postings, num_union_docs)
    _add_importance_scores(scores, intersecting_postings)

    # adapted from https://stackoverflow.com/questions/613183/how-do-i-sort-a-dictionary-by-value
    # sorting works because dictionaries remember insertion order
    scores = {k: v for k, v in sorted(scores.items(), key=lambda item: item[1])}
    return scores
