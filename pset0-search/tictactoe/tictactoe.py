"""
Tic Tac Toe Player
"""

import math
import copy

X = "X"
O = "O"
EMPTY = None

MAX = 1
MIN = -1


def initial_state():
    """
    Returns starting state of the board.
    """
    return [[EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY]]


def player(board):
    """
    Returns player who has the next turn on a board.
    """
    count = 0
    for row in board:
        for cell in row:
            if cell != EMPTY:
                count += 1

    if count % 2 == 1:
        return O
    else:
        return X


def actions(board):
    """
    Returns set of all possible actions (i, j) available on the board.
    """
    moves = set()
    for i in range(3):
        for j in range(3):
            if board[i][j] == EMPTY:
                moves.add((i, j))
    return moves


def result(board, action):
    """
    Returns the board that results from making move (i, j) on the board.
    """
    row, cell = action
    new_board = copy.deepcopy(board)

    if new_board[row][cell] != EMPTY:
        raise Exception("Invalid action.")
    else:
        new_board[row][cell] = player(board)
    return new_board


def get_columns(board):
    """
    Returns columns from a 3x3 matrix.
    """
    columns = []
    for i in range(3):
        columns.append([row[i] for row in board])
    return columns


def get_diagonals(board):
    """
    Returns diagonals from a 3x3 matrix.
    """
    return [[board[0][0], board[1][1], board[2][2]],
            [board[0][2], board[1][1], board[2][0]]]


def three_in_a_row(row):
    """
    Returns True if three consecutive moves are from the same player, False otherwise.
    """
    return row.count(row[0]) == 3


def winner(board):
    """
    Returns the winner of the game, if there is one.
    """
    # Check horizontal, vertical and diagonal moves
    rows = board + get_columns(board)+ get_diagonals(board)
    for row in rows:
        if row[0] is not None and three_in_a_row(row):
            return row[0]

    # Return None if there is no winner
    return None


def all_cells_filled(board):
    """
    Returns True if all cells have been filled, False otherwise.
    """
    for row in board:
        for cell in row:
            if cell == EMPTY:
                return False
    return True


def terminal(board):
    """
    Returns True if game is over, False otherwise.
    """
    if winner(board) is not None or all_cells_filled(board):
        return True
    else:
        return False


def utility(board):
    """
    Returns 1 if X has won the game, -1 if O has won, 0 otherwise.
    """
    value = winner(board)
    if value == X:
        return MAX
    elif value == O:
        return MIN
    else:
        return 0


def maxvalue(board, alpha, beta):
    """
    Returns max utility value for a given state.
    """
    v = MIN

    # If game is over, return utility
    if terminal(board):
        return utility(board)

    # Search lower nodes and return max utility (v)
    for action in actions(board):
        v = max(v, minvalue(result(board, action), alpha, beta))
        alpha = max(v, alpha)  # Update alpha if current utility is higher

        # Stop if maximizer's best guaranteed utility (alpha) equals/exceeds minimizer's at current node
        if beta <= alpha:
            break

    return v


def minvalue(board, alpha, beta):
    """
    Returns min utility value for a given state.
    """
    v = MAX

    # If game is over, return utility
    if terminal(board):
        return utility(board)

    # Search lower nodes and return min utility (v)
    for action in actions(board):
        v = min(v, maxvalue(result(board, action), alpha, beta))
        beta = min(v, beta)  # Update beta if current utility is lower

        # Stop if minimizer's best guaranteed utility (beta) equals/is lower than maximizer's at current node
        if beta <= alpha:
            break

    return v


def minimax(board):
    """
    Returns the optimal action for the current player on the board.
    """

    # If game is over, return None
    if terminal(board):
        return None

    # Else, intialize local variables
    turn = player(board)
    move = None
    alpha = MIN
    beta = MAX

    # Find the best move for the current player
    if turn == X:

        v = MIN
        for action in actions(board):
            new_v = minvalue(result(board, action), alpha, beta)
            alpha = max(new_v, alpha)  # Update alpha if current utility is higher

            # Keep track of optimal move
            if new_v > v:
                move = action
                v = new_v

            # Stop if no other moves lead to a better result for maximizer
            if beta <= alpha:
                break

    else:

        v = MAX
        for action in actions(board):
            new_v = maxvalue(result(board, action), alpha, beta)
            beta = min(new_v, beta)  # Update beta if current utility is lower

            # Keep track of optimal move
            if new_v < v:
                move = action
                v = new_v

            # Stop if no other moves lead to a better result for minimizer
            if beta <= alpha:
                break

    return move
