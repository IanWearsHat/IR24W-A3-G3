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

import math


def initailize_scores(intersecting_postings):
    term = next(iter(intersecting_postings))

    scores = {}
    for docID in intersecting_postings[term]:
        scores[docID] = 0

    return scores


def add_tf_idf_scores(scores, postings, intersecting_postings, num_union_docs):
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

            scores[docID] += tf_idf


def add_importance_scores(scores, intersecting_postings):
    for docID in scores:
        for token in intersecting_postings:
            posting = intersecting_postings[token][docID]

            try:
                posting[3]
                scores[docID] += 10
            except:
                continue


def calculate_scores(postings, intersecting_postings, num_union_docs):
    scores = initailize_scores(intersecting_postings)

    add_tf_idf_scores(scores, postings, intersecting_postings, num_union_docs)
    add_importance_scores(scores, intersecting_postings)

    # adapted from https://stackoverflow.com/questions/613183/how-do-i-sort-a-dictionary-by-value
    scores = {
        k: v for k, v in sorted(scores.items(), key=lambda item: item[1], reverse=True)
    }
    return scores
