from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import string
import math
import sys
import os

FILE_MATCHES = 1
SENTENCE_MATCHES = 1
FILTER = set(stopwords.words("english")).union(string.punctuation)


def main():

    # Check command-line arguments
    if len(sys.argv) != 2:
        sys.exit("Usage: python questions.py corpus")

    # Calculate IDF values across files
    files = load_files(sys.argv[1])
    file_words = {
        filename: tokenize(files[filename])
        for filename in files
    }
    file_idfs = compute_idfs(file_words)

    while True:
        # Prompt user for query
        query = set(tokenize(input("Query: ")))

        # Determine top file matches according to TF-IDF
        filenames = top_files(query, file_words, file_idfs, n=FILE_MATCHES)

        # Extract sentences from top files
        sentences = dict()
        for filename in filenames:
            for passage in files[filename].split("\n"):
                for sentence in sent_tokenize(passage):
                    tokens = tokenize(sentence)
                    if tokens:
                        sentences[sentence] = tokens

        # Compute IDF values across sentences
        idfs = compute_idfs(sentences)

        # Determine top sentence matches
        matches = top_sentences(query, sentences, idfs, n=SENTENCE_MATCHES)
        for match in matches:
            print(match)


def load_files(directory):
    """
    Given a directory name, return a dictionary mapping the filename of each
    `.txt` file inside that directory to the file's contents as a string.
    """
    files = dict()
    for filename in os.listdir(directory):
        with open(os.path.join(directory, filename), "r") as f:
            files[filename] = f.read()
    return files


def tokenize(document):
    """
    Given a document (represented as a string), return a list of all of the
    words in that document, in order.

    Process document by coverting all words to lowercase, and removing any
    punctuation or English stopwords.
    """
    return [
        word.lower() for word in
        word_tokenize(document)
        if word not in FILTER
    ]


def compute_idfs(documents):
    """
    Given a dictionary of `documents` that maps names of documents to a list
    of words, return a dictionary that maps words to their IDF values.

    Any word that appears in at least one of the documents should be in the
    resulting dictionary.
    """

    # Get all words from documents
    words = set()
    for filename in documents:
        words.update(documents[filename])

    # Calculate word IDFs
    idfs = dict()
    for word in words:
        f = sum(word in documents[filename] for filename in documents)
        idfs[word] = math.log(len(documents) / f)

    return idfs


def top_files(query, files, idfs, n):
    """
    Given a `query` (a set of words), `files` (a dictionary mapping names of
    files to a list of their words), and `idfs` (a dictionary mapping words
    to their IDF values), return a list of the filenames of the the `n` top
    files that match the query, ranked according to tf-idf.
    """
    tfidfs = dict()
    for filename in files:
        tfidf = 0
        for word in query:
            if word in files[filename]:
                tf = files[filename].count(word)
                tfidf += tf * idfs[word]
        tfidfs[filename] = tfidf
    return sorted(list(tfidfs), key=lambda x: tfidfs[x], reverse=True)[:n]


def top_sentences(query, sentences, idfs, n):
    """
    Given a `query` (a set of words), `sentences` (a dictionary mapping
    sentences to a list of their words), and `idfs` (a dictionary mapping words
    to their IDF values), return a list of the `n` top sentences that match
    the query, ranked according to idf. If there are ties, preference should
    be given to sentences that have a higher query term density.
    """

    # Calculate matching word measure and query word density for sentences
    metrics = dict()
    for sentence in sentences:
        mwm = sum(idfs[word] for word in query if word in sentences[sentence])
        qtd = sum(word in query for word in sentences[sentence]) / len(sentences[sentence])
        metrics[sentence] = (mwm, qtd)
    return sorted(list(sentences), key=lambda x: metrics[x], reverse=True)[:n]


if __name__ == "__main__":
    main()
