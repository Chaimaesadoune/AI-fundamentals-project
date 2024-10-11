import time
import random
from client import ClientSocket
from argparse import ArgumentParser

class Creature:
    def __init__(self, count):
        self.count = count

    def move(self, from_cell, to_cell, grid):
        if grid[to_cell[0]][to_cell[1]] == "":
            grid[to_cell[0]][to_cell[1]] = self
            grid[from_cell[0]][from_cell[1]] = ""
        else:
            self.battle(grid[to_cell[0]][to_cell[1]])

    def battle(self, opponent):
        E1 = self.count
        E2 = opponent.count
        if E1 >= 1.5 * E2:
            # Guaranteed win
            self.count -= int(0.5 * E2)
            opponent.count = 0
        elif E2 >= 1.5 * E1:
            # Guaranteed loss
            opponent.count -= int(0.5 * E1)
            self.count = 0
        else:
            # Random battle
            if E1 == E2:
                P = 0.5
            elif E1 < E2:
                P = E1 / (2 * E2)
            else:
                P = E1 / E2 - 0.5

            if random.random() < P:
                # Attackers win
                self.count = int(self.count * P)
                opponent.count = int(opponent.count * P)
                if isinstance(opponent, Human):
                    self.convert_humans(opponent)
            else:
                # Attackers lose
                self.count = int(self.count * (1 - P))
                opponent.count = int(opponent.count * (1 - P))

    def convert_humans(self, humans):
        pass  # To be overridden by subclasses

class Vampire(Creature):
    def convert_humans(self, humans):
        if self.count >= humans.count:
            self.count += humans.count
            humans.count = 0

class Werewolf(Creature):
    def convert_humans(self, humans):
        if self.count >= humans.count:
            self.count += humans.count
            humans.count = 0

class Human(Creature):
    pass

class GameState:
    def __init__(self, n, m):
        self.players = {}
        self.map = [["" for _ in range(m)] for _ in range(n)]
        self.turn = 0

    def update_player(self, player_id, data):
        self.players[player_id] = data

    def update_map(self, map_data):
        self.map = map_data

    def increment_turn(self):
        self.turn += 1

# Initialize the game state
n, m = 3, 3  # Example grid size
GAME_STATE = GameState(n, m)

def UPDATE_GAME_STATE(message):
    global GAME_STATE

    if message[0] == "upd":
        player_id = message[1]
        player_data = message[2:]
        GAME_STATE.update_player(player_id, player_data)
    elif message[0] == "map":
        map_data = message[1:]
        GAME_STATE.update_map(map_data)
    elif message[0] == "turn":
        GAME_STATE.increment_turn()
    else:
        print(f"Unknown message type: {message[0]}")

# Define a cache for evaluated moves
move_cache = {}

def is_valid_position(position, game_map):
    n, m = len(game_map), len(game_map[0])
    return 0 <= position[0] < n and 0 <= position[1] < m

def evaluate_move(position, creatures, game_state):
    score = 0
    cell_content = game_state.map[position[0]][position[1]]
    
    if isinstance(cell_content, Creature):
        if isinstance(cell_content, Vampire) and isinstance(creatures, Werewolf):
            score -= 10  # Penalty for moving towards enemy
        elif isinstance(cell_content, Werewolf) and isinstance(creatures, Vampire):
            score -= 10  # Penalty for moving towards enemy
        else:
            score += 5  # Bonus for moving towards own species
    elif isinstance(cell_content, Human):
        score += 10  # Bonus for moving towards humans

    return score

def minimax(game_state, depth, alpha, beta, maximizing_player):
    if depth == 0 or game_over(game_state):
        return evaluate_game_state(game_state)

    if maximizing_player:
        max_eval = float('-inf')
        for move in get_all_possible_moves(game_state, maximizing_player):
            new_game_state = apply_move(game_state, move)
            eval = minimax(new_game_state, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in get_all_possible_moves(game_state, maximizing_player):
            new_game_state = apply_move(game_state, move)
            eval = minimax(new_game_state, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def get_all_possible_moves(game_state, maximizing_player):
    # Implement logic to get all possible moves for the current player
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    current_position = game_state.players.get("player_id", (0, 0))  # Replace with actual player ID and location
    possible_moves = []
    for direction in directions:
        new_position = (current_position[0] + direction[0], current_position[1] + direction[1])
        if is_valid_position(new_position, game_state.map):
            possible_moves.append((current_position, new_position))
    return possible_moves

def apply_move(game_state, move):

    # Implement logic to apply a move and return the new game state
    new_game_state = GameState(len(game_state.map), len(game_state.map[0]))
    new_game_state.map = [row[:] for row in game_state.map]
    from_pos, to_pos = move
    creature = new_game_state.map[from_pos[0]][from_pos[1]]
    creature.move(from_pos, to_pos, new_game_state.map)

    # Check if the target cell contains humans and convert them if possible
    target_cell_content = new_game_state.map[to_pos[0]][to_pos[1]]
    if isinstance(target_cell_content, Human):
        creature.convert_humans(target_cell_content)
    return new_game_state

def game_over(game_state):

    vampires_exist = any(isinstance(cell, Vampire) for row in game_state.map for cell in row)
    werewolves_exist = any(isinstance(cell, Werewolf) for row in game_state.map for cell in row)
    return not vampires_exist or not werewolves_exist

def evaluate_game_state(game_state):

    vampire_count = sum(cell.count for row in game_state.map for cell in row if isinstance(cell, Vampire))
    werewolf_count = sum(cell.count for row in game_state.map for cell in row if isinstance(cell, Werewolf))
    return vampire_count - werewolf_count

def COMPUTE_NEXT_MOVE(game_state):
    best_score = float('-inf')
    best_move = None

    for move in get_all_possible_moves(game_state, True):
        new_game_state = apply_move(game_state, move)
        score = minimax(new_game_state, 3, float('-inf'), float('inf'), False)
        if score > best_score:
            best_score = score
            best_move = move

    return 1, [best_move]

def play_game(strategy, args):
    client_socket = ClientSocket(args.ip, args.port)
    client_socket.send_nme("NOM DE VOTRE IA")
    
    # Initial messages
    for _ in range(4):
        message = client_socket.get_message()
        UPDATE_GAME_STATE(message)

    # Start of the game
    while True:
        message = client_socket.get_message()
        time_message_received = time.time()
        UPDATE_GAME_STATE(message)
        if message[0] == "upd":
            nb_moves, moves = strategy(GAME_STATE)
            client_socket.send_mov(nb_moves, moves)

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(dest='ip', default='localhost', type=str, help='IP address the connection should be made to.')
    parser.add_argument(dest='port', default='5555', type=int, help='Chosen port for the connection.')
    args = parser.parse_args()
    
    play_game(COMPUTE_NEXT_MOVE, args)