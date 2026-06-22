import random
from .environment import BaseEnvironment
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


    # Actions in our env comprise of : ahead, left, right, wink
    # 1. ahead : move snake 1 step forward in current facing direction
    # 2. left : move snake 1 step forward in left of current facing direction
    # 3. right : move snake 1 step forward in right of current facing direction
    # 4. wink : shirnk the size with some penulty and if snake has no body nodes it moves 1 step forward
    def __init__(self):
        super().__init__()
        self.current_state = np.zeros(13)
        self._intialized = False

    def env_init(self, env_info = {
        'grid_layout' : (10, 10),
        'grid_size' : (400, 400),
        'grid_location' : (20, 80),
        'apple_count' : 1,
    }):
        self.grid_layout = env_info['grid_layout']
        self.grid_size = env_info['grid_size']
        self.grid_location = env_info['grid_location']
        self.apple_count = env_info['apple_count']

        self.grid = Grid(
            grid_layout=self.grid_layout,
            grid_size=self.grid_size,
            grid_location=self.grid_location
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
        pass

    def env_cleanup(self):
        return None
    
    def env_message(self, message):
        return None
    
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
        danger_vector = get_danger_vector(snake_head, snake_facing, snake_body_positions, self.grid_layout)

        is_grid_full = 1 if (self.apple_count + self.snake.length == (self.grid.layout[0] * self.grid.layout[1])) else 0

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