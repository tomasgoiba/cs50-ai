import csv
import itertools
import sys

PROBS = {

    # Unconditional probabilities for having gene
    "gene": {
        2: 0.01,
        1: 0.03,
        0: 0.96
    },

    "trait": {

        # Probability of trait given two copies of gene
        2: {
            True: 0.65,
            False: 0.35
        },

        # Probability of trait given one copy of gene
        1: {
            True: 0.56,
            False: 0.44
        },

        # Probability of trait given no gene
        0: {
            True: 0.01,
            False: 0.99
        }
    },

    # Mutation probability
    "mutation": 0.01
}


def main():

    # Check for proper usage
    if len(sys.argv) != 2:
        sys.exit("Usage: python heredity.py data.csv")
    people = load_data(sys.argv[1])

    # Keep track of gene and trait probabilities for each person
    probabilities = {
        person: {
            "gene": {
                2: 0,
                1: 0,
                0: 0
            },
            "trait": {
                True: 0,
                False: 0
            }
        }
        for person in people
    }

    # Loop over all sets of people who might have the trait
    names = set(people)
    for have_trait in powerset(names):

        # Check if current set of people violates known information
        fails_evidence = any(
            (people[person]["trait"] is not None and
             people[person]["trait"] != (person in have_trait))
            for person in names
        )
        if fails_evidence:
            continue

        # Loop over all sets of people who might have the gene
        for one_gene in powerset(names):
            for two_genes in powerset(names - one_gene):

                # Update probabilities with new joint probability
                p = joint_probability(people, one_gene, two_genes, have_trait)
                update(probabilities, one_gene, two_genes, have_trait, p)

    # Ensure probabilities sum to 1
    normalize(probabilities)

    # Print results
    for person in people:
        print(f"{person}:")
        for field in probabilities[person]:
            print(f"  {field.capitalize()}:")
            for value in probabilities[person][field]:
                p = probabilities[person][field][value]
                print(f"    {value}: {p:.4f}")


def load_data(filename):
    """
    Load gene and trait data from a file into a dictionary.
    File assumed to be a CSV containing fields name, mother, father, trait.
    mother, father must both be blank, or both be valid names in the CSV.
    trait should be 0 or 1 if trait is known, blank otherwise.
    """
    data = dict()
    with open(filename) as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"]
            data[name] = {
                "name": name,
                "mother": row["mother"] or None,
                "father": row["father"] or None,
                "trait": (True if row["trait"] == "1" else
                          False if row["trait"] == "0" else None)
            }
    return data


def powerset(s):
    """
    Return a list of all possible subsets of set s.
    """
    s = list(s)
    return [
        set(s) for s in itertools.chain.from_iterable(
            itertools.combinations(s, r) for r in range(len(s) + 1)
        )
    ]


def joint_probability(people, one_gene, two_genes, have_trait):
    """
    Compute and return a joint probability.

    The probability returned should be the probability that
        * everyone in set `one_gene` has one copy of the gene, and
        * everyone in set `two_genes` has two copies of the gene, and
        * everyone not in `one_gene` or `two_gene` does not have the gene, and
        * everyone in set `have_trait` has the trait, and
        * everyone not in set` have_trait` does not have the trait.
    """

    # Map children to the number of copies of the gene each parent has
    children = {
        person : (
            gene_copies(people[person]["mother"], one_gene, two_genes),
            gene_copies(people[person]["father"], one_gene, two_genes)
        )
        for person in people if people[person]["mother"] and people[person]["father"]
    }

    # Initialize joint probability
    probability = 1

    for person in people:

        # Number of copies of the gene `person` has
        copies = gene_copies(person, one_gene, two_genes)

        # Whether `person` exhibits the trait
        has_trait = person in have_trait

        # Probability that `person` has 0, 1 or 2 copies of the gene
        if person in children:  # If they have parents
            probability *= gets_gene(children[person], copies)

        else:  # If they don't have parents
            probability *= PROBS["gene"][copies]

        # Probability that `person` has the trait or doesn't
        probability *= PROBS["trait"][copies][has_trait]

    return probability


def gene_copies(person, one_gene, two_genes):
    """
    Returns the number of copies of the gene a person has.
    """
    if person in one_gene:
        return 1
    elif person in two_genes:
        return 2
    else:
        return 0


def gets_gene(parents, child):
    """
    Given the number of copies of the gene each parent has (`parents`),
    compute and return the conditional probability that the child
    inherits `child` copies of the gene.
    """

    # Probability that parent passes one copy of gene to child
    from_mother = (
        PROBS["mutation"] if parents[0] == 0 else
        0.5 if parents[0] == 1 else
        negation(PROBS["mutation"])
    )

    from_father = (
        PROBS["mutation"] if parents[1] == 0 else
        0.5 if parents[1] == 1 else
        negation(PROBS["mutation"])
    )

    # Child doesn't inherit any copies
    if child == 0:
        probability = negation(from_mother) * negation(from_father)

    # Child inherits 1 copy from one parent (and not the other)
    elif child == 1:
        probability = from_mother * negation(from_father) + from_father * negation(from_mother)

    # Child inherits 2 copies, one from each parent
    else:
        probability = from_mother * from_father

    return probability


def negation(probability):
    """
    Returns the probability that an event doesn't occur.
    """
    return 1 - probability


def update(probabilities, one_gene, two_genes, have_trait, p):
    """
    Add to `probabilities` a new joint probability `p`.
    Each person should have their "gene" and "trait" distributions updated.
    Which value for each distribution is updated depends on whether
    the person is in `have_gene` and `have_trait`, respectively.
    """
    for person in probabilities:
        if person in one_gene:
            probabilities[person]["gene"][1] += p
        elif person in two_genes:
            probabilities[person]["gene"][2] += p
        else:
            probabilities[person]["gene"][0] += p

        if person in have_trait:
            probabilities[person]["trait"][True] += p
        else:
            probabilities[person]["trait"][False] += p


def normalize(probabilities):
    """
    Update `probabilities` such that each probability distribution
    is normalized (i.e., sums to 1, with relative proportions the same).
    """
    for person in probabilities:
        gene_sum = sum(probabilities[person]["gene"].values())
        trait_sum = sum(probabilities[person]["trait"].values())

        for gene in probabilities[person]["gene"]:
            probabilities[person]["gene"][gene] /= gene_sum

        for trait in probabilities[person]["trait"]:
            probabilities[person]["trait"][trait] /= trait_sum


if __name__ == "__main__":
    main()
