import math
import random
import copy
import bisect
import queue
import numpy

class board:
    def __init__(self):
        self.pointcalc = [0, 40, 100, 300, 1200]
        self.weights = (5.06450279, -0.40483617,  1.14291331,  1.83894321,  0.18530122, 0.35860931,  0.93125075,  0.23497438)
        self.survweights = (1.72746616e+00,  1.18972449e-02,  4.54023544e-01,  4.19517578e-01,1.46628694e-03, -2.19499807e-01,  5.36884577e-01, -4.83240272e-01)
        #board data
        self.heights = [0] * 10
        self.ones = [0] * 10
        self.grid = [0] * 24 #each row is an integer
        self.rowTrans = [0] * 24
        self.alive = 1
        #heuristic variables
        self.holes = 0
        self.avgHeight = 0
        self.maxHeight = 0
        self.bumpiness = 0
        self.newl = 0 #new lines in this move
        self.wellCells = 0
        self.deepWells = 0
        self.blocks = 0
        #scoring variables
        self.lines = 0
        self.pts = 0
    def col(self, x, y, piece): #checks collision
        for i in piece:
            if y + i[1] < 0 or x + i[0] >= 10 or x + i[0] < 0:
                return True
            if y + i[1] >= 20:
                continue
            if self.grid[y + i[1]] & (1<<(x + i[0])):
                return True
        return False
    def countrowTrans(self, row):
        v = self.grid[row]
        ret = 0
        state = (v & 1) == 1
        for i in range(10):
            if v & 1:
                if not state:
                    ret += 1
                state = True
            else:
                if state:
                    ret += 1
                state = False
            v >>= 1
        return ret
    def place (self, x, y, piece, type): #places piece
        if type:
            for i in piece:
                self.grid[y + i[1]] |= 1<<(x + i[0])
                self.ones[x + i[0]] += 1
                if y + i[1] + 1 > self.heights[x + i[0]]:
                    self.heights[x + i[0]] = y + i[1] + 1
                    self.maxHeight = max(self.maxHeight, self.heights[x + i[0]])
                self.rowTrans[y + i[1]] = self.countrowTrans(y + i[1])
            self.blocks += 4
            # for i in piece:
            #     self.wellCells += self.iswell(x + i[0] - 1, y + i[1]) + self.iswell(x + i[0] + 1, y + i[1])
        else:
            for i in piece:
                self.grid[y + i[1]] ^= 1<<(x + i[0])
    def checkline(self): #checks for filled lines and updates board position
        self.newl = 0
        recalc = False
        for i in range(19, -1, -1):
            if self.grid[i] == 1023:
                recalc = True
                self.newl += 1
                for j in range(i, 23):
                    self.grid[j] = self.grid[j + 1]
                    self.rowTrans[j] = self.rowTrans[j + 1]
                self.blocks -= 10
        self.lines += self.newl
        self.pts += (int(max(self.lines - 120, 0) / 10) + 19) * self.pointcalc[self.newl]
        for i in range(10):
            self.ones[i] -= self.newl
        if recalc:
            self.getstats()
    def put(self, x, piece): #puts piece down according to rotation and position
        for y in range(19, -2, -1):
            if self.col(x, y, piece):
                if y + 1 >= 20:
                    self.alive = 0
                self.place(x, y + 1, piece, 1)
                self.checkline()
                return
    def printboard(self): #prints current board for debugging
        for i in range(19, -1, -1):
            for j in range(10):
                if self.grid[i] & (1 << j):
                    print(1, end="")
                else:
                    print(0, end="")
            print()
        print()
    def getstats(self): #completely refreshes stats by checking entire board (only called when lines are cleared)
        maxh = 0
        for i in range(10):
            found = False
            for j in range(19, -1, -1):
                if self.grid[j] & (1 << i):
                    found = True
                    self.heights[i] = j + 1
                    break
            maxh = max(maxh, self.heights[i])
            if not found:
                self.heights[i] = 0
        self.maxHeight = maxh
        self.getval()
    def getval(self): #the evaluation function
        self.bumpiness, self.avgHeight, self.holes, self.deepWells, self.wellCells = 0, 0, 0, 0, 0
        for i in range(1, 9):
            self.bumpiness += (abs(self.heights[i] - self.heights[i + 1]) + 1) * (abs(self.heights[i] - self.heights[i - 1]) + 1)
        for i in range(10):
            self.holes += int(math.sqrt(max(0, self.heights[i] - self.ones[i])))
            isdeep = True
            dif = 1000
            if i > 0:
                isdeep &= self.heights[i] < self.heights[i - 1] - 3
                dif = min(dif, self.heights[i - 1] - self.heights[i])
            if i < 9:
                isdeep &= self.heights[i] < self.heights[i + 1] - 3
                dif = min(dif, self.heights[i + 1] - self.heights[i])
            if isdeep:
                self.deepWells += 1
            self.wellCells += max(0, dif)
        self.bumpiness /= 7
        self.avgHeight = sum(self.heights) / 10
        totalrowtrans = sum(self.rowTrans)
        if self.alive:
            if self.maxHeight <= 13:
                return self.weights[0] * self.holes + self.weights[1] * self.bumpiness + self.weights[2] * (max(7, self.maxHeight) - 7) \
                       + self.weights[3] * (-self.newl) + self.weights[4] * self.wellCells + self.weights[5] * self.deepWells + \
                       self.weights[6] * totalrowtrans + self.weights[7] * -self.blocks + 0.1 * self.avgHeight
            else:
                return self.survweights[0] * self.holes + self.survweights[1] * self.bumpiness + self.survweights[2] * (
                            max(7, self.maxHeight) - 7) \
                       + self.survweights[3] * (-self.newl) + self.survweights[4] * self.wellCells + self.survweights[
                           5] * self.deepWells + \
                       self.survweights[6] * totalrowtrans + self.survweights[7] * -self.blocks + 0.1 * self.avgHeight
        else:
            return 999


class piece:
    def __init__(self, p, num):
        self.tile = [] #stores representation of different tile rotations
        self.types = num
        self.tile.append(copy.deepcopy(p))
        self.minx = []
        self.maxx = []
        if num == 1:
            return
        for i in p:
            save = i[0]
            i[0] = -i[1]
            i[1] = save
        self.tile.append(copy.deepcopy(p))
        if num == 2:
            return
        for i in p:
            i[0] *= -1
            i[1] *= -1
        self.tile.append(copy.deepcopy(p))
        for i in p:
            save = i[0]
            i[0] = i[1]
            i[1] = -save
        self.tile.append(copy.deepcopy(p))
    def getbounds(self):
        for i in self.tile:
            minx, maxx = 0, 0
            for j in i:
                minx = min(minx, j[0])
                maxx = max(maxx, j[0])
            self.minx.append(minx * -1)
            self.maxx.append(9 - maxx)

#all seven tetris pieces
tet = [piece([[0, 0], [0, 1], [0, 2], [0, 3]], 2),
       piece([[0, 0], [0, 1], [1, 1], [1, 0]], 1),
       piece([[0, 0], [1, 0], [0, 1], [0, 2]], 4),
       piece([[0, 0], [1, 0], [1, 1], [1, 2]], 4),
       piece([[0, 0], [1, 0], [1, 1], [2, 1]], 2),
       piece([[0, 0], [0, 1], [1, 1], [1, 2]], 2),
       piece([[0, 0], [0, 1], [0, 2], [1, 1]], 4), ] #I, O, L, J, S, Z, T
for i in tet:
    i.getbounds()

#generating test data
testcases = []
def gettestdata(cases):
    global testcases
    testcases = []
    for i in range(cases):
        testcases.append([])
        for j in range(1000):
            testcases[i].append(random.randint(0, 6))

#ai move
avgpts, avglines = 0, 0
def move(gameboard, piece, nextp, pnt, ty):
    cur = piece
    nextpiece = nextp
    values = []
    best = 1500
    bestrot, bestpos = 0, 0
    for i in range(cur.types):  # for each rotation
        for j in range(cur.minx[i], cur.maxx[i] + 1):  # possible placements
            result = copy.deepcopy(gameboard)
            result.put(j, cur.tile[i])
            resval = result.getval()
            if result.newl == 4:
                bestrot, bestpos = i, j
                best = -999
                resval = -999
            if ty == 0:
                if resval < best:
                    best = resval
                    bestrot, bestpos = i, j
            else:
                if bisect.bisect_left(values, resval) <= len(values) / 3 or len(values) < 10:
                    m = 1000
                    for i2 in range(nextpiece.types):
                        for j2 in range(nextpiece.minx[i2], nextpiece.maxx[i2] + 1):
                            res2 = copy.deepcopy(result)
                            res2.put(j2, nextpiece.tile[i2])
                            rv = res2.getval()
                            if res2.newl == 4:
                                rv = -900
                            if rv < m:
                                m = rv
                    if m < best:
                        best = m
                        bestrot, bestpos = i, j
                bisect.insort(values, resval)
            # print(result.bumpiness)
    if ty <= 1:
        gameboard.put(bestpos, cur.tile[bestrot])
    gameboard.getstats()
    if gameboard.alive == 0 or gameboard.lines >= 230:
        return;
    return (bestrot, bestpos)

#getting average score for some parameters
def score(param, type):
    global testcases, avgpts, avglines
    pnt = 0
    limit = 230
    for x in testcases:
        gameboard = board()
        gameboard.weights = param
        cnt = 0
        while gameboard.alive and gameboard.lines < 230:
            move(gameboard, tet[x[cnt]], tet[x[cnt + 1]], pnt, type)
            gameboard.getstats()
            cnt += 1
        avgpts += gameboard.pts
        avglines += gameboard.lines
        pnt += gameboard.pts
        if type:
            print(gameboard.pts)

    return pnt / len(testcases)


# gettestdata(50)
# print(score((5.06450279, -0.40483617,  1.14291331,  1.83894321,  0.18530122, 0.35860931,  0.93125075,  0.23497438), 1))
#
# print("Average lines: ", avglines / 50)
# print("Average points: ", avgpts / 50)
'''
#Genetic Algorithm
pop = []
size = 50
tabugen = 3
clancnt = 0
for i in range(size):
    pop.append([numpy.array(list(random.uniform(-1, 1) for i in range(8))), clancnt, [], numpy.array(list(random.uniform(-1, 1) for i in range(8))), 1])
    # individual: weights forming a chromosome, the clan number, tabu list, memetic vector for local optimization, memetic scalar
    clancnt += 1

for gen in range(100):
    print("Generation ", gen + 1, sep='')
    print(pop)
    gettestdata(20)
    res = []
    c = 0
    for individual in pop:
        val = score(individual[0], 0)
        #print(individual[0], individual[3], individual[4])
        for step in range(5):
            newparam = numpy.add(individual[0], numpy.multiply(numpy.divide(individual[3], numpy.linalg.norm(individual[3])), individual[4]))
            localval = score(newparam, 0)
            if localval > val:
                val = localval
                individual[0] = newparam
                individual[4] *= 0.9
            else:
                if step == 0:
                    individual[3] = numpy.array(list(random.random() for i in range(8)))
                break
        #print(individual[0])
        res.append((val, individual))
        print(val, end=" ")
        c += 1
    res = sorted(res, key= lambda x: x[0])
    res.reverse()
    print()
    print(res[0])
    s = sum(list(a[0] for a in res))
    pop = []
    valid = 0
    count = 0
    while valid < size - 1:
        count += 1
        p1, p2 = [], [] #selects p1 and p2 as parents
        s1, s2 = 0, 0
        r = random.uniform(0, s - 0.01)
        n = 0
        for j in range(len(res)):
            n += res[j][0]
            if n > r:
                p1 = res[j][1]
                s1 = res[j][0]
                break

        r = random.uniform(0, s - 0.01)
        n = 0
        for j in range(len(res)):
            n += res[j][0]
            if n > r:
                p2 = res[j][1]
                s2 = res[j][0]
                break
        #print(p1, p2)
        tabu = False #checks if match is tabu/
        if p1[1] == p2[1]:
            tabu = True
        for clan in p1[2]:
            if p2[1] == clan:
                tabu = True
        for clan in p2[2]:
            if p1[1] == clan:
                tabu = True
        #print(tabu)
        if tabu:
            if count > 10000:
                for j in range(len(res)):
                    res[j][1][2] = []
                    res[j][1][1] = clancnt
                    clancnt += 1
                print(res)
            continue
        else:
            valid += 2

        child1, child2 = [numpy.array([0.0] * 8), p1[1], copy.deepcopy(p1[2])], [numpy.array([0.0] * 8), p2[1], copy.deepcopy(p2[2])]

        for j in range(8):
            if random.random() < 0.5:
                child1[0][j] = p1[0][j]
                child2[0][j] = p2[0][j]
            else:
                child1[0][j] = p2[0][j]
                child2[0][j] = p1[0][j]
            if random.random() < 0.07122: #mutation
                if random.randint(0, 1) == 0:
                    child1[0][j] += random.uniform(-0.5/(gen + 1), 0.5/(gen + 1))
                else:
                    child2[0][j] += random.uniform(-0.5/(gen + 1), 0.5/(gen + 1))

        child1[2].append(child2[1]) #adds each other to tabu list
        child2[2].append(child1[1])
        while len(child1[2]) > tabugen:
            child1[2].pop(0)
        while len(child2[2]) > tabugen:
            child2[2].pop(0)

        if s1 > s2:
            child1.append(p1[3])
            child1.append(p1[4])
            child2.append(p1[3])
            child2.append(p1[4])
        else:
            child1.append(p2[3])
            child1.append(p2[4])
            child2.append(p2[3])
            child2.append(p2[4])

        pop.append(child1)
        if valid < size - 1:
            pop.append(child2)
    pop.append(res[0][1])
    clancnt += 1
'''
#[[[0.5120815834113909, 0.3568590863062684, 0.0017964894856954405, 0.2905304023008368], 7, [36, 14, 22]], [[0.5120815834113909, 0.20272830530657449, 0.0017964894856954405, 0.4235616428775391], 22, [11, 45, 7]], [[0.5120815834113909, 0.3638913042158495, 0.0017964894856954405, 0.2905304023008368], 22, [2, 36, 11]], [[0.5120815834113909, 0.3568590863062684, -0.016209773130931332, 0.42333329503014483], 11, [7, 19, 22]], [[0.9140729603910726, 0.3638913042158495, 0.018591678554635727, 0.42333329503014483], 2, [45, 36, 11]], [[0.5120815834113909, 0.3568590863062684, 0.07076573439810366, 0.4410430971553432], 11, [7, 19, 2]], [[0.7740458161453696, 0.20272830530657449, 0.0017964894856954405, 0.2905304023008368], 2, [36, 19, 7]], [[0.9140729603910726, 0.3638913042158495, 0.0017964894856954405, 0.01158306538204823], 7, [45, 11, 2]], [[0.49699922264082763, 0.3568590863062684, 0.0017964894856954405, 0.42333329503014483], 11, [30, 45, 2]], [[0.9140729603910726, 0.3638913042158495, 0.0017964894856954405, 0.07661989714436501], 2, [14, 7, 11]], [[0.9140729603910726, 0.3568590863062684, 0.07076573439810366, 0.01158306538204823], 11, [7, 19, 22]], [[0.5120815834113909, 0.3568590863062684, -0.012961139637447334, 0.42333329503014483], 22, [19, 2, 11]], [[0.9140729603910726, 0.20272830530657449, 0.0017964894856954405, 0.2905304023008368], 14, [2, 45, 36]], [[0.5120815834113909, 0.3568590863062684, 0.0017964894856954405, 0.3380433380277704], 36, [22, 11, 14]], [[0.5120815834113909, 0.3638913042158495, 0.0017964894856954405, 0.4287038060432591], 19, [22, 2, 11]], [[0.5120815834113909, 0.3568590863062684, 0.0017964894856954405, 0.40154741071360334], 11, [14, 36, 19]], [[0.49699922264082763, 0.20272830530657449, 0.0017964894856954405, -0.03265961683079752], 11, [30, 45, 2]], [[0.7740458161453696, 0.3638913042158495, 0.0017964894856954405, 0.07661989714436501], 2, [36, 19, 11]], [[0.5120815834113909, 0.3638913042158495, 0.0017964894856954405, 0.3204453254296826], 2, [14, 7, 30]], [[0.9140729603910726, 0.3568590863062684, 0.0017964894856954405, 0.42333329503014483], 30, [11, 14, 2]], [[0.9140729603910726, 0.3568590863062684, 0.0017964894856954405, 0.3824193612162917], 14, [2, 45, 36]], [[0.8273733732094635, 0.3568590863062684, 0.0017964894856954405, 0.2905304023008368], 36, [45, 2, 14]], [[0.8312480236896608, 0.3638913042158495, 0.0017964894856954405, 0.2905304023008368], 45, [2, 14, 36]], [[0.7740458161453696, 0.1823271727302449, 0.0017964894856954405, 0.40154741071360334], 36, [19, 22, 45]], [[0.49699922264082763, 0.3638913042158495, 0.0017964894856954405, 0.07661989714436501], 2, [45, 36, 11]], [[0.9140729603910726, 0.3638913042158495, 0.07076573439810366, 0.40154741071360334], 11, [30, 45, 2]], [[0.9300627676125302, 0.3638913042158495, 0.07076573439810366, 0.3824193612162917], 2, [45, 36, 14]], [[0.9140729603910726, 0.7223076148810849, 0.0017964894856954405, 0.40154741071360334], 14, [11, 45, 2]], [[0.8415949690559933, 0.20272830530657449, 0.0017964894856954405, 0.32576138915238584], 19, [22, 11, 36]], [[0.5120815834113909, 0.20272830530657449, 0.1428950280661342, 0.40154741071360334], 36, [22, 2, 19]], [[0.8312480236896608, 0.20272830530657449, 0.0017964894856954405, 0.2905304023008368], 19, [22, 11, 45]], [[0.5120815834113909, 0.3638913042158495, 0.0017964894856954405, 0.01158306538204823], 45, [2, 14, 19]], [[0.5120815834113909, 0.20272830530657449, 0.0017964894856954405, 0.2905304023008368], 45, [2, 22, 19]], [[0.8620221354977, 0.3638913042158495, 0.0017964894856954405, 0.01158306538204823], 19, [22, 11, 45]], [[0.9140729603910726, 0.4018282223920616, 0.0017964894856954405, 0.3824193612162917], 14, [2, 45, 7]], [[0.9297065618484807, 0.3568590863062684, 0.0017964894856954405, 0.2905304023008368], 7, [2, 36, 14]], [[0.9140729603910726, 0.3568590863062684, 0.0017964894856954405, 0.2905304023008368], 45, [36, 11, 22]], [[0.9936915610783116, 0.3568590863062684, 0.07076573439810366, 0.01158306538204823], 22, [19, 2, 45]], [[0.5120815834113909, 0.20272830530657449, 0.0017964894856954405, 0.3824193612162917], 36, [22, 11, 2]], [[0.7740458161453696, 0.20272830530657449, 0.1428950280661342, 0.3380433380277704], 2, [45, 22, 36]], [[0.8415949690559933, 0.20272830530657449, 0.0017964894856954405, 0.40154741071360334], 19, [22, 11, 36]], [[0.5120815834113909, 0.20272830530657449, 0.1428950280661342, 0.01158306538204823], 36, [22, 2, 19]], [[0.5120815834113909, 0.20272830530657449, 0.0017964894856954405, 0.3380433380277704], 36, [22, 11, 19]], [[0.5120815834113909, 0.20272830530657449, 0.0017964894856954405, 0.01158306538204823], 19, [22, 11, 36]], [[0.7740458161453696, 0.20272830530657449, 0.1428950280661342, 0.07661989714436501], 2, [45, 22, 11]], [[0.49699922264082763, 0.3638913042158495, 0.0017964894856954405, 0.3824193612162917], 11, [30, 45, 2]], [[0.5120815834113909, 0.3638913042158495, 0.0017964894856954405, 0.07661989714436501], 45, [2, 14, 19]], [[0.9140729603910726, 0.20272830530657449, 0.0017964894856954405, 0.32576138915238584], 19, [22, 11, 45]], [[0.49699922264082763, 0.3638913042158495, 0.0017964894856954405, 0.4264884950363803], 2, [14, 36, 11]], [[0.7740458161453696, 0.3638913042158495, 0.0017964894856954405, 0.40154741071360334], 2, [36, 45, 22]]]

#2.71272415, 0.15215891, 0.08104456, 0.92096303, 0.0415802 ,0.65177485, 0.04188228
#2.09392989, 0.05191848, 0.43117246, 0.54843443, 0.07827848, 0.10796015, 0.03869007, 0.04661041
#5.06450279, -0.40483617,  1.14291331,  1.83894321,  0.18530122, 0.35860931,  0.93125075,  0.23497438
#3.51257442, -0.3457632 ,  0.52339586, -1.47081766,  0.37722158,0.07432846,  0.84031976, -0.02831209
