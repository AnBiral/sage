from sage.combinat.permutation import Permutation
from sage.all import *

class PermutreeNode():
    def __init__(self, decoration, position, level, children=None):
        if children is None:
            children = []

        self.decoration = decoration  # decorations are 0 = "I", 1 = "Up", 2 = "Down", 3 = "X"
        self.position = position
        self.level = level
        self.children = children    # child ordering is bottom left = 0, bottom right = 1, top left = 2, top right = 3
                                    # child content corresponds to number in permutation. -1 = no child.

        decoration_children_length = {0: 2, 1: 3, 2: 3, 3: 4}
        if decoration_children_length[self.decoration] < len(self.children):
            raise Exception("Amount of children should not exceed node capacity")

        self.children += [-1 for _ in range(decoration_children_length[self.decoration] - len(self.children))]

    def set_child(self, index, child_position):
        """
        Child position can either be self.children index, or string "t"/"tl"/"tr"/"b"/"bl"/"br"
        (top/top left/top right/bottom/bottom left/bottom right).
        If no top left/right exists, they are redirected to top. Same for bottom.
        """
        string_indexing = dict()

        idx = 0
        if self.decoration == 0 or self.decoration == 1:
            string_indexing["b"] = 0
            string_indexing["bl"] = 0
            string_indexing["br"] = 0
            idx += 1
        else:
            string_indexing["bl"] = 0
            string_indexing["br"] = 1
            idx += 2
        if self.decoration == 0 or self.decoration == 2:
            string_indexing["t"] = idx
            string_indexing["tl"] = idx
            string_indexing["tr"] = idx
        else:
            string_indexing["tl"] = idx
            string_indexing["tr"] = idx+1

        if type(child_position) is str:
            child_position = string_indexing[child_position]

        self.children[child_position] = index

    def get_child(self, child_position):
        # TODO: clean this up
        string_indexing = dict()

        idx = 0
        if self.decoration == 0 or self.decoration == 1:
            string_indexing["b"] = 0
            string_indexing["bl"] = 0
            string_indexing["br"] = 0
            idx += 1
        else:
            string_indexing["bl"] = 0
            string_indexing["br"] = 1
            idx += 2
        if self.decoration == 0 or self.decoration == 2:
            string_indexing["t"] = idx
            string_indexing["tl"] = idx
            string_indexing["tr"] = idx
        else:
            string_indexing["tl"] = idx
            string_indexing["tr"] = idx+1

        if type(child_position) is str:
            child_position = string_indexing[child_position]

        return self.children[child_position]

    def __str__(self):
        return f"id {self.position} | {self.children}"




class Permutree():
    def __init__(self, permutation: Permutation, decoration):
        self.perm = permutation
        self.dec = decoration
        if len(permutation) != len(decoration):
            raise Exception("Decoration and permutation have different lengths")

        self.leveling = self.perm.dict()

        self.walls = []
        self.calculate_walls()

        self.nodes = [PermutreeNode(self.dec[n], self.leveling[n+1], n+1) for n in range(len(self.dec))]

        self.insertion()

        self.print_walls = False

    def calculate_walls(self):
        """
        walls: [number in permutation, down wall, up wall]
        """
        for i in range(len(self.dec)):
            wall = [self.leveling[i+1], False, False]
            if self.dec[i] == 1 or self.dec[i] == 3:
                wall[2] = True
            if self.dec[i] == 2 or self.dec[i] == 3:
                wall[1] = True
            self.walls.append(wall)

    def insertion(self):
        perm_inv_dict = dict(zip(self.leveling.values(), self.leveling.keys()))

        active_regions = []  # region = [left wall, right wall, source number]
        current_region = 0
        for w in sorted(self.walls):
            if w[1] is True:
                active_regions.append([current_region, w[0], -1])
                current_region = w[0]
        active_regions.append([current_region, len(self.dec)+1, -1])

        for number in self.perm:
            new_regions = []
            old_regions = []
            for r in range(len(active_regions)):
                reg = active_regions[r]
                if reg[0] < number < reg[1]:  # Set bottom child of node
                    new_regions = [[active_regions[r][0], number, number], [number, reg[1], number]]
                    if self.dec[perm_inv_dict[number] - 1] == 0 :
                        new_regions = [[reg[0], reg[1], number]]
                    self.nodes[perm_inv_dict[number]-1].set_child(reg[2], 'b')
                if reg[0] == number:
                    if self.dec[perm_inv_dict[number] - 1] == 3:
                        new_regions.append([reg[0], reg[1], number])
                    elif len(new_regions) == 0:
                        new_regions.append([-1, reg[1], number])
                    else:
                        new_regions[0][1] = reg[1]
                    self.nodes[perm_inv_dict[number]-1].set_child(reg[2], 'br')
                if reg[1] == number:
                    if self.dec[perm_inv_dict[number] - 1] == 3:
                        new_regions.append([reg[0], reg[1], number])
                    elif len(new_regions) == 0:
                        new_regions.append([reg[0], -1, number])
                    else:
                        new_regions[0][0] = reg[0]
                    self.nodes[perm_inv_dict[number]-1].set_child(reg[2], 'bl')

                if reg[0] <= number <= reg[1]:
                    if reg[2] == reg[0]:  # Set top child of previous node
                        self.nodes[perm_inv_dict[reg[2]]-1].set_child(number, 'tr')
                    elif reg[2] == reg[1]:
                        self.nodes[perm_inv_dict[reg[2]]-1].set_child(number, 'tl')
                    elif reg[2] != -1:
                        self.nodes[perm_inv_dict[reg[2]]-1].set_child(number, 't')

                    old_regions.append(r)

            for r in sorted(old_regions, reverse=True):
                active_regions.pop(r)
            old_regions = []
            active_regions += new_regions

        for remaining_reg in active_regions:
            if remaining_reg[2] == remaining_reg[0]:  # Set top child of previous node
                self.nodes[perm_inv_dict[remaining_reg[2]] - 1].set_child(-1, 'tr')
            if remaining_reg[2] == remaining_reg[1]:
                self.nodes[perm_inv_dict[remaining_reg[2]] - 1].set_child(-1, 'tl')
            if remaining_reg[2] == remaining_reg[1] and remaining_reg[2] == remaining_reg[0]:
                self.nodes[perm_inv_dict[remaining_reg[2]] - 1].set_child(-1, 't')

    def rotation(self, index1, index2):
        # TODO: sort indices before rotating to save lines
        perm_inv_dict = dict(zip(self.leveling.values(), self.leveling.keys()))
        res = deepcopy(self)
        node_i = res.nodes[perm_inv_dict[index1]-1]
        node_j = res.nodes[perm_inv_dict[index2]-1]

        res.leveling[perm_inv_dict[index1]], res.leveling[perm_inv_dict[index2]] = res.leveling[perm_inv_dict[index2]], res.leveling[perm_inv_dict[index1]]
        p_list = list(res.perm)
        p_list[perm_inv_dict[index1] - 1], p_list[perm_inv_dict[index2] - 1] = p_list[perm_inv_dict[index2] - 1], p_list[perm_inv_dict[index1] - 1]
        res.perm = Permutation(p_list)
        res.dec[perm_inv_dict[index1] - 1], res.dec[perm_inv_dict[index2] - 1] = res.dec[perm_inv_dict[index2] - 1], res.dec[perm_inv_dict[index1] - 1]
        res.nodes = [PermutreeNode(res.dec[n], res.leveling[n+1], n+1) for n in range(len(res.dec))]
        res.insertion()

        if index2 not in node_i.children:
            raise Exception(f"Cannot rotate nodes {index1} and {index2}, as they are not adjacent")

        """
        if self.leveling[index1] < self.leveling[index2]:
            U = node_j.get_child("tl")
            D = node_i.get_child("br")
            node_i.set_child(U, "tr")
            node_i.set_child(index2, "br")
            node_j.set_child(D, "bl")
            node_j.set_child(index1, "tl")
            if U != -1:
                res.nodes[perm_inv_dict[U] - 1].children[res.nodes[perm_inv_dict[U] - 1].children.index(index2)] = index1
            if D != -1:
                res.nodes[perm_inv_dict[D] - 1].children[res.nodes[perm_inv_dict[D] - 1].children.index(index1)] = index2
        else:
            U = node_i.get_child("tr")
            D = node_j.get_child("bl")
            node_i.set_child(index2, "tr")
            node_i.set_child(D, "br")
            node_j.set_child(index1, "bl")
            node_j.set_child(U, "tl")
            if U != -1:
                res.nodes[perm_inv_dict[U] - 1].children[res.nodes[perm_inv_dict[U] - 1].children.index(index1)] = index2
            if D != -1:
                res.nodes[perm_inv_dict[D] - 1].children[res.nodes[perm_inv_dict[D] - 1].children.index(index2)] = index1
        
        res.leveling[perm_inv_dict[index1]], res.leveling[perm_inv_dict[index2]] = res.leveling[perm_inv_dict[index2]], res.leveling[perm_inv_dict[index1]]
        res.nodes[perm_inv_dict[index1]-1], res.nodes[perm_inv_dict[index2]-1] = res.nodes[perm_inv_dict[index2]-1], res.nodes[perm_inv_dict[index1]-1]
        p_list = list(res.perm)
        p_list[perm_inv_dict[index1] - 1], p_list[perm_inv_dict[index2] - 1] = p_list[perm_inv_dict[index2] - 1], p_list[perm_inv_dict[index1] - 1]
        res.perm = Permutation(p_list)
        res.dec[perm_inv_dict[index1] - 1], res.dec[perm_inv_dict[index2] - 1] = res.dec[perm_inv_dict[index2] - 1], res.dec[perm_inv_dict[index1] - 1]
        """

        return res





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

    def __str__(self):
        perm_inv_dict = dict(zip(self.leveling.values(), self.leveling.keys()))
        decoration_string = {0:"I", 1:"Y", 2:"⅄", 3:"X"}
        res = []
        res_str = ""
        res.append(["     " for _ in range(len(self.dec)+2)])
        for i in range(len(self.dec)):
            res.append(["     " for _ in range(len(self.dec)+2)])
            res.append(["     " for _ in range(len(self.dec)+2)])

        for n in self.nodes:  # Add nodes
            if n.level != -1 and n.position != -1:
                res[(len(self.dec)-n.level)*2+1][n.position] = " (" + decoration_string[n.decoration] + ") "

        for l in range(len(res)):  # Transform into list of characters
            res_str = ""
            for c in res[l]:
                res_str += c
            res[l] = list(res_str)


        orig_pos = []
        if self.print_walls:
            for w in self.walls:
                wall_node = self.nodes[perm_inv_dict[w[0]] - 1]
                if w[1]:
                    for i in range((len(self.dec) - wall_node.level) * 2 + 2, 2*len(self.dec)+1, 1):
                        res[i][5 * (wall_node.position - 1) + 7] = '╵'
                elif w[2]:
                    for i in range(0, (len(self.dec) - wall_node.level) * 2+1, 1):
                        res[i][5 * (wall_node.position - 1) + 7] = '╵'

        orig_pos = []  # list of [orig_y, orig_x, origin_node, destination_node]
        for n in self.nodes:
            if n.get_child("bl") == -1 or n.get_child("br") == -1:
                if n.decoration == 0 or n.decoration == 1:
                    orig_pos.append([(len(self.dec) - n.level) * 2 + 2, 5 * (n.position - 1) + 7, -1, n.position])
                else:
                    for b in ["bl", "br"]:
                        if n.get_child(b) == -1:
                            orig_pos.append([(len(self.dec)-n.level)*2 + 2, 5*(n.position-1)+(6 if b == "bl" else 8), -1, n.position])
            if n.decoration == 0 or n.decoration == 2:
                orig_pos.append([(len(self.dec)-n.level)*2, 5*(n.position-1)+7, n.position, n.get_child("t")])
            else:
                for t in ["tl", "tr"]:
                    orig_pos.append([(len(self.dec)-n.level)*2, 5*(n.position-1)+(6 if t == "tl" else 8), n.position, n.get_child(t)])

            for op in orig_pos:
                if op[2] == -1:  # Case for down into the void
                    curr_node = self.nodes[perm_inv_dict[op[3]]-1]
                    if curr_node.decoration == 0 or curr_node.decoration == 1:
                        dest_pos = [2*len(self.dec), op[1]]
                    else:
                        dest_pos = [2*len(self.dec), op[1] + 4 * (1 if op[1]-(5*(curr_node.position-1)+7) > 0 else -1)]
                    dest_pos, op = op, dest_pos

                elif op[3] != -1:
                    dest_node = self.nodes[perm_inv_dict[op[3]]-1]
                    if dest_node.decoration == 0 or dest_node.decoration == 1:
                        dest_pos = (len(self.dec) - dest_node.level) * 2 + 2, 5 * (dest_node.position-1) + 7
                    else:
                        dest_pos = (len(self.dec) - dest_node.level) * 2 + 2, 5 * (dest_node.position-1) + (6 if dest_node.get_child("bl") == op[2] else 8)

                else:  # Case for up into the void
                    curr_node = self.nodes[perm_inv_dict[op[2]]-1]
                    if curr_node.decoration == 0 or curr_node.decoration == 2:
                        dest_pos = [0, op[1]]
                    else:
                        dest_pos = [0, op[1] + 4 * (1 if op[1]-(5*(curr_node.position-1)+7) > 0 else -1)]

                node_list = [[op[0] + 1, op[1]]] + self._expanded_bresenham(op[0], op[1], dest_pos[0], dest_pos[1]) + [[dest_pos[0]-1, dest_pos[1]]]
                path_matrix = [["│", "┌", "┐"],
                               ["└", "o", "─"],
                               ["┘", "─", "o"]]
                for path in range(1, len(node_list)-1, 1):  # draws path
                    mat_prev = 0
                    if node_list[path-1][0] - node_list[path][0] == 0:  # 0 = down
                        mat_prev = [-1, 1, 2][node_list[path-1][1] - node_list[path][1]]  # 1 = right, 2 = left
                    mat_next = 0
                    if node_list[path][0] - node_list[path+1][0] == 0:  # 0 = up
                        mat_next = [-1, 1, 2][node_list[path+1][1] - node_list[path][1]]  # 1 = right, 2 = left
                    res[node_list[path][0]][node_list[path][1]] = path_matrix[mat_prev][mat_next]



            orig_pos = []



        res_str = ""
        for s in res:
            res_str += "".join(s) + "\n"
        return res_str



class Permutree_Rotation_Graph():
    pass


def min_transposition_distance(p: Permutation, p2, depth=0):
    if p == p2:
        return 0
    if depth == p.size():
        return p.size() + 1
    min = p.size() + 1
    for a in p.permutohedron_pred() + p.permutohedron_succ():
        dst = min_transposition_distance(a, p2, depth+1)
        if dst < min:
            min = dst
        if dst == 0:
            break
    return min + 1



p = Permutation([3,7,5,2,1,4,6])
print(list(p))
#pt = Permutree(p, [1, 1, 0, 2, 0, 3, 2])
#print(pt)

pt = Permutree(p, [0,1,0,1,2,3,2])
print(pt._expanded_bresenham(2, 4, 6,8))
print(pt)
pt2 = pt.rotation(2, 3)
print(pt2)
pt3 = pt.rotation(4, 6)
print(pt3)
