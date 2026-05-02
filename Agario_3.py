from math import hypot
from socket import *
import pygame
from threading import Thread
from random import randint
import time

# 🔌 підключення (сервер НЕ змінюємо)
sock = socket(AF_INET, SOCK_STREAM)
sock.connect(("5.tcp.eu.ngrok.io", 29958))

my_data = list(map(int, sock.recv(64).decode().strip().split(',')))

my_id = my_data[0]
my_player = my_data[1:]

sock.setblocking(False)

# 🟢 pygame init
pygame.init()
win = pygame.display.set_mode((800, 800))
clock = pygame.time.Clock()
font = pygame.font.Font(None, 50)

MAP_SIZE = 2000

all_players = []
running = True
lose = False

# 🧠 анти-баг
eaten_players = set()
last_eat_time = 0
EAT_COOLDOWN = 0.3


def receive_data():
    global all_players, lose
    while running:
        try:
            data = sock.recv(4096).decode().strip()
            if data == "LOSE":
                lose = True
            elif data:
                parts = data.strip('|').split('|')
                all_players = [list(map(int, p.split(','))) for p in parts if len(p.split(',')) == 4]
        except:
            pass


Thread(target=receive_data, daemon=True).start()


class Eat:
    def __init__(self, x, y, r, c):
        self.x = x
        self.y = y
        self.radius = r
        self.color = c

    def check_collision(self, px, py, pr):
        return hypot(self.x - px, self.y - py) <= self.radius + pr


# 🍎 їжа
eats = [Eat(randint(-MAP_SIZE, MAP_SIZE),
            randint(-MAP_SIZE, MAP_SIZE),
            10,
            (randint(0, 255), randint(0, 255), randint(0, 255)))
        for _ in range(300)]


def can_eat(p1, p2):
    dx = p1[1] - p2[1]
    dy = p1[2] - p2[2]
    return hypot(dx, dy) < p1[3] and p1[3] > p2[3] * 1.1


# 🔁 головний цикл
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    win.fill((255, 255, 255))

    scale = max(0.3, min(50 / max(my_player[2], 1), 1.5))

    # 🟦 межі карти
    left = int((-MAP_SIZE - my_player[0]) * scale + 400)
    right = int((MAP_SIZE - my_player[0]) * scale + 400)
    top = int((-MAP_SIZE - my_player[1]) * scale + 400)
    bottom = int((MAP_SIZE - my_player[1]) * scale + 400)
    pygame.draw.rect(win, (0, 0, 0), (left, top, right - left, bottom - top), 5)

    current_time = time.time()

    # 🔴 інші гравці
    for p in all_players:
        if p[0] == my_id:
            continue

        # вже з'їдений
        if p[0] in eaten_players:
            continue

        # їмо (1 раз + кулдаун)
        if current_time - last_eat_time > EAT_COOLDOWN:
            if can_eat([my_id, my_player[0], my_player[1], my_player[2]], p):
                eaten_players.add(p[0])
                my_player[2] += int(p[3] * 0.4)
                last_eat_time = current_time
                continue

        # нас їдять
        if can_eat(p, [my_id, my_player[0], my_player[1], my_player[2]]):
            lose = True

        sx = int((p[1] - my_player[0]) * scale + 400)
        sy = int((p[2] - my_player[1]) * scale + 400)

        pygame.draw.circle(win, (255, 0, 0), (sx, sy), int(p[3] * scale))

    # 🟢 ми
    pygame.draw.circle(win, (0, 255, 0), (400, 400), int(my_player[2] * scale))

    # 🍎 їжа
    to_remove = []
    for eat in eats:
        if eat.check_collision(my_player[0], my_player[1], my_player[2]):
            to_remove.append(eat)
            my_player[2] += int(eat.radius * 0.2)
        else:
            sx = int((eat.x - my_player[0]) * scale + 400)
            sy = int((eat.y - my_player[1]) * scale + 400)
            pygame.draw.circle(win, eat.color, (sx, sy), int(eat.radius * scale))

    for eat in to_remove:
        eats.remove(eat)

    # 🧹 очищення
    if len(eaten_players) > 100:
        eaten_players.clear()

    # ❌ програш
    if lose:
        text = font.render("Ти програв", True, (244, 0, 0))
        win.blit(text, (300, 400))

    pygame.display.update()
    clock.tick(60)

    # 🎮 рух
    if not lose:
        keys = pygame.key.get_pressed()

        if keys[pygame.K_w]: my_player[1] -= 10
        if keys[pygame.K_s]: my_player[1] += 10
        if keys[pygame.K_a]: my_player[0] -= 10
        if keys[pygame.K_d]: my_player[0] += 10

        # 🟦 обмеження карти
        my_player[0] = max(-MAP_SIZE, min(MAP_SIZE, my_player[0]))
        my_player[1] = max(-MAP_SIZE, min(MAP_SIZE, my_player[1]))

        try:
            msg = f"{my_id},{my_player[0]},{my_player[1]},{my_player[2]}"
            sock.send(msg.encode())
        except:
            pass

pygame.quit()

