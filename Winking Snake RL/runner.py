import sys
from pathlib import Path
import random

from environment.snake import Snake, Grid, Apple
from visualizer.pygame_visualizer import Visualizer, GRID_SIZE, GRID_LOC

GRID_NAME = "Grid_10.png"
GRID_LAYOUT = (10, 10)

def reset_environment(apple_count=1):
    grid = Grid(grid_layout=GRID_LAYOUT, grid_size=GRID_SIZE, grid_location=GRID_LOC)

    s_cell_x, s_cell_y = random.randrange(grid.layout[0]), random.randrange(grid.layout[1])
    directions = [0, 1, 2, 3]  # Up, Right, Down, Left
    if s_cell_x == 0:
        directions.remove(1)  # must not face right
    if s_cell_x == grid.layout[0] - 1:
        directions.remove(3)  # must not face left
    if s_cell_y == 0:
        directions.remove(2)  # must not face down
    if s_cell_y == grid.layout[1] - 1:
        directions.remove(0)  # must not face up
    facing = random.choice(directions)
    snake = Snake(position=[s_cell_x, s_cell_y], facing=facing)

    apples = []
    filled_positions = []
    for _ in range(apple_count):
        a_cell_x, a_cell_y = random.randrange(grid.layout[0]), random.randrange(grid.layout[1])

        while [a_cell_x, a_cell_y] in filled_positions or (
            [a_cell_x, a_cell_y] in [snake.head.position, snake.tail.position]
        ):
            a_cell_x, a_cell_y = random.randrange(grid.layout[0]), random.randrange(grid.layout[1])

        apple = Apple(position=[a_cell_x, a_cell_y])
        apples.append(apple)
        if [a_cell_x, a_cell_y] not in filled_positions:
            filled_positions.append([a_cell_x, a_cell_y])

    return grid, snake, apples, filled_positions


def step(action, grid, snake, apples, filled_positions, score, apple_count):
    if action == "ahead":
        snake.ahead()
    elif action == "right":
        snake.right()
    elif action == "left":
        snake.left()
    elif action == "wink":
        snake.wink()
    else:
        print("INVALID ACTION!!!")

    for apple in apples:
        if snake.head.position == apple.position:
            apple.eaten = True
            snake.add_node()
            score += 1

    for apple in apples:
        if apple.eaten:
            apples.remove(apple)
            filled_positions.remove(apple.position)
            snake_positions = [node.position for node in snake.nodes]

            a_cell_x, a_cell_y = random.randrange(grid.layout[0]), random.randrange(grid.layout[1])
            while [a_cell_x, a_cell_y] in filled_positions or ([a_cell_x, a_cell_y] in snake_positions):
                a_cell_x, a_cell_y = random.randrange(grid.layout[0]), random.randrange(grid.layout[1])

            new_apple = Apple(position=[a_cell_x, a_cell_y])
            apples.append(new_apple)
            if [a_cell_x, a_cell_y] not in filled_positions:
                filled_positions.append([a_cell_x, a_cell_y])

    done = False

    if snake.didCollide(grid):
        print("Snake Collided !")
        print("Final Score: ", score)
        done = True

    if snake.length + apple_count == (grid.layout[0] * grid.layout[1]):
        print("Grid is Full")
        print("Final Score:", score)
        done = True

    return score, done


def choose_action():
    return random.choice(["ahead", "right", "left", "wink"])


def run_episode(render=True, fps=5, apple_count=1, visualizer=None):
    grid, snake, apples, filled_positions = reset_environment(apple_count)

    owns_visualizer = visualizer is None
    if render and visualizer is None:
        visualizer = Visualizer(
            grid_name=GRID_NAME,
            grid_layout=GRID_LAYOUT,
            fps=fps,
        )
        visualizer.init()

    score = 0
    run = True
    while run:
        if render and visualizer is not None:
            visualizer.tick()
            if not visualizer.handle_events():
                run = False
                break

        action = choose_action()
        print("Action Taken: ", action)

        score, done = step(action, grid, snake, apples, filled_positions, score, apple_count)

        if render and visualizer is not None:
            visualizer.render(grid, apples, snake, score)

        if done:
            run = False

    if render and owns_visualizer and visualizer is not None:
        visualizer.close()

    return score


def main(render=True, fps=5):
    run_episode(render=render, fps=fps, apple_count=90)


if __name__ == "__main__":
    main()