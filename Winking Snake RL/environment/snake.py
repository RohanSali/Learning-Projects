class SnakeNode :
    def __init__(self, position, facing, nodeType):
        self.position = position
        self.facing = facing      # 0: Up,  1: Right,  2: Bottom,  3: Left
        self.nodeType = nodeType  # 0: Head, 1: Tail, 2: Body
        self.whichTurn = 0        # 0: no turn, 1: right, 2: left
        self.last_pos = position.copy()
        self.last_facing = facing

class Snake():
    def __init__(self, position, facing):
        self.length = 2

        self.head = SnakeNode(position, facing, 0)
        tail_position = self.get_next_node_loc(parent_position=position,parent_facing=facing)
        self.tail = SnakeNode(tail_position, facing, 1)

        self.nodes = [self.head, self.tail]

    def get_next_node_loc(self, parent_position, parent_facing):
        child_pos = None
        if parent_facing == 0:  # Facing Top
            child_pos = [parent_position[0], parent_position[1] + 1]
        elif parent_facing == 1:  # Facing Right
            child_pos = [parent_position[0] - 1, parent_position[1]]
        elif parent_facing == 2:  # Facing Bottom
            child_pos = [parent_position[0], parent_position[1] - 1]
        elif parent_facing == 3:  # Facing Left
            child_pos = [parent_position[0] + 1, parent_position[1]]
        
        return child_pos

    def add_node(self):
        position = self.tail.position
        facing = self.tail.facing
        body_node = SnakeNode(position=position, facing=facing, nodeType=2)

        self.tail.position = self.tail.last_pos.copy()
        self.tail.facing = self.tail.last_facing

        temp_tail = self.nodes.pop()
        self.nodes.append(body_node)
        self.nodes.append(temp_tail)

        self.length += 1
    
    def move_body(self):
        """Move all body nodes to follow the previous node."""
        for i in reversed(range(1, self.length)):
            x, y = self.nodes[i - 1].position
            face = self.nodes[i - 1].facing
            turn = self.nodes[i - 1].whichTurn

            last_pos = self.nodes[i].position.copy()
            last_face = self.nodes[i].facing

            self.nodes[i].position = [x, y]
            self.nodes[i].facing = face
            self.nodes[i].last_pos = last_pos
            self.nodes[i].last_facing = last_face
            self.nodes[i].whichTurn = turn

    def move_head(self):
        """Move head one step in its current direction."""
        self.head.last_pos = self.head.position.copy()

        if self.head.facing == 0:      # Up
            self.head.position[1] -= 1
        elif self.head.facing == 1:    # Right
            self.head.position[0] += 1
        elif self.head.facing == 2:    # Down
            self.head.position[1] += 1
        elif self.head.facing == 3:    # Left
            self.head.position[0] -= 1

    def ahead(self):
        self.move_body()
        self.head.last_facing = self.head.facing
        self.move_head()
        self.head.whichTurn = 0

    def right(self):
        self.move_body()
        self.head.last_facing = self.head.facing
        self.head.facing = (self.head.facing + 1) % 4  # Look towards Right
        self.move_head()
        self.head.whichTurn = 1

    def left(self):
        self.move_body()
        self.head.last_facing = self.head.facing
        self.head.facing = (self.head.facing - 1) % 4  # Look towards Left
        self.move_head()
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
            self.ahead()
        

    def didCollide(self, grid):
        """Returns true is head position is out of grid or on the current position of its body"""
        collide = False
        
        x, y = self.head.position
        if x < 0 or x >= grid.layout[0] or y < 0 or y >= grid.layout[1]:
            collide = True

        for node in self.nodes[2:]:
            if node.position == [x, y]:
                collide = True

        return collide

class Apple:
    def __init__(self, position):
        self.position = position
        self.eaten = False

class Grid:
    def __init__(self, grid_layout, grid_size, grid_location):
        self.layout = grid_layout
        self.size = grid_size
        self.x = grid_location[0]
        self.y = grid_location[1]
        self.cell_size = ((self.size[0] / self.layout[0]), (self.size[1] / self.layout[1]))

    def get_cell(self, x, y):
        cell_x = x - self.x // (self.cell_size[0])
        cell_y = y - self.y // (self.cell_size[1])
        return [cell_x, cell_y]
    
    def get_location(self, cell_x, cell_y):
        x = cell_x * self.cell_size[0]
        y = cell_y * self.cell_size[1]
        return [self.x + x, self.y + y]        