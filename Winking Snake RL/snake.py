import pygame
import time
import os
import random
pygame.font.init()

GRID_NAME = "Grid_10.png"
GRID_LAYOUT = (10, 10)
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
APPLE_IMG = pygame.transform.scale(pygame.image.load(os.path.join("imgs", "Apple.png")), CELL_SIZE)

WIN_WIDTH = 440
WIN_HEIGHT = 500
STAT_FONT = pygame.font.SysFont("comicsans", 20)

class SnakeNode :
    def __init__(self, position, facing, nodeType):
        self.position = position
        self.facing = facing      # 0: Up,  1: Right,  2: Bottom,  3: Left
        self.nodeType = nodeType  # 0: Head, 1: Tail, 2: Body
        self.whichTurn = 0        # 0: no turn, 1: right, 2: left
        self.last_pos = position
        self.last_facing = facing

class Snake():
    IMGS = SNAKE_IMGS
    def __init__(self, position, facing):
        self.length = 2

        self.head = SnakeNode(position, facing, 0)
        tail_position = self.get_next_node_loc(parent_position=position,parent_facing=facing)
        self.tail = SnakeNode(tail_position, facing, 1)

        self.nodes = [self.head, self.tail]

    def get_next_node_loc(self, parent_position, parent_facing):
        child_pos = None
        if parent_facing == 0:  # Facing Top
            child_pos = (parent_position[0], parent_position[1] + 1)
        elif parent_facing == 1:  # Facing Right
            child_pos = (parent_position[0] - 1, parent_position[1])
        elif parent_facing == 2:  # Facing Bottom
            child_pos = (parent_position[0], parent_position[1] - 1)
        elif parent_facing == 3:  # Facing Left
            child_pos = (parent_position[0] + 1, parent_position[1])
        
        return child_pos

    def add_node(self):
        position = self.tail.position
        facing = self.tail.facing
        body_node = SnakeNode(position=position, facing=facing, nodeType=2)

        self.tail.position = self.tail.last_pos
        self.tail.facing = self.tail.last_facing

        temp_tail = self.nodes.pop()
        self.nodes.append(body_node)
        self.nodes.append(temp_tail)

        self.length += 1

    def move(self):
        for i in reversed(range(1, self.length)): 
            x , y = self.nodes[i-1].position
            face = self.nodes[i-1].facing
            turn = self.nodes[i-1].whichTurn

            last_pos = self.nodes[i].position
            last_face = self.nodes[i].facing

            self.nodes[i].position = [x, y]
            self.nodes[i].facing = face
            self.nodes[i].last_pos = last_pos
            self.nodes[i].last_facing = last_face
            self.nodes[i].whichTurn = turn

        if self.head.facing == 0:
            self.head.position[1] -= 1    # Move Up
        elif self.head.facing == 1:
            self.head.position[0] += 1    # Move Right
        elif self.head.facing == 2:
            self.head.position[1] += 1    # Move Down
        elif self.head.facing == 3:
            self.head.position[0] -= 1    # Move Left
        
        self.head.whichTurn = 0

    def right(self):
        for i in reversed(range(1, self.length)): 
            x , y = self.nodes[i-1].position
            face = self.nodes[i-1].facing
            turn = self.nodes[i-1].whichTurn

            last_pos = self.nodes[i].position
            last_face = self.nodes[i].facing

            self.nodes[i].position = [x, y]
            self.nodes[i].facing = face
            self.nodes[i].last_pos = last_pos
            self.nodes[i].last_facing = last_face
            self.nodes[i].whichTurn = turn

        if self.head.facing == 0:
            self.head.position[0] += 1    # Move Right
            self.head.facing = 1
        elif self.head.facing == 1:
            self.head.position[1] += 1    # Move Down
            self.head.facing = 2
        elif self.head.facing == 2:
            self.head.position[0] -= 1    # Move Left
            self.head.facing = 3
        elif self.head.facing == 3:
            self.head.position[1] -= 1    # Move Up
            self.head.facing = 0

        self.head.whichTurn = 1

    def left(self):
        for i in reversed(range(1, self.length)): 
            x , y = self.nodes[i-1].position
            face = self.nodes[i-1].facing
            turn = self.nodes[i-1].whichTurn

            last_pos = self.nodes[i].position
            last_face = self.nodes[i].facing

            self.nodes[i].position = [x, y]
            self.nodes[i].facing = face
            self.nodes[i].last_pos = last_pos
            self.nodes[i].last_facing = last_face
            self.nodes[i].whichTurn = turn

        if self.head.facing == 0:
            self.head.position[0] -= 1    # Move Left
            self.head.facing = 3
        elif self.head.facing == 1:
            self.head.position[1] -= 1    # Move Up
            self.head.facing = 0
        elif self.head.facing == 2:
            self.head.position[0] += 1    # Move Right
            self.head.facing = 1
        elif self.head.facing == 3:
            self.head.position[1] += 1    # Move Down
            self.head.facing = 2

        self.head.whichTurn = 2
    
    def wink(self):
        """Special Fucnction that gives snake ability to get more score by shrinking its size directly 2 (initial point) with some penuly."""
        if self.length > 2 :
            pos = self.nodes[1].position
            face = self.nodes[1].facing
            last_pos = self.nodes[1].last_pos
            last_face = self.nodes[1].last_facing

            self.tail.position = pos.copy()
            self.tail.facing = face
            self.tail.last_pos = last_pos.copy()
            self.tail.last_facing = last_face

            for _ in range(self.length-1):
                self.nodes.pop()

            self.nodes.append(self.tail)
            self.length = 2
        else :
            self.move()
        

    def didCollide(self, grid):
        """Returns true is head position is out of grid or on the current position of its body"""
        collide = False
        
        x, y = self.head.position
        if x < 0 or x >= grid.layout[0] or y < 0 or y >= grid.layout[1]:
            collide = True

        for i in range(2,self.length):
            if (x == self.nodes[i].position[0]) and (y == self.nodes[i].position[1]):
                collide = True

        return collide

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

            image = self.IMGS[idx]

            rotation = 0  # No Rotation
            if face == 1:
                rotation = 270    # 90 deg anti clk wise rotation
            elif face == 2:
                rotation = 180    # 180 deg anti clk wise rotation
            elif face == 3:
                rotation = 90    # 270 deg anti clk wise rotation
            rotated_image = pygame.transform.rotate(image, rotation)
            new_rect = rotated_image.get_rect(center = image.get_rect(topleft = (x, y)).center) # makes the iamge centered correctly after rotation

            win.blit(rotated_image, new_rect.topleft)

class Apple:
    IMG = APPLE_IMG
    def __init__(self, position):
        self.position = position
        self.eaten = False
        #self.age = 0       # Will Implement Later
        #self.life = 10

    # def live(self):
    #     self.age += 1
    #     if self.age >= self.life:
    #         return False
    #     else:
    #         return True

    def draw(self, win, grid):
        x, y = grid.get_location(self.position[0], self.position[1])
        win.blit(self.IMG, (x, y))

class Grid:
    IMG = GRID_IMG
    def __init__(self, grid_layout, grid_size, grid_location):
        self.layout = grid_layout
        self.size = grid_size
        self.x = grid_location[0]
        self.y = grid_location[1]
        self.cell_size = ((self.size[0] / self.layout[0]), (self.size[1] / self.layout[1]))

    def get_cell(self, x, y):
        cell_x = self.x - x // (self.cell_size[0])
        cell_y = self.y - y // (self.cell_size[1])
        return [cell_x, cell_y]
    
    def get_location(self, cell_x, cell_y):
        x = cell_x * self.cell_size[0]
        y = cell_y * self.cell_size[1]
        return [self.x + x, self.y + y]
    
    def draw(self, win):
        win.blit(self.IMG, (self.x, self.y))


def draw_window(win, score, grid, apple, snake):
    win.blit(BG_IMG, (0,0))

    text = STAT_FONT.render("Score: " + str(score), 1, (0,0,0))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 3))
    
    grid.draw(win)
    apple.draw(win, grid)
    snake.draw(win, grid)

    pygame.display.update()

def main():
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()

    grid  = Grid(grid_layout=GRID_LAYOUT, grid_size=GIRD_SIZE, grid_location=GRID_LOC)
    # apple = Apple(position=[0,0])
    # snake = Snake(position=[5,5], facing=1)

    a_cell_x , a_cell_y = random.randrange(grid.layout[0]), random.randrange(grid.layout[1])
    apple = Apple(position=[a_cell_x, a_cell_y])

    s_cell_x , s_cell_y = random.randrange(grid.layout[0]), random.randrange(grid.layout[1])
    directions = [0,1,2,3]  # Up, Right, Down, Left
    if (s_cell_x == 0):
        directions.remove(3)  # must not face left
    if (s_cell_x == grid.layout[0]-1):
        directions.remove(1)  # must not face right
    if (s_cell_y == 0):
        directions.remove(0)  # must not face up
    if (s_cell_y == grid.layout[1]-1):
        directions.remove(2)  # must not face down
    
    facing = random.choice(directions)

    snake = Snake(position=[s_cell_x, s_cell_y], facing=facing)

    score = 0
    run = True
    while run:
        clock.tick(5)  # FPS = 2
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        action = random.choice(["ahead", "right", "left", "wink"])

        print("Action Taken: ", action)

        if action == "ahead":
            snake.move()
        elif action == "right":
            snake.right()
        elif action == "left":
            snake.left()
        elif action == "wink":
            snake.wink()
        else:
            print("INVALID ACTION!!!")

        if (snake.head.position == apple.position):
            apple.eaten = True
            snake.add_node()
            score += 1

        if apple.eaten :
            a_cell_x , a_cell_y = random.randrange(grid.layout[0]), random.randrange(grid.layout[1])
            snake_positions = []
            for i in snake.nodes:
                snake_positions.append(i.position)
            
            while [a_cell_x, a_cell_y] in snake_positions:
                a_cell_x , a_cell_y = random.randrange(grid.layout[0]), random.randrange(grid.layout[1])
                    
            apple = Apple(position=[a_cell_x, a_cell_y])

        if snake.didCollide(grid):
            print("Snake Collided !")
            print("Final Score: ", score)
            run = False
            pygame.quit()
            quit()

        draw_window(win, score, grid, apple, snake)

if __name__ == "__main__":
    main()