import sys
import copy

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """

        # Loop over all variables and their domains
        for var, domain in self.domains.items():

            # Kepp track of inconsistent domain values
            inconsistent = set()
            for word in domain:
                if len(word) != var.length:
                    inconsistent.add(word)

            # Remove current variable's inconsistent values
            for word in inconsistent:
                domain.remove(word)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """

        # Initialize `revise` to False
        revised = False

        # Check that `x` and `y` form an arc
        if self.crossword.overlaps[x, y]:
            i, j = self.crossword.overlaps[x, y]

            # Keep track of inconsistent domain values
            inconsistent = set()

            # Check all of `x`'s domain values
            for w1 in self.domains[x]:

                # At least one value of `y` must be consistent
                consistent = any(
                    w1[i] == w2[j] for w2 in self.domains[y]
                )

                # Otherwise, add value to `inconsistent`
                if not consistent:
                    inconsistent.add(w1)
                    revised = True

            # Remove `x`'s inconsistent values
            for word in inconsistent:
                self.domains[x].remove(word)

        return revised

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """

        # Initialize queue to arcs
        if arcs:
            queue = arcs
        else:
            queue = []
            for v1 in self.crossword.variables:
                for v2 in self.crossword.neighbors(v1):
                    queue.append((v1, v2))

        # While queue isn't empty
        while queue:

            # Take next arc
            x, y = queue[0]
            queue = queue[1:]

            # Enforce arc consistency
            if self.revise(x, y):

                # `x`'s domain mustn't be empty
                if not self.domains[x]:
                    return False

                # Add `x`'s arcs to queue to check consistency still holds
                for z in self.crossword.neighbors(x):
                    if z != y and (z, x) not in queue:
                        queue.append((z, x))

        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        return all(var in assignment for var in self.crossword.variables)

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """

        # Assignment values must be distinct
        words = assignment.values()
        if len(words) != len(set(words)):
            return False

        # Assignment values mustn't violate unary/binary constraints
        for var, word in assignment.items():

            if len(word) != var.length:
                return False

            for neighbor in self.crossword.neighbors(var):
                if neighbor in assignment:
                    i, j = self.crossword.overlaps[var, neighbor]
                    if assignment[var][i] != assignment[neighbor][j]:
                        return False

        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """

        # Keep track of inconsistent values for each value of `var`
        domain = dict()

        # Loop over `var`'s domain values
        for w1 in self.domains[var]:

            # Initialize count
            count = 0

            # Count many neighbors' values are ruled out by current value
            for neighbor in self.crossword.neighbors(var):
                if neighbor in assignment:
                    continue

                for w2 in self.domains[neighbor]:
                    i, j = self.crossword.overlaps[var, neighbor]
                    if w1[i] != w2[j]:
                        count += 1

            # Store total in `domain`
            domain[w1] = count

        # Return values in order (least-constraining values first)
        return sorted(domain, key=lambda x: domain[x])

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """

        # Initialize unassigned variables
        unassigned = [
            var for var in self.crossword.variables
            if var not in assignment
        ]

        # Sort them by domain size (minimum remaining values first)
        ranked = sorted(
            unassigned,
            key=lambda x: len(self.domains[x])
        )

        # Sort them by degree if tied (highest degree first)
        if unassigned == ranked:
            ranked = sorted(
                unassigned,
                key=lambda x: len(self.crossword.neighbors(x)),
                reverse=True
            )

        return ranked[0]

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """

        # Return assignment if all variables have been assigned a value
        if self.assignment_complete(assignment):
            return assignment

        # Otherwise, select an unassigned variable and assign a value
        var = self.select_unassigned_variable(assignment)
        for value in self.order_domain_values(var, assignment):
            assignment[var] = value

            # Call `backtrack` recursively until assignment is complete/None
            if self.consistent(assignment):
                    result = self.backtrack(assignment)
                    if result:
                        return result

            assignment.pop(var)

        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
