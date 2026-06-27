import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import random
from rlglue.environment import BaseEnvironment
import numpy as np
from .snake import Grid, Snake, Apple

class WinkerSnake(BaseEnvironment):
    """Environment for Snake with state space of len 13 and action space of len 4"""
    # State in our env comprise of : snake_head, snake_facing, snake_length, closest_food_distance, food_intuition_vector, danger_vector, is_grid_full
    # 1. snake_head : Position of head of snake in grid as [cell_x, cell_y]
    # 2. snake_facing : Current facing of snake in grid as 0: Up, 1: Right, 2: Down, 3: Left
    # 3. snake_length : Length of snake as integer
    # 4. closest_food_distance : Manhatton distance from Closest apple in grid as [cell_x, cell_y]
    # 5. food_intuition_vector : Tells if in that direction food is present or not. as [Up, Right, Down, Left] ; if [1,1,0,0] tells food in top, right side. (Relative to Grid Directions)
    # 6. danger_vector : If danger in front or adjacent cells where it is facing then it is 1 otherwise 0. as [Ahead, Right, Left] ; if [1,1,0] tells wall or body in top and right side. (Relative to Snake Facing)
    # 7. is_grid_full : It is 1 if grid is full and 0 otherwise.
    # Finally a state is : ndarray as : [head_x, head_y, head_facing, snake_length, closest_food_distance, is_food_up, is_food_right, is_food_down, is_food_left, is_danger_ahead, is_danger_right_side, is_danger_left_side, is_grid_full]


    # Actions in our env comprise of : ahead, right, left, wink
    # 1. ahead or 0 : move snake 1 step forward in current facing direction
    # 2. right or 1 : move snake 1 step forward in right of current facing direction
    # 3. left or 2 : move snake 1 step forward in left of current facing direction
    # 4. wink or 3 : shirnk the size with some penulty and if snake has no body nodes it moves 1 step forward
    def __init__(self):
        super().__init__()
        self.current_state = np.zeros(13)
        self._intialized = False
        self.nodes_added = 0
        self.no_food_eaten_count = 0

    def env_init(self, env_info = {
        'grid_layout' : (10, 10),
        'grid_size' : (500, 500),
        'grid_location' : (40, 200),
        'apple_count' : 1,
    }):
        self.apple_count = env_info['apple_count']

        self.grid = Grid(
            grid_layout = env_info['grid_layout'],
            grid_size = env_info['grid_size'],
            grid_location = env_info['grid_location']
            )

        self.snake = None
        self.apples = []

        self._intialized = True

    def env_start(self):
        if not self._intialized:
            self.env_init()
        self.reset_env()
        
        observation = self.get_observation()
        self.current_state = observation

        reward = 0.0
        terminal = False

        self.reward_obs_term = (reward, observation, terminal)
        return observation

    def env_step(self, action):
        eaten = self.perform_action(action)

        observation = self.get_observation()
        self.current_state = observation

        reward, terminal = self.get_reward(action=action, eaten=eaten, is_grid_full=observation[-1])

        self.reward_obs_term = (reward, observation, terminal)
        return self.reward_obs_term

    def env_cleanup(self):
        self.snake = None
        self.apples = []
        self.current_state = np.zeros(13)
        self.reward_obs_term = None
        self.nodes_added = 0
        self.no_food_eaten_count = 0

    def env_message(self, message):
        if message == "score":
            return self.nodes_added
        if message == "debug":
            return {
                "head": self.snake.head.position,
                "facing": self.snake.head.facing,
                "length": self.snake.length,
                "apples": [a.position for a in self.apples],
            }
    
    def reset_env(self):
        s_cell_x, s_cell_y = random.randrange(self.grid.layout[0]), random.randrange(self.grid.layout[1])
        directions = [0, 1, 2, 3]  # Up, Right, Down, Left
        if s_cell_x == 0:
            directions.remove(1)  # must not face right
        if s_cell_x == self.grid.layout[0] - 1:
            directions.remove(3)  # must not face left
        if s_cell_y == 0:
            directions.remove(2)  # must not face down
        if s_cell_y == self.grid.layout[1] - 1:
            directions.remove(0)  # must not face up
        facing = random.choice(directions)

        self.snake = Snake(position=[s_cell_x, s_cell_y], facing=facing)

        self.apples = []
        filled_positions = []
        for _ in range(self.apple_count):
            a_cell_x, a_cell_y = random.randrange(self.grid.layout[0]), random.randrange(self.grid.layout[1])

            while [a_cell_x, a_cell_y] in filled_positions or (
                [a_cell_x, a_cell_y] in [self.snake.head.position, self.snake.tail.position]
            ):
                a_cell_x, a_cell_y = random.randrange(self.grid.layout[0]), random.randrange(self.grid.layout[1])

            apple = Apple(position=[a_cell_x, a_cell_y])
            self.apples.append(apple)

            if [a_cell_x, a_cell_y] not in filled_positions:
                filled_positions.append([a_cell_x, a_cell_y])
        
        self.nodes_added = 0
        self.no_food_eaten_count = 0

    def get_observation(self):
        snake_head = self.snake.head.position
        snake_facing = self.snake.head.facing
        snake_length = self.snake.length

        closest_apple = get_closest_apple(snake_head, self.apples)
        if closest_apple is not None:
            closest_food = closest_apple.position
            closest_food_distance = manhattan_distance(snake_head, closest_food)
        else:
            closest_food_distance = -1

        food_intuition_vector = get_food_intuition_vector(snake_head, self.apples)

        snake_body_positions = [node.position for node in self.snake.nodes]
        danger_vector = get_danger_vector(snake_head, snake_facing, snake_body_positions, self.grid.layout)

        is_grid_full = 1 if (self.apple_count + self.snake.length >= (self.grid.layout[0] * self.grid.layout[1])) else 0

        observation = np.array(
            [
                *snake_head,
                snake_facing,
                snake_length,
                closest_food_distance,
                *food_intuition_vector,
                *danger_vector,
                is_grid_full,
            ],
            dtype=np.float32,
        )

        return observation
    
    def perform_action(self, action):
        is_eaten = False

        if action == 0:
            self.snake.ahead()
        elif action == 1:
            self.snake.right()
        elif action == 2:
            self.snake.left()
        elif action == 3:
            self.snake.wink()

        for apple in self.apples:
            if self.snake.head.position == apple.position:
                apple.eaten = True
                is_eaten = True
                self.snake.add_node()
                self.nodes_added += 1  # Only for display purpose

        snake_positions = [node.position for node in self.snake.nodes]
        apple_positions = [apple.position for apple in self.apples]
        for apple in list(self.apples):
            if apple.eaten:
                self.apples.remove(apple)
                apple_positions.remove(apple.position)
                
                a_cell_x, a_cell_y = random.randrange(self.grid.layout[0]), random.randrange(self.grid.layout[1])
                while [a_cell_x, a_cell_y] in  apple_positions + snake_positions:
                    a_cell_x, a_cell_y = random.randrange(self.grid.layout[0]), random.randrange(self.grid.layout[1])

                new_apple = Apple(position=[a_cell_x, a_cell_y])
                self.apples.append(new_apple)
        
        return is_eaten
    
    def get_reward(self, action, eaten, is_grid_full):
        reward = 0.0
        terminal = False
        fruit_reward = 5  # or 10
        action_penulty = 0.02  # or 0.01
        death_penulty = 20  # or 50
        k = 5

        early_penulty = k * fruit_reward   # k fruit penulty
        later_penulty = 0.1 * early_penulty
        min_len = 2
        max_len = (self.grid.layout[0] * self.grid.layout[1]) - 2
        t = (self.snake.length - min_len) / (max_len - min_len)
        wink_penulty = later_penulty + (early_penulty - later_penulty) * (1 - t)**2

        if action == 3:   
            reward -= wink_penulty      # wink action   (earlier penulty : k*fruit_reward and later_penulty : 10% of k*fruit_penulty)
        else:       
            reward -= action_penulty    # For other actions

        if eaten:
            reward += fruit_reward
            self.no_food_eaten_count = 0
        else:
            self.no_food_eaten_count += 1

        if self.no_food_eaten_count >= 2*self.grid.layout[0]*self.grid.layout[1]:
            reward -= 100
            terminal = True

        if self.snake.didCollide(self.grid):
            reward -= death_penulty
            terminal = True
        
        if is_grid_full == 1:
            reward -= death_penulty
            terminal = True

        return reward, terminal
    
class WinkerSnake2(WinkerSnake):
    """Environment for Snake (Position Independent) with state space of len 11 and action space of len 4"""
    # State: [head_facing, snake_length, closest_food_distance, is_food_up, is_food_right,
    #         is_food_down, is_food_left, is_danger_ahead, is_danger_right_side,
    #         is_danger_left_side, is_grid_full]

    def __init__(self):
        super().__init__()
        self.current_state = np.zeros(11)

    def get_observation(self):
        snake_head = self.snake.head.position
        snake_facing = self.snake.head.facing
        snake_length = self.snake.length

        closest_apple = get_closest_apple(snake_head, self.apples)
        if closest_apple is not None:
            closest_food = closest_apple.position
            closest_food_distance = manhattan_distance(snake_head, closest_food)
        else:
            closest_food_distance = -1

        food_intuition_vector = get_food_intuition_vector(snake_head, self.apples)

        snake_body_positions = [node.position for node in self.snake.nodes]
        danger_vector = get_danger_vector(snake_head, snake_facing, snake_body_positions, self.grid.layout)

        is_grid_full = 1 if (self.apple_count + self.snake.length >= (self.grid.layout[0] * self.grid.layout[1])) else 0

        observation = np.array(
            [
                snake_facing,
                snake_length,
                closest_food_distance,
                *food_intuition_vector,
                *danger_vector,
                is_grid_full,
            ],
            dtype=np.float32,
        )

        return observation
    
    def env_cleanup(self):
        self.snake = None
        self.apples = []
        self.current_state = np.zeros(11)
        self.reward_obs_term = None
        self.nodes_added = 0
        self.no_food_eaten_count = 0

# Utility Functions:
def manhattan_distance(pos_a, pos_b):
    return abs(pos_a[0] - pos_b[0]) + abs(pos_a[1] - pos_b[1])


def get_closest_apple(snake_head, apples):
    if not apples:
        return None
    return min(apples, key=lambda apple: manhattan_distance(snake_head, apple.position))


def get_food_intuition_vector(snake_head, apples):
    hx, hy = snake_head
    up = right = down = left = 0

    for apple in apples:
        ax, ay = apple.position
        if ay < hy:
            up = 1
        if ax > hx:
            right = 1
        if ay > hy:
            down = 1
        if ax < hx:
            left = 1

    return [up, right, down, left]


def get_danger_vector(snake_head, snake_facing, snake_body_positions, grid_layout):
    hx, hy = snake_head
    cols, rows = grid_layout

    # Direction vectors:
    # 0 = Up, 1 = Right, 2 = Down, 3 = Left
    directions = {
        0: (0, -1),  # up
        1: (1, 0),   # right
        2: (0, 1),   # down
        3: (-1, 0),  # left
    }

    def is_danger(x, y):
        is_wall = x < 0 or x >= cols or y < 0 or y >= rows
        is_body = [x, y] in snake_body_positions
        return 1 if (is_wall or is_body) else 0

    # Ahead
    dx, dy = directions[snake_facing]
    ahead = (hx + dx, hy + dy)

    # Left relative to current facing
    left_facing = (snake_facing - 1) % 4
    dx, dy = directions[left_facing]
    left = (hx + dx, hy + dy)

    # Right relative to current facing
    right_facing = (snake_facing + 1) % 4
    dx, dy = directions[right_facing]
    right = (hx + dx, hy + dy)

    return [
        is_danger(*ahead),
        is_danger(*right),
        is_danger(*left),
    ]