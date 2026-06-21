import pygame
import neat
import os
import random

pygame.font.init()
STAT_FONT = pygame.font.SysFont("comicsans", 20)

GRID_NAME = "Grid_5.png"
GRID_LAYOUT = (5, 5)
GIRD_SIZE = (400, 400)
GRID_LOC = (20, 80)
CELL_SIZE = (int(GIRD_SIZE[0]/GRID_LAYOUT[0]), int(GIRD_SIZE[1]/GRID_LAYOUT[1]))

BG_IMG = pygame.image.load(os.path.join("imgs", "BgIMG.png"))
GRID_IMG = pygame.image.load(os.path.join("imgs", GRID_NAME))

SNAKE_IMGS = [
    pygame.transform.scale(pygame.image.load(os.path.join("imgs", "Head.png")), CELL_SIZE),
    pygame.transform.scale(pygame.image.load(os.path.join("imgs", "Tail.png")), CELL_SIZE),
    pygame.transform.scale(pygame.image.load(os.path.join("imgs", "Body.png")), CELL_SIZE),
    pygame.transform.scale(pygame.image.load(os.path.join("imgs", "RightTurn.png")), CELL_SIZE),
    pygame.transform.scale(pygame.image.load(os.path.join("imgs", "LeftTurn.png")), CELL_SIZE)
]

APPLE_IMG = pygame.transform.scale(
    pygame.image.load(os.path.join("imgs", "Apple.png")),
    CELL_SIZE
)

WIN_WIDTH = 440
WIN_HEIGHT = 500
GEN = 0

class SnakeNode:
    def __init__(self, position, facing, nodeType):
        self.position = position
        self.facing = facing
        self.nodeType = nodeType
        self.whichTurn = 0
        self.last_pos = position.copy()
        self.last_facing = facing

class Snake:
    def __init__(self, position, facing):
        self.length = 2
        self.head = SnakeNode(position, facing, 0)
        tail_position = self.get_next_node_loc(position, facing)
        self.tail = SnakeNode(list(tail_position), facing, 1)
        self.nodes = [self.head, self.tail]

    def get_next_node_loc(self, parent_position, parent_facing):
        if parent_facing == 0:
            return (parent_position[0], parent_position[1] + 1)
        elif parent_facing == 1:
            return (parent_position[0] - 1, parent_position[1])
        elif parent_facing == 2:
            return (parent_position[0], parent_position[1] - 1)
        return (parent_position[0] + 1, parent_position[1])

    def _shift(self):
        for i in reversed(range(1, self.length)):
            self.nodes[i].last_pos = self.nodes[i].position.copy()
            self.nodes[i].last_facing = self.nodes[i].facing
            self.nodes[i].position = self.nodes[i-1].position.copy()
            self.nodes[i].facing = self.nodes[i-1].facing
            self.nodes[i].whichTurn = self.nodes[i-1].whichTurn

    def move(self):
        self._shift()
        if self.head.facing == 0: self.head.position[1] -= 1
        elif self.head.facing == 1: self.head.position[0] += 1
        elif self.head.facing == 2: self.head.position[1] += 1
        else: self.head.position[0] -= 1
        self.head.whichTurn = 0

    def right(self):
        self._shift()
        self.head.facing = (self.head.facing + 1) % 4
        if self.head.facing == 0: self.head.position[1] -= 1
        elif self.head.facing == 1: self.head.position[0] += 1
        elif self.head.facing == 2: self.head.position[1] += 1
        else: self.head.position[0] -= 1
        self.head.whichTurn = 1

    def left(self):
        self._shift()
        self.head.facing = (self.head.facing - 1) % 4
        if self.head.facing == 0: self.head.position[1] -= 1
        elif self.head.facing == 1: self.head.position[0] += 1
        elif self.head.facing == 2: self.head.position[1] += 1
        else: self.head.position[0] -= 1
        self.head.whichTurn = 2

    def wink(self):
        if self.length > 2:
            pos = self.nodes[1].position
            face = self.nodes[1].facing
            self.tail.position = pos.copy()
            self.tail.facing = face
            for _ in range(self.length - 1):
                self.nodes.pop()
            self.nodes.append(self.tail)
            self.length = 2
        else:
            self.move()

    def add_node(self):
        body = SnakeNode(self.tail.position.copy(), self.tail.facing, 2)
        self.tail.position = self.tail.last_pos.copy()
        self.tail.facing = self.tail.last_facing
        temp = self.nodes.pop()
        self.nodes.append(body)
        self.nodes.append(temp)
        self.length += 1

    def didCollide(self, grid):
        x, y = self.head.position
        if x < 0 or x >= grid.layout[0] or y < 0 or y >= grid.layout[1]:
            return True
        for i in range(2, self.length):
            if self.nodes[i].position == [x, y]:
                return True
        return False

    def get_inputs(self, apple, grid):
        hx, hy = self.head.position

        def coll(x, y):
            if x < 0 or x >= grid.layout[0] or y < 0 or y >= grid.layout[1]:
                return 1
            for i in range(1, self.length):
                if self.nodes[i].position == [x, y]:
                    return 1
            return 0

        d = self.head.facing
        if d == 0:
            ds, dl, dr = coll(hx, hy-1), coll(hx-1, hy), coll(hx+1, hy)
        elif d == 1:
            ds, dl, dr = coll(hx+1, hy), coll(hx, hy-1), coll(hx, hy+1)
        elif d == 2:
            ds, dl, dr = coll(hx, hy+1), coll(hx+1, hy), coll(hx-1, hy)
        else:
            ds, dl, dr = coll(hx-1, hy), coll(hx, hy+1), coll(hx, hy-1)

        return (
            ds, dl, dr,
            1 if apple.position[1] < hy else 0,
            1 if apple.position[1] > hy else 0,
            1 if apple.position[0] < hx else 0,
            1 if apple.position[0] > hx else 0,
            (apple.position[0]-hx)/grid.layout[0],
            (apple.position[1]-hy)/grid.layout[1]
        )
    
    def draw(self, win, grid):
        for i in range(self.length):
            node_type = self.nodes[i].nodeType
            position = self.nodes[i].position
            x, y = grid.get_location(position[0], position[1])
            face = self.nodes[i].facing

            idx = node_type

            if node_type == 2:
                turn = self.nodes[i-1].whichTurn
                if turn == 1:
                    idx = 3
                elif turn == 2:
                    idx = 4

            elif node_type == 1:
                face = self.nodes[i-1].facing

            image = SNAKE_IMGS[idx]

            rotation = 0

            if face == 1:
                rotation = 270

            elif face == 2:
                rotation = 180

            elif face == 3:
                rotation = 90

            rotated_image = pygame.transform.rotate(
                image,
                rotation
            )

            new_rect = rotated_image.get_rect(
                center=image.get_rect(
                    topleft=(x, y)
                ).center
            )

            win.blit(
                rotated_image,
                new_rect.topleft
            )

class Apple:
    IMG = APPLE_IMG

    def __init__(self, position):
        self.position = position

    def draw(self, win, grid):
        x, y = grid.get_location(
            self.position[0],
            self.position[1]
        )

        win.blit(
            self.IMG,
            (x, y)
        )

class Grid:
    IMG = GRID_IMG

    def __init__(
            self,
            grid_layout,
            grid_size,
            grid_location):

        self.layout = grid_layout
        self.size = grid_size

        self.x = grid_location[0]
        self.y = grid_location[1]

        self.cell_size = (
            self.size[0] / self.layout[0],
            self.size[1] / self.layout[1]
        )

    def get_location(
            self,
            cell_x,
            cell_y):

        x = cell_x * self.cell_size[0]
        y = cell_y * self.cell_size[1]

        return [
            self.x + x,
            self.y + y
        ]

    def draw(self, win):
        win.blit(
            self.IMG,
            (self.x, self.y)
        )
        
def random_snake(grid):
    x = random.randrange(grid.layout[0])
    y = random.randrange(grid.layout[1])
    directions = [0,1,2,3]

    if x == 0:
        directions.remove(3)

    if x == grid.layout[0]-1:
        directions.remove(1)

    if y == 0:
        directions.remove(0)

    if y == grid.layout[1]-1:
        directions.remove(2)

    facing = random.choice(directions)

    return Snake(
        [x,y],
        facing
    )

def random_apple(grid, snake):
    while True:
        p = [random.randrange(grid.layout[0]), random.randrange(grid.layout[1])]
        if p not in [n.position for n in snake.nodes]:
            return Apple(p)

def draw_window(
        win,
        grid,
        apple,
        snake,
        score,
        generation,
        fitness):

    win.blit(BG_IMG, (0,0))

    grid.draw(win)
    apple.draw(win, grid)
    snake.draw(win, grid)

    score_text = STAT_FONT.render(
        f"Score: {score}",
        1,
        (0,0,0)
    )

    gen_text = STAT_FONT.render(
        f"Gen: {generation}",
        1,
        (0,0,0)
    )

    fit_text = STAT_FONT.render(
        f"Fitness: {round(fitness,2)}",
        1,
        (0,0,0)
    )

    len_text = STAT_FONT.render(
        f"Length: {snake.length}",
        1,
        (0,0,0)
    )

    win.blit(score_text,(5,5))
    win.blit(gen_text,(5,25))
    win.blit(fit_text,(5,45))
    win.blit(len_text,(5,65))

    pygame.display.update()

def eval_genomes(genomes, config):
    global GEN
    GEN += 1
    grid = Grid(
        GRID_LAYOUT,
        GIRD_SIZE,
        GRID_LOC
    )

    win = pygame.display.set_mode(
        (WIN_WIDTH, WIN_HEIGHT)
    )

    clock = pygame.time.Clock()

    for _, genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        genome.fitness = 0.0

        snake = random_snake(grid)
        apple = random_apple(grid, snake)
        moves_without_food = 0
        score = 0
        last_action = None
        same_action_count = 0   

        visited_positions = {}
        while True:
            clock.tick(10)
            for event in pygame.event.get():

                if event.type == pygame.QUIT:

                    pygame.quit()
                    quit()

            inputs = snake.get_inputs(apple, grid)
            outputs = net.activate(inputs)
            action = outputs.index(max(outputs))

            if action == last_action:
                same_action_count += 1
            else:
                same_action_count = 1
                last_action = action

            action_name = [
                "AHEAD",
                "LEFT",
                "RIGHT",
                "WINK"
            ][action]

            print(
                "Gen:",
                GEN,
                "Fitness:",
                round(genome.fitness,2),
                "Length:",
                snake.length,
                "Action:",
                action_name
            )

            genome.fitness -= 0.1
            genome.fitness += 0.001

            if action == 0:
                snake.move()
            elif action == 1:
                snake.left()
            elif action == 2:
                snake.right()
            else:
                genome.fitness -= (3.0 / snake.length)
                snake.wink()

            # penalize repetitive behaviour

            if same_action_count > 10:
                genome.fitness -= 0.10

            if same_action_count > 20:
                genome.fitness -= 0.20

            if same_action_count > 50:
                genome.fitness -= 0.50

            pos = tuple(snake.head.position)

            visited_positions[pos] = (
                visited_positions.get(pos, 0) + 1
            )

            if visited_positions[pos] > 4:
                genome.fitness -= 0.1

            moves_without_food += 1

            if snake.head.position == apple.position:
                snake.add_node()
                genome.fitness += 50
                moves_without_food = 0
                score += 1
                apple = random_apple(grid, snake)

            if snake.didCollide(grid):
                genome.fitness -= 100
                break

            if moves_without_food > 50:
                genome.fitness -= 10
                break
        
            draw_window(
                win,
                grid,
                apple,
                snake,
                score,
                GEN,
                genome.fitness
            )

def run(config_path):
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_path
    )

    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    p.add_reporter(neat.StatisticsReporter())

    winner = p.run(eval_genomes, 500)
    print("Winner:", winner)

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "nn-config.txt")
    run(config_path)
