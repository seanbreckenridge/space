from __future__ import annotations
import os
import random
from typing import Dict, Literal, List, NamedTuple

import pygame

WIDTH = 480
HEIGHT = 600
FPS = 60

# colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# global constants
START_ASTEROID_COUNT = 13

# initialize, create window
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SPACE!")
clock = pygame.time.Clock()

img_dir = os.path.join(os.path.dirname(__file__), "img")
explosions_dir = os.path.join(img_dir, "explosions")
sound_dir = os.path.join(os.path.dirname(__file__), "sound")

font_name = pygame.font.match_font("arial")

# load graphics
background = pygame.image.load(os.path.join(img_dir, "darkPurple.png")).convert()
background_rect = background.get_rect()
player_img = pygame.image.load(os.path.join(img_dir, "player.png")).convert()
meteor_img = pygame.image.load(os.path.join(img_dir, "meteor.png")).convert()
bullet_img = pygame.image.load(os.path.join(img_dir, "laser.png")).convert()
heart_img = pygame.image.load(os.path.join(img_dir, "hudHeart_full.png")).convert()
heart_img.set_colorkey(BLACK)
shoot_sound = pygame.mixer.Sound(os.path.join(sound_dir, "laser.wav"))
shoot_sound.set_volume(0.2)
explosion_sounds = []
for s in [1, 2]:
    explosion_sounds.append(
        pygame.mixer.Sound(os.path.join(sound_dir, f"Explosion{s}.wav"))
    )
for e in explosion_sounds:
    e.set_volume(0.2)
pygame.mixer.music.load(os.path.join(sound_dir, "background.wav"))
pygame.mixer.music.set_volume(0.4)
explosions: Dict[Literal["sm", "lg", "huge"], List[pygame.Surface]] = {}
explosions["sm"] = []
explosions["lg"] = []
explosions["huge"] = []
for i in range(9):
    filename = "regularExplosion0{}.png".format(i)
    expl_img = pygame.image.load(os.path.join(explosions_dir, filename))
    explosions["sm"].append(pygame.transform.scale(expl_img, (40, 40)))
    explosions["lg"].append(pygame.transform.scale(expl_img, (75, 75)))
    explosions["huge"].append(pygame.transform.scale(expl_img, (170, 170)))


def draw_text(surf, text, size, x, y, color):
    font = pygame.font.Font(font_name, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (int(x), int(y))
    surf.blit(text_surface, text_rect)


def update_hearts(surf, x, y, hp, img):
    for i in range(hp):
        img_rect = img.get_rect()
        img_rect.x = x + 30 * i
        img_rect.y = y
        surf.blit(img, img_rect)


class Player(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.transform.scale(player_img, (50, 38))
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()
        self.radius = 20
        # pygame.draw.circle(self.image, RED, self.rect.center, self.radius)
        self.rect.centerx = int(WIDTH / 2)
        self.rect.bottom = HEIGHT - 10
        self.speedx = 0
        self.health = 3
        self.shoot_delay = 250
        self.last_shot = pygame.time.get_ticks()

    def update(self):
        self.speedx = 0
        keystate = pygame.key.get_pressed()
        if keystate[pygame.K_LEFT] or keystate[pygame.K_a]:
            self.speedx = -5
        if keystate[pygame.K_RIGHT] or keystate[pygame.K_d]:
            self.speedx = 5
        if keystate[pygame.K_UP] or keystate[pygame.K_w]:
            self.rect.y -= 5
        if keystate[pygame.K_DOWN] or keystate[pygame.K_s]:
            self.rect.y += 5
        if keystate[pygame.K_SPACE]:
            self.shoot()
        if keystate[pygame.K_ESCAPE] or keystate[pygame.K_q]:
            pygame.quit()
            exit(0)
        self.rect.x += self.speedx
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.y > HEIGHT - 30:
            self.rect.y = HEIGHT - 30
        if self.rect.y < 0:
            self.rect.y = 0

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            bullet = Bullet(self.rect.centerx, self.rect.top)
            state.all_sprites.add(bullet)
            state.bullets.add(bullet)
            shoot_sound.play()


class Mob(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image_orig = pygame.transform.scale(meteor_img, (40, 40))
        self.image_orig.set_colorkey(BLACK)
        self.image = self.image_orig.copy()
        self.rect = self.image.get_rect()
        self.radius = int(self.rect.width * 0.85 / 2)
        # pygame.draw.circle(self.image, RED, self.rect.center, self.radius)
        self.rect.x = random.randrange(WIDTH - self.rect.width)
        self.rect.y = random.randrange(-100, -40)
        self.prevspeedmin = 1
        self.prevspeedmax = 6
        self.speedy = random.randrange(self.prevspeedmin, self.prevspeedmax)
        self.speedx = random.randrange(-3, 3)
        self.rot = 0
        self.rot_speed = random.randrange(-8, 8)
        self.last_update = pygame.time.get_ticks()

    def rotate(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > 50:
            self.last_update = now
            self.rot = (self.rot + self.rot_speed) % 360
            new_image = pygame.transform.rotate(self.image_orig, self.rot)
            # make sure center stays the same when rotated
            old_center = self.rect.center
            self.image = new_image
            self.rect = self.image.get_rect()
            self.rect.center = old_center

    def update(self):
        self.rotate()
        self.rect.y += self.speedy
        self.rect.x += self.speedx
        if (
            self.rect.top > HEIGHT + 10
            or self.rect.left < -25
            or self.rect.right > WIDTH + 25
        ):
            self.rect.x = random.randrange(WIDTH - self.rect.width)
            self.rect.y = random.randrange(-100, -40)
            self.prevspeedmin += 2
            self.prevspeedmax += 2
            self.speedy = random.randrange(self.prevspeedmin, self.prevspeedmax)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = bullet_img
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()
        self.rect.bottom = y
        self.rect.centerx = x
        self.speedy = -10

    def update(self):
        self.rect.y += self.speedy
        # kill it if it moves off the top of the screen
        if self.rect.bottom < 0:
            self.kill()


class Explosion(pygame.sprite.Sprite):
    def __init__(self, center, size):
        pygame.sprite.Sprite.__init__(self)
        self.size = size
        self.image = explosions[self.size][0]
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.frame = 0
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 50

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_rate:
            self.last_update = now
            self.frame += 1
            if self.frame == len(explosions[self.size]):
                self.kill()
            else:
                center = self.rect.center
                self.image = explosions[self.size][self.frame]
                self.rect = self.image.get_rect()
                self.rect.center = center


def show_go_screen(score: int) -> None:
    screen.blit(background, background_rect)
    draw_text(screen, "SPACE!", 64, WIDTH / 2, HEIGHT / 4, WHITE)
    draw_text(
        screen, "arrow keys/wasd move, space to fire", 22, WIDTH / 2, HEIGHT / 2, WHITE
    )
    draw_text(screen, "press a key to begin", 18, WIDTH / 2, HEIGHT * 3 / 4, WHITE)
    if not score == 0:
        draw_text(screen, f"{score}", 18, WIDTH / 2, 10, WHITE)
    pygame.display.flip()
    waiting = True
    while waiting:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit(0)
            if event.type == pygame.KEYUP:
                waiting = False
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    pygame.quit()
                    exit(0)


class State(NamedTuple):
    all_sprites: pygame.sprite.Group
    mobs: pygame.sprite.Group
    bullets: pygame.sprite.Group
    player: Player

    @staticmethod
    def reset_state() -> State:
        all_sprites: pygame.sprite.Group = pygame.sprite.Group()
        mobs: pygame.sprite.Group = pygame.sprite.Group()
        bullets: pygame.sprite.Group = pygame.sprite.Group()
        player = Player()
        all_sprites.add(player)
        for _ in range(START_ASTEROID_COUNT):
            m = Mob()
            all_sprites.add(m)
            mobs.add(m)

        return State(all_sprites, mobs, bullets, player)

    def spawn_mob(self) -> None:
        m = Mob()
        self.all_sprites.add(m)
        self.mobs.add(m)


pygame.mixer.music.play(loops=-1, fade_ms=800)  # repeat music

state = State.reset_state()


def game_loop():
    global state
    score: int = 0
    game_over = True
    death_expl = None

    running = True
    while running:
        if game_over:
            show_go_screen(score)
            game_over = False
            score = 0
            state = State.reset_state()

        clock.tick(FPS)

        # Process Inputs
        for event in pygame.event.get():
            # check if we should close the window
            if event.type == pygame.QUIT:
                running = False

        # Update
        state.all_sprites.update()
        for bullet_hit in pygame.sprite.groupcollide(
            state.mobs, state.bullets, True, True
        ):
            score += 100
            random.choice(explosion_sounds).play()
            expl = Explosion(bullet_hit.rect.center, "lg")
            state.all_sprites.add(expl)
            state.spawn_mob()

        # check to see if mob hit the player
        for hit in pygame.sprite.spritecollide(
            state.player, state.mobs, True, pygame.sprite.collide_circle
        ):
            state.player.health -= 1
            random.choice(explosion_sounds).play()
            if state.player.health > 0:
                expl = Explosion(hit.rect.center, "sm")
                state.all_sprites.add(expl)
                state.spawn_mob()
            else:
                state.player.kill()
                death_expl = Explosion(hit.rect.center, "huge")
                state.all_sprites.add(death_expl)
                break

        if (
            not state.player.alive()
            and death_expl is not None
            and not death_expl.alive()
        ):
            game_over = True

        # Render
        screen.fill(BLACK)
        screen.blit(background, background_rect)
        state.all_sprites.draw(screen)
        # draw_text(screen, f"{score}", 18, WIDTH / 2, 10, WHITE)
        update_hearts(screen, WIDTH - 90, 5, state.player.health, heart_img)
        # do this last; after drawing, flip the display
        pygame.display.flip()

    pygame.quit()
    return 0


if __name__ == "__main__":
    exit(game_loop())
