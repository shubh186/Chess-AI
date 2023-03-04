#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os

class HeuristicScores:
    CHECKMATE = 100000000
    CHECK = 0
    STALEMATE = 0
    
    SCORES = {'Q' : 5, 'R' : 4, 'B' : 3, 'N' : 3, 'P' : 1, 'K' : 0}
    
    OPPORTUNITIES_COEF = 0.05


class GameStatus:
    INVALID_INPUT = 'INVALID_INPUT'
    VALID_MOVE = 'VALID_MOVE'
    INVALID_MOVE = 'INVALID_MOVE'
    INVALID_MOVE_DUE_TO_CHECK = 'INVALID_MOVE_DUE_TO_CHECK'
    AWAITING_PROMOTION = 'AWAITING_PROMOTION'
    INVALID_PROMOTION = 'INVALID_PROMOTION'
    
    CHECK = 'CHECK'
    CHECKMATE = 'CHECKMATE'
    STALEMATE = 'STALEMATE'

class ChessBoard():
    def __init__(self, orig=None):
        if orig is None:
            self.__constructor()
        else:
            self.__copy_constructor(orig)
    
    # initialize new board:
    def __constructor(self):
        self.board = [['wR', 'wN', 'wB', 'wQ', 'wK', 'wB', 'wN', 'wR'],
                      ['wP', 'wP', 'wP', 'wP', 'wP', 'wP', 'wP', 'wP'],
                      ['.', '.', '.', '.', '.', '.', '.', '.'],
                      ['.', '.', '.', '.', '.', '.', '.', '.'],
                      ['.', '.', '.', '.', '.', '.', '.', '.'],
                      ['.', '.', '.', '.', '.', '.', '.', '.'],
                      ['bP', 'bP', 'bP', 'bP', 'bP', 'bP', 'bP', 'bP'],
                      ['bR', 'bN', 'bB', 'bQ', 'bK', 'bB', 'bN', 'bR']]
        
        self.turn = 'w'
        self.status = GameStatus.VALID_MOVE
        
        # information to validate castling move:
        self.king_ever_moved = {'b': False, 'w': False}
        self.right_rook_ever_moved = {'b': False, 'w': False}
        self.left_rook_ever_moved = {'b': False, 'w': False}
        
        # information to help sort successor outcomes in alpha-beta pruning:
        self.last_move_score = 0
        
    # copy existing board:
    def __copy_constructor(self, orig):
        self.board = [['']*8 for i in range(8)]
        for y, row in enumerate(orig.board):
            for x, piece in enumerate(row):
                self.board[y][x] = piece
                
        self.turn = orig.turn
        self.status = orig.status
        
        self.king_ever_moved = orig.king_ever_moved.copy()
        self.right_rook_ever_moved = orig.right_rook_ever_moved.copy()
        self.left_rook_ever_moved = orig.left_rook_ever_moved.copy()
        
        self.last_move_score = orig.last_move_score
        
    def print_board(self):
        for index, row in enumerate(self.board):
            print(index + 1, end='\t')
            print(*row, sep='\t', end='\n\n')
            
        for i in range(ord('A'), ord('H')+1):
            print(end='\t')
            print(chr(i), end='')
            
        print(end='\n')
            
    @staticmethod
    def __column_index(column):
        if 'a' <= column <= 'h':
            return ord(column) - ord('a')
        elif 'A' <= column <= 'H':
            return ord(column) - ord('A')
        else:
            raise Exception('ERROR: invalid column address')
            
    @staticmethod
    def chess_pos_to_index(pos):
        return [int(pos[1]) - 1, ChessBoard.__column_index(pos[0])]
    
    @staticmethod     
    def __valid_position(position):
        if len(position) != 2:
            return False
        if not ('a' <= position[0] <= 'h' or 'A' <= position[0] <= 'H'):
            return False
        if not ('1' <= position[1] <= '8'):
            return False
        return True
    
    @staticmethod     
    def __opposite_turn(turn):
        if turn == 'w':
            return 'b'
        elif turn == 'b':
            return 'w'
        else:
            raise Exception('ERROR: invalid turn')
    
    @staticmethod    
    def __sign(number):
        if number > 0:
            return 1
        if number < 0:
            return -1
        return 0
    
    # plays a move and returns status
    # status can be: VALID_MOVE, INVALID_MOVE, INVALID_MOVE_DUE_TO_CHECK or AWAITING_PROMOTION
    def play(self, start, target):
        if not (ChessBoard.__valid_position(start) and ChessBoard.__valid_position(target)):
            self.status = GameStatus.INVALID_INPUT
            return self.status
        start = ChessBoard.chess_pos_to_index(start)
        target = ChessBoard.chess_pos_to_index(target)
        
        if not self.__check_move_legal(start, target):
            self.status = GameStatus.INVALID_MOVE
            return self.status
        
        # possibly valid move, but still need to check if player's king gets in danger
        # so what we do is: temporarily apply the move, check for king being checked
        # if king is safe, confirm the move otherwise restore board and let user 
        # make a different move
        
        # save game state to restore:
        orig_board = ChessBoard(self)
        
        # valid action, apply the move:
        piece = self.board[start[0]][start[1]]
        self.board[start[0]][start[1]] = '.'
        if self.board[target[0]][target[1]] != '.':
            self.last_move_score = HeuristicScores.SCORES[self.board[target[0]][target[1]][1]]
        self.board[target[0]][target[1]] = piece
        
        # update castling validation information:
        row = 7 if self.turn == 'b' else 0
        if piece[1] == 'K':
            self.king_ever_moved[self.turn] = True
        if piece[1] == 'R':
            if start == [row, 0]:
                self.left_rook_ever_moved[self.turn] = True
            elif start == [row, 7]:
                self.right_rook_ever_moved[self.turn] = True
        
        # check if movement is castling:
        if piece[1] == 'K' and abs(target[1] - start[1]) == 2:
            if target[1] > start[1]: # moving the right Rook:
                self.board[row][7] = '.'
                self.board[row][5] = self.turn + 'R'
            else: # moving the left Rook:
                self.board[row][0] = '.'
                self.board[row][3] = self.turn + 'R'
                
        # pawn promotion has no effect on player's king getting checked or not
        # so we check and apply it after move verification
        
        # if player's king is threatened (move verification)
        if self.__check_check():
            # restore original board:
            self.__copy_constructor(orig_board)
            
            self.status = GameStatus.INVALID_MOVE_DUE_TO_CHECK
            return self.status
        
        # now we made sure that the move is valid and verified
        # so the movement is confirmed
                
        # check if movement is promotion:
        if piece[1] == 'P' and (target[0] == 0 or target[0] == 7):
            self.status = GameStatus.AWAITING_PROMOTION
            return self.status
        
        # successful move, now it's opponent's turn
        self.status = GameStatus.VALID_MOVE
        self.turn = ChessBoard.__opposite_turn(self.turn)
        return self.status
        
    # replaces the pawn with another piece and returns status
    # status can be: VALID_MOVE or INVALID_PROMOTION
    def apply_promotion(self, replacement):
        if self.status not in {GameStatus.AWAITING_PROMOTION, GameStatus.INVALID_PROMOTION}:
            raise Exception('ERROR: no pawn is awaiting promotion')
        replacement = replacement.upper()
        if replacement not in {'R', 'N', 'B', 'Q'}:
            self.status = GameStatus.INVALID_PROMOTION
            return GameStatus.INVALID_PROMOTION
            
        row = 0 if self.turn == 'b' else 7
        
        for i in range(8):
            if self.board[row][i] == (self.turn + 'P'):
                self.board[row][i] = (self.turn + replacement)
                break
        
        # successful move, now it's opponent's turn
        self.status = GameStatus.VALID_MOVE
        self.turn = ChessBoard.__opposite_turn(self.turn)
        return self.status
       
    # checks if the king is in check
    # returns True if the king is in check
    # returns False if the king is not threatened
    def __check_check(self):
        # find player's king:
        king = None
        for y, row in enumerate(self.board):
            for x, piece in enumerate(row):
                if piece == self.turn + 'K':
                    king = [y, x]
                    break
            if king is not None:
                break
                
        # temporarily change the turn:
        self.turn = ChessBoard.__opposite_turn(self.turn)
        
        # check if anyone can attack player's king
        attack_found = False
        for y, row in enumerate(self.board):
            for x, piece in enumerate(row):
                if self.__check_move_legal([y, x], king):
                    attack_found = True # king is in check
                    break
            if attack_found:
                break
            
        # restore turn change:
        self.turn = ChessBoard.__opposite_turn(self.turn)
        
        return attack_found
        
    # checks if moving a piece from start to target is legal, given self.turn
    def __check_move_legal(self, start, target):
        if self.board[start[0]][start[1]] == '.': # no piece to move
            return False
        if self.board[start[0]][start[1]][0] != self.turn: # moving the wrong color
            return False
        if self.board[target[0]][target[1]][0] == self.turn: # self attack or not moving
            return False
        if self.board[start[0]][start[1]][1] == 'P':
            return self.__pawn_move_legal(start, target)
        if self.board[start[0]][start[1]][1] == 'R':
            return self.__rook_move_legal(start, target)
        if self.board[start[0]][start[1]][1] == 'N':
            return self.__knight_move_legal(start, target)
        if self.board[start[0]][start[1]][1] == 'B':
            return self.__bishop_move_legal(start, target)
        if self.board[start[0]][start[1]][1] == 'Q':
            return self.__queen_move_legal(start, target)
        if self.board[start[0]][start[1]][1] == 'K':
            return self.__king_move_legal(start, target)
        
    def __pawn_move_legal(self, start, target):
        base = 6 if self.turn == 'b' else 1
        direction = -1 if self.turn == 'b' else 1
        if (target[0] - start[0]) * direction <= 0: # vertically backward or still
            return False
        
        if start[1] == target[1]: # forward
            if self.board[start[0] + direction][start[1]] != '.': # 1 steps ahead is occupied
                return False
            if abs(target[0] - start[0]) > 2: # more than 2 steps
                return False
            if abs(target[0] - start[0]) == 2 and start[0] != base:
                return False # 2 steps but not first move
            if abs(target[0] - start[0]) == 2 and self.board[start[0] + 2 * direction][start[1]] != '.':
                return False # 2 steps ahead is occupied
            return True
        
        # diagonal:
        if abs(target[1] - start[1]) == 1 and abs(target[0] - start[0]) == 1 and self.board[target[0]][target[1]] != '.':
            return True
        return False
    
    def __rook_move_legal(self, start, target):
        v_move = abs(target[0] - start[0])
        h_move = abs(target[1] - start[1])
        if v_move > 0 and h_move > 0: # diagonal
            return False
        
        y_step = ChessBoard.__sign(target[0] - start[0])
        x_step = ChessBoard.__sign(target[1] - start[1])
        
        for i in range(1, v_move + h_move):
            if self.board[start[0] + y_step * i][start[1] + x_step * i] != '.':
                return False
        return True
    
    def __knight_move_legal(self, start, target):
        v_move = abs(target[0] - start[0])
        h_move = abs(target[1] - start[1])
        if (h_move == 1 and v_move == 2) or (h_move == 2 and v_move == 1):
            return True
        return False
    
    def __bishop_move_legal(self, start, target):
        v_move = abs(target[0] - start[0])
        h_move = abs(target[1] - start[1])
        if v_move != h_move:
            return False
        
        y_step = ChessBoard.__sign(target[0] - start[0])
        x_step = ChessBoard.__sign(target[1] - start[1])
        
        for i in range(1, v_move):
            if self.board[start[0] + y_step * i][start[1] + x_step * i] != '.':
                return False
        return True
    
    def __queen_move_legal(self, start, target):
        return self.__bishop_move_legal(start, target) or self.__rook_move_legal(start, target)
    
    def __king_move_legal(self, start, target):
        v_move = abs(target[0] - start[0])
        h_move = abs(target[1] - start[1])
        
        if v_move <= 1 and h_move <= 1:
            return True
        
        if h_move == 2 and v_move == 0 and not self.king_ever_moved[self.turn]:
            row = 7 if self.turn == 'b' else 0
            if target[1] > start[1] and not self.right_rook_ever_moved[self.turn]:
                if self.board[row][5] == '.' and self.board[row][6] == '.':
                    return True
            elif target[1] < start[1] and not self.left_rook_ever_moved[self.turn]:
                if self.board[row][1] == '.' and self.board[row][2] == '.' and self.board[row][3] == '.':
                    return True
            
        return False
    
    # returns CHECK, CHECKMATE, STALEMATE or None
    def get_game_status(self):
        checks = self.__check_check()
        action_outcomes = self.forcast_actions()
        
        # the player is in check and has no valid moves
        if len(action_outcomes) == 0 and checks:
            return GameStatus.CHECKMATE
        # the player is not check but has no valid moves
        if len(action_outcomes) == 0 and not checks:
            return GameStatus.STALEMATE
        # the player is in check but has valid moves
        if checks:
            return GameStatus.CHECK
        # the player is not in check and has valid moves
        return None
    
    # returns possible (action, outcome) pairs for the next move
    # by moving a specific piece at position(start)
    # action is tuple: (piece to move, target position, pawn promotion replacement)
    def __forcast_by_piece(self, start):
        start = chr(start[1] + ord('A')) + str(start[0] + 1)
        action_outcomes = []
        
        # create a new board for for forcast testing so the original game board is untouched
        test_board = ChessBoard(self)
        
        # for every target position, check if player can play (start, target) move:
        for y, row in enumerate(self.board):
            for x, piece in enumerate(row):
                target = chr(x + ord('A')) + str(y + 1)
                
                # play the action
                play_result = test_board.play(start, target)
                
                # if valid action
                if play_result == GameStatus.VALID_MOVE:
                    # valid move, store the (action, outcome) pair:
                    action_outcomes.append(((start, target, None), test_board))
                    
                    # now create another test board for other possible moves:
                    test_board = ChessBoard(self)
                
                # if valid but needs pawn promotion
                elif play_result == GameStatus.AWAITING_PROMOTION:
                    # we assign Queen or Knight for promotion
                    # as there is no point in promotion with Bishop or Rook rather than Queen
                    
                    # fork board for alternative promotion
                    promotion_fork = ChessBoard(test_board)
                    
                    # promote to Knight
                    promotion_fork.apply_promotion('N')
                    action_outcomes.append(((start, target, 'N'), promotion_fork))
                    
                    # promote to Queen
                    test_board.apply_promotion('Q')
                    action_outcomes.append(((start, target, 'Q'), test_board))
                    
                    test_board = ChessBoard(self)

        return action_outcomes
    
    # returns possible (action, outcome) pairs for the next move
    # given the current state of the game (self)
    def forcast_actions(self):
        action_outcomes = []
        # for every position
        for y, row in enumerate(self.board):
            for x, piece in enumerate(row):
                # if there is a piece and the piece is ours:
                if self.board[y][x] != '.' and self.board[y][x][0] == self.turn:
                    # get possible (action, outcome)s by
                    # moving a special piece at position(y,x):
                    action_outcomes += self.__forcast_by_piece([y,x])
            
        return action_outcomes
    
        
    # returns (action_outcomes, terminal_state, utility)
    # action_outcomes is the forcast for all possible outcomes for the next move
    # terminal_state determines wether it's end of the game or not
    # utility is the chess board's heuristic score for player('w' or 'b')
    # merged into a single function to avoid forcasting multiple times
    def forcast_terminal_utility(self, player):
        # check if player is in check
        checks = self.__check_check()
        
        # get all possible outcomes for the next move:
        action_outcomes = self.forcast_actions()
        
        # determine game_status and terminal state:
        terminal_state = False
        if len(action_outcomes) == 0 and checks:
            game_status = GameStatus.CHECKMATE
            terminal_state = True
        elif len(action_outcomes) == 0 and not checks:
            game_status = GameStatus.STALEMATE
            terminal_state = True
        elif checks:
            game_status = GameStatus.CHECK
        else:
            game_status = None
            
        
        if game_status == GameStatus.CHECKMATE:
            if self.turn == player: # player got checkmated
                return action_outcomes, terminal_state, -HeuristicScores.CHECKMATE
            
            # opponent got checkmated
            return action_outcomes, terminal_state, HeuristicScores.CHECKMATE
        
        if game_status == GameStatus.STALEMATE:
            return action_outcomes, terminal_state, HeuristicScores.STALEMATE
        
        utility = 0
        
        if self.turn == player:
            utility += len(action_outcomes) * HeuristicScores.OPPORTUNITIES_COEF
        else:
            utility -= len(action_outcomes) * HeuristicScores.OPPORTUNITIES_COEF
        
        if game_status == GameStatus.CHECK:
            if self.turn == player: # player got checked
                utility -= HeuristicScores.CHECK
            else: # opponent got checked
                utility += HeuristicScores.CHECK
                
        scores = {'b': 0, 'w': 0}
        for y, row in enumerate(self.board):
            for x, piece in enumerate(row):
                if piece != '.':
                    scores[piece[0]] += HeuristicScores.SCORES[piece[1]]
                    
        utility += scores[player]
        utility -= scores[ChessBoard.__opposite_turn(player)]
        
        return action_outcomes, terminal_state, utility
        

class MinMax():
    INFINITY = 1000000000
    
    # sort for a more efficient alpha-beta pruning:
    def sort_forcast(forcast):
        if len(forcast) == 0:
            return forcast
        
        forcast_utility_sorted = []
        for action, outcome in forcast:
            start = ChessBoard.chess_pos_to_index(action[0])
            target = ChessBoard.chess_pos_to_index(action[1])
            target_piece = outcome.board[target[0]][target[1]]
            utility = 0
            
            # a little score for longer moves (to break even cases)
            utility += max(abs(target[0] - start[0]), abs(target[1] - start[1])) / 40
            # score for the move's oponent pick
            utility += outcome.last_move_score
            # prioritize higher score piece moves 
            utility += HeuristicScores.SCORES[target_piece[1]] / 10
            
            forcast_utility_sorted.append((utility, (action, outcome)))
            
        forcast_utility_sorted.sort(key=lambda tup: tup[0], reverse=True)
        
        forcast_sorted = []
        for utility, element in forcast_utility_sorted:
            forcast_sorted.append(element)
            
        return forcast_sorted
    
    @staticmethod # max_player is requred for proper heuristic utility calculation
    def alpha_beta_decision(chess_board, max_depth, max_player):
        forcast = chess_board.forcast_actions()
        
        forcast = MinMax.sort_forcast(forcast)
        
        value = -MinMax.INFINITY
        best_action = None
        for action, outcome in forcast:
            tmp = MinMax.min_value(outcome, max_depth - 1, -MinMax.INFINITY, MinMax.INFINITY, max_player)
            if tmp > value:
                value = tmp
                best_action = action
                
        return best_action
    
    @staticmethod
    def max_value(chess_board, max_depth, alpha, beta, max_player):
        # get forcast, terminal and utility of chess_board
        forcast, terminal, utility = chess_board.forcast_terminal_utility(max_player)
        
        forcast = MinMax.sort_forcast(forcast)
        
        # check terminal 
        if max_depth == 0 or terminal:
            return utility
        
        value = -MinMax.INFINITY
        
        for action, outcome in forcast:
            value = max(value, MinMax.min_value(outcome, max_depth - 1, alpha, beta, max_player))
            alpha = max(alpha, value)
            if value >= beta:
                break
        
        return value
    
    @staticmethod
    def min_value(chess_board, max_depth, alpha, beta, max_player):
        # get forcast, terminal and utility of chess_board
        forcast, terminal, utility = chess_board.forcast_terminal_utility(max_player)
        
        forcast = MinMax.sort_forcast(forcast)
        
        # check terminal 
        if max_depth == 0 or terminal:
            return utility
        
        value = MinMax.INFINITY
        
        for action, outcome in forcast:
            value = min(value, MinMax.max_value(outcome, max_depth - 1, alpha, beta, max_player))
            beta = min(beta, value)
            if value <= alpha:
                break
        
        return value
    
def AI_play(chess_board, max_depth, max_player):
    start, target, promotion = MinMax.alpha_beta_decision(chess_board, max_depth, max_player)
    status = chess_board.play(start, target)
    if status == GameStatus.AWAITING_PROMOTION:
        chess_board.apply_promotion(promotion)

# clear terminal
def clear_terminal():
    os.system('cls' if os.name=='nt' else 'clear')

# clears screen and prints chess board
# returns game status
def print_board(chess_board):
    clear_terminal()
    chess_board.print_board()
    status = chess_board.get_game_status()
    print(status)
    if status == GameStatus.CHECKMATE or status == GameStatus.STALEMATE:
        print('Game Over!')
        
    return status

def play_two_AIs(chess_board):
    while True:
        # the more powerful one, with depth 3 prediction
        AI_play(chess_board, 3, 'w')
        status = print_board(chess_board)
        if status == GameStatus.CHECKMATE or status == GameStatus.STALEMATE:
            break

        # the weaker AI, predicts 2 levels deep
        AI_play(chess_board, 2, 'b')
        status = print_board(chess_board)
        if status == GameStatus.CHECKMATE or status == GameStatus.STALEMATE:
            break

def user_play(chess_board):
    while True:
        move = input('Enter move:')
        move = move.split()
        if len(move) != 2:
            print('Enter like example: [B2 A3]')
            continue
        status = chess_board.play(move[0], move[1])
        if status == GameStatus.AWAITING_PROMOTION:
            while True:
                promotion = input('promote pawn with? [R, N, B, Q]:')
                status = chess_board.apply_promotion(promotion)
                if status == GameStatus.VALID_MOVE:
                    break
                print('choose again')
                
        elif status == GameStatus.VALID_MOVE:
            break
            
        print('invalid move')
        
        
def two_player_mode(chess_board):
    print_board(chess_board)
    while True:
        user_play(chess_board)
        status = print_board(chess_board)
        if status == GameStatus.CHECKMATE or status == GameStatus.STALEMATE:
            break
        user_play(chess_board)
        status = print_board(chess_board)
        if status == GameStatus.CHECKMATE or status == GameStatus.STALEMATE:
            break
    
    
def play_with_AI(chess_board, max_player, AI_DEPTH):
    print_board(chess_board)
    # if AI is first do the first move
    if max_player == 'w':
        print('AI is thinking...')
        AI_play(chess_board, AI_DEPTH, max_player)
        print_board(chess_board)
        
    while True:
        user_play(chess_board)
        status = print_board(chess_board)
        if status == GameStatus.CHECKMATE or status == GameStatus.STALEMATE:
            break
    
        print('Thinking...')
        AI_play(chess_board, AI_DEPTH, max_player)
        status = print_board(chess_board)
        if status == GameStatus.CHECKMATE or status == GameStatus.STALEMATE:
            break
    
    
# create chess_board
chess_board = ChessBoard()

# uncomment to let two AIs play with each other
# play_two_AIs(chess_board)

# the depth of decision tree
# the more this number, the more powerful the AI becomes
# but it taked exponentially longer time to play
AI_DEPTH = 3

while True:
    players = input('1 player or 2 players? [1, 2]:')
    
    if players == '1':
        while True:
            color = input('choose your color [b, w]:')
            if color == 'w':
                max_player = 'b'
                break
            if color == 'b':
                max_player = 'w'
                break
            print('choose again')
            
        play_with_AI(chess_board, max_player, AI_DEPTH)
            
    if players == '2':
        two_player_mode(chess_board)
        
    print('choose again')    



# In[ ]:




