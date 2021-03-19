import os
import random
import re
import sys
from collections import Counter

DAMPING = 0.85
SAMPLES = 10000
THRESHOLD = 0.001


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python pagerank.py corpus")
    corpus = crawl(sys.argv[1])
    ranks = sample_pagerank(corpus, DAMPING, SAMPLES)
    print(f"PageRank Results from Sampling (n = {SAMPLES})")
    for page in sorted(ranks):
        print(f"  {page}: {ranks[page]:.4f}")
    ranks = iterate_pagerank(corpus, DAMPING)
    print(f"PageRank Results from Iteration")
    for page in sorted(ranks):
        print(f"  {page}: {ranks[page]:.4f}")


def crawl(directory):
    """
    Parse a directory of HTML pages and check for links to other pages.
    Return a dictionary where each key is a page, and values are
    a list of all other pages in the corpus that are linked to by the page.
    """
    pages = dict()

    # Extract all links from HTML files
    for filename in os.listdir(directory):
        if not filename.endswith(".html"):
            continue
        with open(os.path.join(directory, filename)) as f:
            contents = f.read()
            links = re.findall(r"<a\s+(?:[^>]*?)href=\"([^\"]*)\"", contents)
            pages[filename] = set(links) - {filename}

    # Only include links to other pages in the corpus
    for filename in pages:
        pages[filename] = set(
            link for link in pages[filename]
            if link in pages
        )

    return pages


def transition_model(corpus, page, damping_factor):
    """
    Return a probability distribution over which page to visit next,
    given a current page.

    With probability `damping_factor`, choose a link at random
    linked to by `page`. With probability `1 - damping_factor`, choose
    a link at random chosen from all pages in the corpus.
    """

    # Probability that random link is chosen over links on page
    any_link = (1 - damping_factor) / len(corpus)

    # Compute probability distribution
    distribution = dict()
    if not corpus[page]:  # Page has no links
        for link in corpus.keys():
            distribution[link] = 1 / len(corpus)
    else:  # Page has links
        for link in corpus.keys():
            if link in corpus[page]:
                distribution[link] = damping_factor / len(corpus[page]) + any_link
            else:
                distribution[link] = any_link

    return distribution

def sample_pagerank(corpus, damping_factor, n):
    """
    Return PageRank values for each page by sampling `n` pages
    according to transition model, starting with a page at random.

    Return a dictionary where keys are page names, and values are
    their estimated PageRank value (a value between 0 and 1). All
    PageRank values should sum to 1.
    """

    # Initialize list of samples to random page
    samples = [random.choice(list(corpus.keys()))]

    # Generate remaining samples based on transition model
    for i in range(n - 1):
        next = transition_model(corpus, samples[i], damping_factor)
        samples.extend(
            random.choices(list(next.keys()), weights=next.values(), k=1)
        )

    # Count samples from each page
    counts = Counter(samples)

    # Estimate PageRank from sample counts
    pagerank = dict()
    for page in counts.keys():
        pagerank[page] = counts[page] / n

    return pagerank


def iterate_pagerank(corpus, damping_factor):
    """
    Return PageRank values for each page by iteratively updating
    PageRank values until convergence.

    Return a dictionary where keys are page names, and values are
    their estimated PageRank value (a value between 0 and 1). All
    PageRank values should sum to 1.
    """

    # Initialize PageRank and convergence values
    pagerank = dict()
    convergence = dict()
    for page in corpus.keys():
        pagerank[page] = 1 / len(corpus)
        convergence[page] = False

    # Update PageRank values until convergence
    while not all(convergence.values()):

        # Compute PageRank for each page
        current = dict()
        for page in pagerank.keys():
            current[page] = (1 - damping_factor) / len(corpus)
            for other in pagerank.keys():
                if other != page and page in corpus[other]:
                    current[page] += damping_factor * pagerank[other] / len(corpus[other])
                if not corpus[other]:
                    current[page] += damping_factor * pagerank[other] / len(corpus)

        # Mark pages whose values have converged
        for page, value in pagerank.items():
            if abs(current[page] - value) <= THRESHOLD:
                convergence[page] = True

        # Update PageRank values to the current ones
        pagerank = current.copy()

    return pagerank


if __name__ == "__main__":
    main()
