import itertools
import random


class Minesweeper():
    """
    Minesweeper game representation
    """

    def __init__(self, height=8, width=8, mines=8):

        # Set initial width, height, and number of mines
        self.height = height
        self.width = width
        self.mines = set()

        # Initialize an empty field with no mines
        self.board = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                row.append(False)
            self.board.append(row)

        # Add mines randomly
        while len(self.mines) != mines:
            i = random.randrange(height)
            j = random.randrange(width)
            if not self.board[i][j]:
                self.mines.add((i, j))
                self.board[i][j] = True

        # At first, player has found no mines
        self.mines_found = set()

    def print(self):
        """
        Prints a text-based representation
        of where mines are located.
        """
        for i in range(self.height):
            print("--" * self.width + "-")
            for j in range(self.width):
                if self.board[i][j]:
                    print("|X", end="")
                else:
                    print("| ", end="")
            print("|")
        print("--" * self.width + "-")

    def is_mine(self, cell):
        i, j = cell
        return self.board[i][j]

    def nearby_mines(self, cell):
        """
        Returns the number of mines that are
        within one row and column of a given cell,
        not including the cell itself.
        """

        # Keep count of nearby mines
        count = 0

        # Loop over all cells within one row and column
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):

                # Ignore the cell itself
                if (i, j) == cell:
                    continue

                # Update count if cell in bounds and is mine
                if 0 <= i < self.height and 0 <= j < self.width:
                    if self.board[i][j]:
                        count += 1

        return count

    def won(self):
        """
        Checks if all mines have been flagged.
        """
        return self.mines_found == self.mines


class Sentence():
    """
    Logical statement about a Minesweeper game
    A sentence consists of a set of board cells,
    and a count of the number of those cells which are mines.
    """

    def __init__(self, cells, count):
        self.cells = set(cells)
        self.count = count

    def __eq__(self, other):
        return self.cells == other.cells and self.count == other.count

    def __str__(self):
        return f"{self.cells} = {self.count}"

    def is_empty(self):
        """
        Checks if set of cells is empty
        """
        return len(self.cells) == 0

    def known_mines(self):
        """
        Returns the set of all cells in self.cells known to be mines.
        """
        if len(self.cells) == self.count:
            return self.cells
        return set()

    def known_safes(self):
        """
        Returns the set of all cells in self.cells known to be safe.
        """
        if self.count == 0:
            return self.cells
        return set()

    def mark_mine(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be a mine.
        """
        if cell in self.cells:
            self.cells.remove(cell)
            self.count -= 1

    def mark_safe(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be safe.
        """
        if cell in self.cells:
            self.cells.remove(cell)


class MinesweeperAI():
    """
    Minesweeper game player
    """

    def __init__(self, height=8, width=8):

        # Set initial height and width
        self.height = height
        self.width = width

        # Keep track of which cells have been clicked on
        self.moves_made = set()

        # Keep track of cells known to be safe or mines
        self.mines = set()
        self.safes = set()

        # List of sentences about the game known to be true
        self.knowledge = []

    def mark_mine(self, cell):
        """
        Marks a cell as a mine, and updates all knowledge
        to mark that cell as a mine as well.
        """
        self.mines.add(cell)
        for sentence in self.knowledge:
            sentence.mark_mine(cell)

    def mark_safe(self, cell):
        """
        Marks a cell as safe, and updates all knowledge
        to mark that cell as safe as well.
        """
        self.safes.add(cell)
        for sentence in self.knowledge:
            sentence.mark_safe(cell)

    def add_knowledge(self, cell, count):
        """
        Called when the Minesweeper board tells us, for a given
        safe cell, how many neighboring cells have mines in them.
        """

        # Add cell to set of moves made
        self.moves_made.add(cell)

        # Mark cell as safe
        self.mark_safe(cell)

        # Find neighboring cells
        neighbors = list()
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):

                # Ignore cell itself
                if (i, j) == cell:
                    continue

                # Add neighboring cell to set only if it's in bounds
                if 0 <= i < self.height and 0 <= j < self.width:
                    neighbors.append((i, j))

        # Create new sentence and mark known cells as safe or as mines in it
        new_sentence = Sentence(neighbors, count)

        for safe in self.safes:
            new_sentence.mark_safe(safe)
        for mine in self.mines:
            new_sentence.mark_mine(mine)

        self.knowledge.append(new_sentence)

        # Check KB and mark additional cells as safe or as mines if possible
        new_safes = set()
        new_mines = set()

        for sentence in self.knowledge:
            for safe in sentence.known_safes():
                new_safes.add(safe)
            for mine in sentence.known_mines():
                new_mines.add(mine)

        for safe in new_safes:
            self.mark_safe(safe)
        for mine in new_mines:
            self.mark_mine(mine)

        # Add inferences to KB (check for duplicates)
        for superset, subset in itertools.permutations(self.knowledge, 2):
            inference = self.make_inference(superset, subset)
            if inference is not None and inference not in self.knowledge:
                self.knowledge.append(inference)

        # Remove empty KB sentences
        for sentence in self.knowledge:
            if sentence.is_empty():
                self.knowledge.remove(sentence)

    def make_inference(self, superset, subset):
        """
        Returns an inference given a pair of sentences if one's
        cells are a subset of the other. If no inferences can
        be drawn, returns None.
        """
        if superset.cells > subset.cells:
            return Sentence(
                superset.cells - subset.cells,
                superset.count - subset.count
            )
        return None

    def make_safe_move(self):
        """
        Returns a safe cell to choose on the Minesweeper board.
        The move must be known to be safe, and not already a move
        that has been made.
        """

        # Make subset of unselected safe cells
        safe_moves = self.safes - self.moves_made

        # Return cell from subset if not empty
        if safe_moves:
            return random.choice(tuple(safe_moves))
        return None


    def make_random_move(self):
        """
        Returns a move to make on the Minesweeper board.
        Should choose randomly among cells that have not already
        been chosen and are not known to be mines.
        """

        # Make subset of moves left to make
        all_moves = set(itertools.product(range(self.height), range(self.width)))
        moves_left = all_moves - self.moves_made - self.mines

        # Return cell from subset if not empty
        if moves_left:
            return random.choice(tuple(moves_left))
        return None
