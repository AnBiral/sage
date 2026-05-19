from enum import Enum
from sage.combinat.permutation import Permutation

class Decoration(Enum):
    r"""
    Enum to define the decorations of a permutree's vertices and/or a decorated permutation's elements.

    "I" - Decoration with 1 parent and 1 child
    "Down" - Decoration with 1 parent and 2 children
    "Up" - Decoration with 2 parents and 1 child
    "X" - Decoration with 2 parents and 2 children
    """
    I = 'i'
    Down = 'd'
    Up = 'u'
    X = 'x'

    def parent_count(self):
        r"""

        """
        if self is Decoration.I or self is Decoration.Down:
            return 1
        if self is Decoration.X or self is Decoration.Up:
            return 2
        return None

    def child_count(self):
        r"""

        """
        if self is Decoration.I or self is Decoration.Up:
            return 1
        if self is Decoration.X or self is Decoration.Down:
            return 2
        return None


class Permutree():
    def __init__(self, permutation: Permutation, decoration):
        if len(permutation) != len(decoration):
            raise ValueError("Length of permutation and decoration must be equal")

        self._decorations = dict()
        self._vertex_parents = {i: [] for i in range(1, len(permutation)+1, 1)}
        self._walls = dict()
        self.size = len(permutation)

        for i in range(self.size):
            self._decorations[permutation.dict()[i+1]] = decoration[i]

        self.calculate_walls()
        self.insertion(permutation)

    def calculate_walls(self):
        r"""
        walls: [number in permutation, down wall, up wall]
        """
        walls = dict()
        for i, d in self._decorations.items():
            wall = [False, False]
            if d == Decoration.Down or d == Decoration.X:
                wall[0] = True
            if d == Decoration.Up or d == Decoration.X:
                wall[1] = True
            walls[i] = wall
        self._walls = walls

    def insertion(self, permutation):
        active_regions = []  # region = [left wall, right wall, source number of active edge]

        current_region = 0
        for i in range(1, self.size+1, 1):
            if self._walls[i][0] is True:
                active_regions.append([current_region, i, -1])  # -1 means the edge originates from no other vertex
                current_region = i
        active_regions.append([current_region, self.size+1, -1])

        for nb in permutation:
            new_regions = []
            old_regions = []

            for r in range(len(active_regions)):
                curr_reg = active_regions[r]

                if curr_reg[0] < nb < curr_reg[1]:
                    new_regions = [[active_regions[r][0], nb, nb], [nb, curr_reg[1], nb]]
                    if self._decorations[nb] == Decoration.I :
                        new_regions = [[curr_reg[0], curr_reg[1], nb]]

                if curr_reg[0] == nb:  # TODO: merge 2 following if blocks into smaller block
                    if self._decorations[nb] == Decoration.X:
                        new_regions.append([curr_reg[0], curr_reg[1], nb])
                    elif len(new_regions) == 0:
                        new_regions.append([-1, curr_reg[1], nb])
                    else:
                        new_regions[0][1] = curr_reg[1]

                if curr_reg[1] == nb:
                    if self._decorations[nb] == Decoration.X:
                        new_regions.append([curr_reg[0], curr_reg[1], nb])
                    elif len(new_regions) == 0:
                        new_regions.append([curr_reg[0], -1, nb])
                    else:
                        new_regions[0][0] = curr_reg[0]

                if curr_reg[0] <= nb <= curr_reg[1]:
                    if curr_reg[2] != -1:
                        self._vertex_parents[curr_reg[2]].append(nb)  # Set top child of previous vertex
                    old_regions.append(r)

            for r in sorted(old_regions, reverse=True):
                active_regions.pop(r)
            old_regions = []
            active_regions += new_regions
            active_regions.sort()

        for remaining_reg in active_regions:
            self._vertex_parents[remaining_reg[2]].append(-1)  # Set top child of previous vertex

        for k, v in self._vertex_parents.items():
            self._vertex_parents[k] = sorted(v)




class LeveledPermutree(Permutree):
    def __init__(self, permutation: Permutation, decoration):
        Permutree.__init__(self, permutation, decoration)

        self._underlying_permutation = permutation
    def _expanded_bresenham(self, y1, x1, y2, x2):
        points = []
        i = 0
        xstep = ystep = 1
        error = 0
        errorprev = 0
        y = y1
        x = x1
        dx = x2-x1
        dy = y2-y1
        points.append([y1, x1])
        if dy < 0:
            ystep = -1
            dy = -dy
        if dx < 0:
            xstep = -1
            dx = -dx
        ddy = 2*dy
        ddx = 2*dx
        if ddx >= ddy:
            errorprev = error = dx
            for i in range(dx):
                x += xstep
                error += ddy
                if error > ddx:
                    y += ystep
                    error -= ddx
                    if error + errorprev < ddx:
                        points.append([y-ystep, x])
                    elif error + errorprev > ddx:
                        points.append([y, x-xstep])
                    else:
                        points.append([y-ystep, x])
                points.append([y, x])
                errorprev = error
        else:
            errorprev = error = dy
            for i in range(dy):
                y += ystep
                error += ddx
                if error > ddy:
                    x += xstep
                    error -= ddy
                    if error + errorprev < ddy:
                        points.append([y, x-xstep])
                    elif error + errorprev > ddy:
                        points.append([y-ystep, x])
                    else:
                        points.append([y, x-xstep])
                points.append([y, x])
                errorprev = error
        return points

    def __str__(self):  # TODO: needs to be cleaned up
        level = self._underlying_permutation.dict()
        decoration_string = {Decoration.I:"I", Decoration.Down:"⅄", Decoration.Up:"Y", Decoration.X:"X"}
        res = []
        res_str = ""
        res.append(["     " for _ in range(self.size+2)])
        for i in range(self.size):
            res.append(["     " for _ in range(self.size+2)])
            res.append(["     " for _ in range(self.size+2)])

        for n in range(1, self.size+1, 1):  # Add nodes
            res[(self.size-level[n]-1)*2+1][n-1] = " (" + decoration_string[self._decorations[n]] + ") "

        for l in range(len(res)):  # Transform into list of characters
            res_str = ""
            for c in res[l]:
                res_str += c
            res[l] = list(res_str)

        paths_to_draw = []
        for nb, parents in self._vertex_parents.items():
            for p in parents:
                if p != -1:  # Connections between vertices
                    offsets = [0, 0]
                    if self._decorations[nb] == Decoration.X or self._decorations[nb] == Decoration.Up:
                        offsets[0] = -1 if p < nb else 1
                    if self._decorations[p] == Decoration.X or self._decorations[p] == Decoration.Down:
                        offsets[1] = 1 if p < nb else -1
                    paths_to_draw.append(self._expanded_bresenham( (2*(self.size-level[nb])),
                                                                   5*(nb-1) + 7 + offsets[0],
                                                                   (2*(self.size-level[p]+1)),
                                                                   5*(p-1) + 7 + offsets[1]))
                else:  # Connections between vertices and empty space above
                    if len(parents) == 1:
                        paths_to_draw.append(self._expanded_bresenham((2 * (self.size - level[nb])),
                                                                      5 * (nb - 1) + 7,
                                                                      0,
                                                                      5 * (nb - 1) + 7))
                    elif parents[1] == -1:
                        paths_to_draw.append(self._expanded_bresenham((2 * (self.size - level[nb])),
                                                                      5 * (nb - 1) + 6,
                                                                      0,
                                                                      5 * (nb - 2) + 7))
                        paths_to_draw.append(self._expanded_bresenham((2 * (self.size - level[nb])),
                                                                      5 * (nb - 1) + 8,
                                                                      0,
                                                                      5 * (nb) + 7))
                        break
                    else:
                        offset = 1 if parents[1] < nb else -1
                        paths_to_draw.append(self._expanded_bresenham((2 * (self.size - level[nb])),
                                                                      5 * (nb - 1) + 7 + offset,
                                                                      0,
                                                                      5 * (nb) + 7))

        for p in paths_to_draw:
            p = [[p[0][0]+1, p[0][1]]] + p + [[p[-1][0]-1, p[-1][1]]]
            path_matrix = [["│", "┌", "┐"],
                           ["└", "o", "─"],
                           ["┘", "─", "o"]]
            for cell in range(1, len(p) - 1, 1):  # draws path
                mat_prev = 0
                if p[cell - 1][0] - p[cell][0] == 0:  # 0 = down
                    mat_prev = [-1, 1, 2][p[cell - 1][1] - p[cell][1]]  # 1 = right, 2 = left
                mat_next = 0
                if p[cell][0] - p[cell + 1][0] == 0:  # 0 = up
                    mat_next = [-1, 1, 2][p[cell + 1][1] - p[cell][1]]  # 1 = right, 2 = left
                res[p[cell][0]][p[cell][1]] = path_matrix[mat_prev][mat_next]




        orig_pos = []
        #if self.print_walls:
        #    for w in self.walls:
        #        wall_node = self.nodes[perm_inv_dict[w[0]] - 1]
        #        if w[1]:
        #            for i in range((len(self.dec) - wall_node.level) * 2 + 2, 2*len(self.dec)+1, 1):
        #                res[i][5 * (wall_node.position - 1) + 7] = '╵'
        #        elif w[2]:
        #            for i in range(0, (len(self.dec) - wall_node.level) * 2+1, 1):
        #                res[i][5 * (wall_node.position - 1) + 7] = '╵'

        orig_pos = []  # list of [orig_y, orig_x, origin_node, destination_node]



        #for n in self.nodes:
        #    if n.get_child("bl") == -1 or n.get_child("br") == -1:
        #        if n.decoration == 0 or n.decoration == 1:
        #            orig_pos.append([(len(self.dec) - n.level) * 2 + 2, 5 * (n.position - 1) + 7, -1, n.position])
        #        else:
        #            for b in ["bl", "br"]:
        #                if n.get_child(b) == -1:
        #                    orig_pos.append([(len(self.dec)-n.level)*2 + 2, 5*(n.position-1)+(6 if b == "bl" else 8), -1, n.position])
        #    if n.decoration == 0 or n.decoration == 2:
        #        orig_pos.append([(len(self.dec)-n.level)*2, 5*(n.position-1)+7, n.position, n.get_child("t")])
        #    else:
        #        for t in ["tl", "tr"]:
        #            orig_pos.append([(len(self.dec)-n.level)*2, 5*(n.position-1)+(6 if t == "tl" else 8), n.position, n.get_child(t)])
#
        #    for op in orig_pos:
        #        if op[2] == -1:  # Case for down into the void
        #            curr_node = self.nodes[perm_inv_dict[op[3]]-1]
        #            if curr_node.decoration == 0 or curr_node.decoration == 1:
        #                dest_pos = [2*len(self.dec), op[1]]
        #            else:
        #                dest_pos = [2*len(self.dec), op[1] + 4 * (1 if op[1]-(5*(curr_node.position-1)+7) > 0 else -1)]
        #            dest_pos, op = op, dest_pos
#
        #        elif op[3] != -1:
        #            dest_node = self.nodes[perm_inv_dict[op[3]]-1]
        #            if dest_node.decoration == 0 or dest_node.decoration == 1:
        #                dest_pos = (len(self.dec) - dest_node.level) * 2 + 2, 5 * (dest_node.position-1) + 7
        #            else:
        #                dest_pos = (len(self.dec) - dest_node.level) * 2 + 2, 5 * (dest_node.position-1) + (6 if dest_node.get_child("bl") == op[2] else 8)
#
        #        else:  # Case for up into the void
        #            curr_node = self.nodes[perm_inv_dict[op[2]]-1]
        #            if curr_node.decoration == 0 or curr_node.decoration == 2:
        #                dest_pos = [0, op[1]]
        #            else:
        #                dest_pos = [0, op[1] + 4 * (1 if op[1]-(5*(curr_node.position-1)+7) > 0 else -1)]
#
        #        node_list = [[op[0] + 1, op[1]]] + self._expanded_bresenham(op[0], op[1], dest_pos[0], dest_pos[1]) + [[dest_pos[0]-1, dest_pos[1]]]
        #        path_matrix = [["│", "┌", "┐"],
        #                       ["└", "o", "─"],
        #                       ["┘", "─", "o"]]
        #        for path in range(1, len(node_list)-1, 1):  # draws path
        #            mat_prev = 0
        #            if node_list[path-1][0] - node_list[path][0] == 0:  # 0 = down
        #                mat_prev = [-1, 1, 2][node_list[path-1][1] - node_list[path][1]]  # 1 = right, 2 = left
        #            mat_next = 0
        #            if node_list[path][0] - node_list[path+1][0] == 0:  # 0 = up
        #                mat_next = [-1, 1, 2][node_list[path+1][1] - node_list[path][1]]  # 1 = right, 2 = left
        #            res[node_list[path][0]][node_list[path][1]] = path_matrix[mat_prev][mat_next]



        #   orig_pos = []
        res_str = ""
        for s in res:
            res_str += "".join(s) + "\n"
        return res_str

p = Permutation([3,7,5,2,1,4,6])
pt = LeveledPermutree(p, [Decoration.I,Decoration.Up,Decoration.I,Decoration.Up,Decoration.Down,Decoration.X,Decoration.Down])
print(pt._vertex_parents)
print(pt)