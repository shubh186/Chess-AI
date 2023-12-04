
To execute it, simply run the following commands in the
directory of the code file: python3 ChessAI.py

Note: if there was any problem in executions, try python instead of python3 command.
********************************************************************************

Evaluation Function: 
********************************************************************************
The utility value for terminal or maximum depth nodes is determined as follows:

If the terminal state is "checkmate":

- Returns negative infinity if max_user got checkmate.
- Returns positive infinity otherwise.
- If the terminal state is "stalemate": Returns 0.

For other cases:

- Part of the evaluation score is derived from the difference between the total value of scores assigned to the pieces for max_user and the opponent.

- Pieces are scored according to: {'Q' : 5, 'R' : 4, 'B' : 3, 'N' : 3, 'P' : 1}.

Another part of the evaluation score is based on the difference between:

- Max_user's number of next possible moves.
- The opponent's number of next possible moves, multiplied by a specific coefficient.
- States where a player has more opportunities are considered superior.


Sorting Successor Outcomes of States:
********************************************************************************
To enhance the efficiency of alpha-beta pruning, possible outcomes are sorted.

The main part of the score for this sorting comes from:

- The score of the picked piece by the move (if the action picks any piece).
- Another part of this score is based on: The piece just moved, divided by 10.
- A very small score is also considered for longer distance movements.


