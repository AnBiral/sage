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

        self._calculate_walls()
        self.insertion(permutation)

    def _calculate_walls(self):
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

    def rotation(self, i, j):
        """
        Rotates permutree vertices at horizontal index i and j
        """
        for k, v in self._vertex_parents.items():
            self._vertex_parents[k] = sorted(v)
            if len(v) > 1 and v[0] == -1 and v[1] < k:
                v[0], v[1] = v[1], v[0]

        if i in self._vertex_parents[j]:
            i, j = j, i
        if i in self._vertex_parents[j]:
            return  # Does nothing if vertices are non-adjacent
        index = self._vertex_parents[i].index(j)
        U = self._vertex_parents[j][0 if i < j or self._decorations[j].parent_count() == 1 else 1]
        U_index = self._vertex_parents[j].index(U)
        D = -1
        D_index = -1

        for k, v in self._vertex_parents.items():
            if ((i in v and (k > i or self._decorations[i].child_count() == 1) and i < j) or
                    (i in v and (k < i or self._decorations[i].child_count() == 1) and i > j)):
                D = k
                D_index = v.index(i)

        self._vertex_parents[i][index] = U
        self._vertex_parents[j][U_index] = i
        if D != -1:
            self._vertex_parents[D][D_index] = j

        for k, v in self._vertex_parents.items():
            self._vertex_parents[k] = sorted(v)




class LeveledPermutree(Permutree):
    def __init__(self, permutation: Permutation, decoration):
        Permutree.__init__(self, permutation, decoration)

        self._underlying_permutation = permutation

    def rotation(self, i, j):
        if j in self._vertex_parents[i] or i in self._vertex_parents[j]:
            permutation_list = list(self._underlying_permutation)
            i_index = self._underlying_permutation.index(i)
            j_index = self._underlying_permutation.index(j)
            permutation_list[j_index], permutation_list[i_index] = permutation_list[i_index], permutation_list[j_index]
            self._underlying_permutation = Permutation(permutation_list)
            Permutree.rotation(self, i, j)

    def _expanded_bresenham(self, y1, x1, y2, x2):  # TODO: Find a way to reduce or remove this
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
        reverse_level = dict(zip(level.values(), level.keys()))
        decoration_string = {Decoration.I:"I", Decoration.Down:"⅄", Decoration.Up:"Y", Decoration.X:"X"}
        res = []
        res_str = ""
        res.append(["     " for _ in range(self.size+2)])
        for i in range(self.size):
            res.append(["     " for _ in range(self.size+2)])
            res.append(["     " for _ in range(self.size+2)])

        for n in range(1, self.size+1, 1):  # Add nodes
            res[(self.size-reverse_level[n])*2+1][n] = " (" + decoration_string[self._decorations[n]] + ") "

        for l in range(len(res)):  # Transform into list of characters
            res_str = ""
            for c in res[l]:
                res_str += c
            res[l] = list(res_str)

        paths_to_draw = []
        bottom_connections = {i:[0,0] for i in range(1, self.size + 1, 1)}
        for nb, parents in self._vertex_parents.items():
            for p in parents:
                if p != -1:  # Connections between vertices
                    bottom_connections[p][0 if p > nb else 1] = 1
                    offsets = [0, 0]
                    if self._decorations[nb] == Decoration.X or self._decorations[nb] == Decoration.Up:
                        offsets[0] = -1 if p < nb else 1
                    if self._decorations[p] == Decoration.X or self._decorations[p] == Decoration.Down:
                        offsets[1] = 1 if p < nb else -1
                    paths_to_draw.append(self._expanded_bresenham( (2*(self.size-reverse_level[nb])),
                                                                   5*(nb-1) + 7 + offsets[0],
                                                                   (2*(self.size-reverse_level[p]+1)),
                                                                   5*(p-1) + 7 + offsets[1]))
                else:  # Connections between vertices and empty space above
                    if len(parents) == 1:  # I/Down decoration with no parents
                        paths_to_draw.append(self._expanded_bresenham((2 * (self.size - reverse_level[nb])),
                                                                      5 * (nb - 1) + 7,
                                                                      0,
                                                                      5 * (nb - 1) + 7))
                    elif parents[1] == -1:  # X/Up decoration with no parents
                        paths_to_draw.append(self._expanded_bresenham((2 * (self.size - reverse_level[nb])),
                                                                      5 * (nb - 1) + 6,
                                                                      0,
                                                                      5 * (nb - 2) + 7))
                        paths_to_draw.append(self._expanded_bresenham((2 * (self.size - reverse_level[nb])),
                                                                      5 * (nb - 1) + 8,
                                                                      0,
                                                                      5 * (nb) + 7))
                        break
                    else:
                        offset = 1 if parents[1] < nb else -1
                        paths_to_draw.append(self._expanded_bresenham((2 * (self.size - reverse_level[nb])),
                                                                      5 * (nb - 1) + 7 + offset,
                                                                      0,
                                                                      5 * (nb - 1 + offset) + 7))
        for nb, children in bottom_connections.items():
            if self._decorations[nb].child_count() == 1 and sum(children) == 0:
                paths_to_draw.append(self._expanded_bresenham((2 * (self.size - reverse_level[nb]) + 2),
                                                              5 * (nb - 1) + 7,
                                                              2*self.size,
                                                              5 * (nb - 1) + 7))
            elif self._decorations[nb].child_count() == 2 and children[0] == 0:
                paths_to_draw.append(self._expanded_bresenham(2*self.size,
                                                              5 * (nb - 2) + 7,
                                                              (2 * (self.size - reverse_level[nb]) + 2),
                                                              5 * (nb - 1) + 6))
            elif self._decorations[nb].child_count() == 2 and children[1] == 0:
                paths_to_draw.append(self._expanded_bresenham(2*self.size,
                                                              5 * (nb) + 7,
                                                              (2 * (self.size - reverse_level[nb]) + 2),
                                                              5 * (nb - 1) + 8))



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

        print(bottom_connections)
        res_str = ""
        for s in res:
            res_str += "".join(s) + "\n"
        return res_str


#  For testing

#p = Permutation([3,7,5,2,1,4,6])
#pt = LeveledPermutree(p, [Decoration.I,Decoration.Up,Decoration.I,Decoration.Up,Decoration.Down,Decoration.X,Decoration.Down])
#
#print(pt._vertex_parents)
#print(pt)
#
#pt.rotation(1,2)
#print(pt)
#print(pt._vertex_parents)
