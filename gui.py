import main
import pygame
import math, time, os

pygame.init()
pygame.font.init()
def load_image(name):
    fullname = os.path.join("assets", name)
    image = pygame.image.load(fullname)
    return image

screen = pygame.display.set_mode((800, 800)) #game board is 350x700
BGColor = (171, 171, 171)

font = pygame.font.Font("fonts/GeosansLight.ttf", 30)

clock = pygame.time.Clock()
fps = 60
running = True

offimg = pygame.transform.scale(load_image("black.png"), (34, 34))
onimg = pygame.transform.scale(load_image("white.png"), (34, 34))

game = main.board()
main.gettestdata(1)
mode = 0 # 0: drop, 1:fall
cnt = 0
rot, pos, y = 0, 0, 20
points = 0
speed = 100


while running:
    screen.fill(BGColor)
    time.sleep(1 / speed)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            pygame.quit()
            exit()

    for i in range(0, 20):
        for j in range(10):
            if game.grid[i] & (1<<j):
                screen.blit(onimg, (300 + j * 35, 750 - i * 35))
            else:
                screen.blit(offimg, (300 + j * 35, 750 - i * 35))
    if game.alive and game.lines < 230:
        if mode == 0:
            rot, pos = main.move(game, main.tet[main.testcases[0][cnt]], main.tet[main.testcases[0][cnt + 1]], points, 2)
            #rot, pos = main.move(game, main.tet[4], main.tet[4], points, 2)
            mode = 1
            y = 20
        else:
            arr = main.tet[main.testcases[0][cnt]].tile[rot]
            #arr = main.tet[4].tile[rot]
            if not game.col(pos, y, arr):
                for i in arr:
                    screen.blit(onimg, (300 + (pos + i[0]) * 35, 750 - (y + i[1]) * 35))
                y -= 1
            else:
                if y + 1 >= 20:
                    game.alive = 0
                game.place(pos, y + 1, arr, 1)
                game.checkline()
                y = 20
                mode = 0
                cnt += 1

    scoretxt = font.render("Score: " + str(game.pts), False, (0, 0, 0))
    linetxt = font.render("Lines: " + str(game.lines), False, (0, 0, 0))
    leveltxt = font.render("Level: " + str(int(max(game.lines - 120, 0) / 10) + 18), False, (0,0,0))
    nextpiecetxt = font.render("Next Piece: ", False, (0,0,0))
    for i in main.tet[main.testcases[0][cnt + 1]].tile[0]:
        screen.blit(onimg, (100 + i[0] * 35, 500 - i[1] * 35))
    # for i in main.tet[6].tile[cnt % 4]:
    #     screen.blit(onimg, (100 + i[0] * 35, 500 - i[1] * 35))
    screen.blit(scoretxt, (75, 100))
    screen.blit(linetxt, (75, 175))
    screen.blit(leveltxt, (75, 250))
    screen.blit(nextpiecetxt, (75, 325))

    pygame.display.update()
