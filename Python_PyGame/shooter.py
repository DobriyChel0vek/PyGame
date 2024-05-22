import pygame
from pygame import mixer
import os
import random
import csv
import button

mixer.init()
pygame.init()


SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Shooter')

#ограничение фпс
clock = pygame.time.Clock()
FPS = 60

#создаём переменные 
GRAVITY = 0.75
SCROLL_THRESH = 200
ROWS = 16
COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 21
MAX_LEVELS = 100
screen_scroll = 0
bg_scroll = 0
level = 1
level_game = False
start_game = False
start_intro = False


#определяем переменные действий игрока
moving_left = False
moving_right = False
shoot = False
grenade = False
grenade_thrown = False


#звуки эффектов
jump_fx = pygame.mixer.Sound('audio/jump.wav')
jump_fx.set_volume(0.05)
shot_fx = pygame.mixer.Sound('audio/shot.wav')
shot_fx.set_volume(0.05)
grenade_fx = pygame.mixer.Sound('audio/grenade.wav')
grenade_fx.set_volume(0.05)



#создание кнопок start exit restart
levels_img = pygame.image.load('img/levels_btn.png').convert_alpha()
start_img = pygame.image.load('img/start_btn.png').convert_alpha()
exit_img = pygame.image.load('img/exit_btn.png').convert_alpha()
restart_img = pygame.image.load('img/restart_btn.png').convert_alpha()
#создание заднего фона
pine1_img = pygame.image.load('img/Background/pine1.png').convert_alpha()
pine2_img = pygame.image.load('img/Background/pine2.png').convert_alpha()
mountain_img = pygame.image.load('img/Background/mountain.png').convert_alpha()
sky_img = pygame.image.load('img/Background/sky_cloud.png').convert_alpha()
#хранит плитки в виде списка
img_list = []
for x in range(TILE_TYPES):
	img = pygame.image.load(f'img/Tile/{x}.png')
	img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
	img_list.append(img)
#выстрел
bullet_img = pygame.image.load('img/icons/bullet.png').convert_alpha()
#грена
grenade_img = pygame.image.load('img/icons/grenade.png').convert_alpha()
#коробки с хилкам и боеприпасами
health_box_img = pygame.image.load('img/icons/health_box.png').convert_alpha()
ammo_box_img = pygame.image.load('img/icons/ammo_box.png').convert_alpha()
grenade_box_img = pygame.image.load('img/icons/grenade_box.png').convert_alpha()
item_boxes = {
	'Health'	: health_box_img,
	'Ammo'		: ammo_box_img,
	'Grenade'	: grenade_box_img
}


#устанавливаем цвет
BG = (144, 201, 120)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
PINK = (235, 65, 54)

#экран входа
bg1 = pygame.image.load('img/background/mountain.png')
bg2 = pygame.image.load('img/background/pine1.png')
bg3 = pygame.image.load('img/background/pine2.png')
bg4 = pygame.image.load('img/background/sky_cloud.png')
bg_x = 0

#шрифт в игре
font = pygame.font.SysFont('Futura', 30)

def draw_text(text, font, text_col, x, y):
	img = font.render(text, True, text_col)
	screen.blit(img, (x, y))


def draw_bg():
	screen.fill(BG)
	width = sky_img.get_width()
	for x in range(5):
		screen.blit(sky_img, ((x * width) - bg_scroll * 0.5, 0))
		screen.blit(mountain_img, ((x * width) - bg_scroll * 0.6, SCREEN_HEIGHT - mountain_img.get_height() - 300))
		screen.blit(pine1_img, ((x * width) - bg_scroll * 0.7, SCREEN_HEIGHT - pine1_img.get_height() - 150))
		screen.blit(pine2_img, ((x * width) - bg_scroll * 0.8, SCREEN_HEIGHT - pine2_img.get_height()))


#функция сброса уровня
def reset_level():
	enemy_group.empty()
	bullet_group.empty()
	grenade_group.empty()
	explosion_group.empty()
	item_box_group.empty()
	decoration_group.empty()
	water_group.empty()
	exit_group.empty()

#создаём лист дял сброса объектов
	data = []
	for row in range(ROWS):
		r = [-1] * COLS
		data.append(r)

	return data




class Soldier(pygame.sprite.Sprite):
	def __init__(self, char_type, x, y, scale, speed, ammo, grenades):
		pygame.sprite.Sprite.__init__(self)
		self.alive = True
		self.char_type = char_type
		self.speed = speed
		self.ammo = ammo
		self.start_ammo = ammo
		self.shoot_cooldown = 0
		self.grenades = grenades
		self.health = 50
		self.max_health = self.health
		self.direction = 1
		self.vel_y = 0
		self.jump = False
		self.in_air = True
		self.flip = False
		self.animation_list = []
		self.frame_index = 0
		self.action = 0
		self.update_time = pygame.time.get_ticks()
		self.move_counter = 0
		self.vision = pygame.Rect(0, 0, 150, 20)
		self.idling = False
		self.idling_counter = 0
		
		#загрузка анимации персов
		animation_types = ['Idle', 'Run', 'Jump', 'Death']
		for animation in animation_types:
			#сбрасывает временный список изображений
			temp_list = []
			#считает кол-во файлов в папке
			num_of_frames = len(os.listdir(f'img/{self.char_type}/{animation}'))
			for i in range(num_of_frames):
				img = pygame.image.load(f'img/{self.char_type}/{animation}/{i}.png').convert_alpha()
				img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
				temp_list.append(img)
			self.animation_list.append(temp_list)

		self.image = self.animation_list[self.action][self.frame_index]
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.width = self.image.get_width()
		self.height = self.image.get_height()


	def update(self):
		self.update_animation()
		self.check_alive()
		#время кулдауна
		if self.shoot_cooldown > 0:
			self.shoot_cooldown -= 1


	def move(self, moving_left, moving_right):
		#ресет переменных перемещения
		screen_scroll = 0
		dx = 0
		dy = 0

		#перемещение персов
		if moving_left:
			dx = -self.speed
			self.flip = True
			self.direction = -1
		if moving_right:
			dx = self.speed
			self.flip = False
			self.direction = 1

		#прыжок
		if self.jump == True and self.in_air == False:
			self.vel_y = -15
			self.jump = False
			self.in_air = True

		#гравитация
		self.vel_y += GRAVITY
		if self.vel_y > 7:
			self.vel_y
		dy += self.vel_y

		
		for tile in world.obstacle_list:
			#проверка столкновений по x
			if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
				dx = 0
				#если бот врезался в стену он развернётся 
				if self.char_type == 'enemy':
					self.direction *= -1
					self.move_counter = 0
			#проверка столкновений по y
			if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
				
				if self.vel_y < 0:
					self.vel_y = 0
					dy = tile[1].bottom - self.rect.top
				
				elif self.vel_y >= 0:
					self.vel_y = 0
					self.in_air = False
					dy = tile[1].top - self.rect.bottom


		#проверка столкновений с водой
		if pygame.sprite.spritecollide(self, water_group, False):
			self.health = 0

		#проверка столкновения с выходом
		level_complete = False
		if pygame.sprite.spritecollide(self, exit_group, False):
			level_complete = True

		#не позволяет выходит за пределы экрана
		if self.rect.bottom > SCREEN_HEIGHT:
			self.health = 0


		
		if self.char_type == 'player':
			if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
				dx = 0

		#обновляет позицию игрока
		self.rect.x += dx
		self.rect.y += dy

		#прокручивает экран в зависимости от позиции игрока
		if self.char_type == 'player':
			if (self.rect.right > SCREEN_WIDTH - SCROLL_THRESH and bg_scroll < (world.level_length * TILE_SIZE) - SCREEN_WIDTH)\
				or (self.rect.left < SCROLL_THRESH and bg_scroll > abs(dx)):
				self.rect.x -= dx
				screen_scroll = -dx

		return screen_scroll, level_complete



	def shoot(self):
		if self.shoot_cooldown == 0 and self.ammo > 0:
			self.shoot_cooldown = 20
			bullet = Bullet(self.rect.centerx + (0.75 * self.rect.size[0] * self.direction), self.rect.centery, self.direction)
			bullet_group.add(bullet)
			#ограничение патронов
			self.ammo -= 1
			shot_fx.play()


	def ai(self):
		if self.alive and player.alive:
			if self.idling == False and random.randint(1, 200) == 1:
				self.update_action(0)
				self.idling = True
				self.idling_counter = 50
			#проверка на растояние между ботом и игроком
			if self.vision.colliderect(player.rect):
				#остоновка бота и разворот лицом к игроку
				self.update_action(0)
				#выстрел
				self.shoot()
			else:
				if self.idling == False:
					if self.direction == 1:
						ai_moving_right = True
					else:
						ai_moving_right = False
					ai_moving_left = not ai_moving_right
					self.move(ai_moving_left, ai_moving_right)
					self.update_action(1)
					self.move_counter += 1
					#обновлять растояние меджу ботом и игроков во время движения
					self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)

					if self.move_counter > TILE_SIZE:
						self.direction *= -1
						self.move_counter *= -1
				else:
					self.idling_counter -= 1
					if self.idling_counter <= 0:
						self.idling = False

		
		self.rect.x += screen_scroll


	def update_animation(self):
		#обновление анимации
		ANIMATION_COOLDOWN = 100
		#обновление кадра в зависимости от текущего
		self.image = self.animation_list[self.action][self.frame_index]
		#проверка времени между обновлениями кадров
		if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
			self.update_time = pygame.time.get_ticks()
			self.frame_index += 1
		#если прокрутка кадров закончена вернётся в начало
		if self.frame_index >= len(self.animation_list[self.action]):
			if self.action == 3:
				self.frame_index = len(self.animation_list[self.action]) - 1
			else:
				self.frame_index = 0



	def update_action(self, new_action):
		#проверяет действия игрока отличается оно от предыдущего или нет
		if new_action != self.action:
			self.action = new_action
			self.frame_index = 0
			self.update_time = pygame.time.get_ticks()



	def check_alive(self):
		if self.health <= 0:
			self.health = 0
			self.speed = 0
			self.alive = False
			self.update_action(3)


	def draw(self):
		screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)


class World():
	def __init__(self):
		self.obstacle_list = []

	def process_data(self, data):
		self.level_length = len(data[0])
		#итерация по каждому значению в файле данных уровня
		for y, row in enumerate(data):
			for x, tile in enumerate(row):
				if tile >= 0:
					img = img_list[tile]
					img_rect = img.get_rect()
					img_rect.x = x * TILE_SIZE
					img_rect.y = y * TILE_SIZE
					tile_data = (img, img_rect)
					if tile >= 0 and tile <= 8:
						self.obstacle_list.append(tile_data)
					elif tile >= 9 and tile <= 10:
						water = Water(img, x * TILE_SIZE, y * TILE_SIZE)
						water_group.add(water)
					elif tile >= 11 and tile <= 14:
						decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
						decoration_group.add(decoration)
					elif tile == 15:#создаёт игрока
						player = Soldier('player', x * TILE_SIZE, y * TILE_SIZE, 1.65, 5, 20, 5)
						health_bar = HealthBar(10, 10, player.health, player.health)
					elif tile == 16:#создаёт врага
						enemy = Soldier('enemy', x * TILE_SIZE, y * TILE_SIZE, 1.65, 2, 20, 0)
						enemy_group.add(enemy)
					elif tile == 17:#создаёт ящик с боеприпасами
						item_box = ItemBox('Ammo', x * TILE_SIZE, y * TILE_SIZE)
						item_box_group.add(item_box)
					elif tile == 18:#создаёт ящик с греной 
						item_box = ItemBox('Grenade', x * TILE_SIZE, y * TILE_SIZE)
						item_box_group.add(item_box)
					elif tile == 19:#создаёт ящик с хилкой
						item_box = ItemBox('Health', x * TILE_SIZE, y * TILE_SIZE)
						item_box_group.add(item_box)
					elif tile == 20:#создаёт выход
						exit = Exit(img, x * TILE_SIZE, y * TILE_SIZE)
						exit_group.add(exit)

		return player, health_bar


	def draw(self):
		for tile in self.obstacle_list:
			tile[1][0] += screen_scroll
			screen.blit(tile[0], tile[1])


class Decoration(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

	def update(self):
		self.rect.x += screen_scroll


class Water(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

	def update(self):
		self.rect.x += screen_scroll

class Exit(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

	def update(self):
		self.rect.x += screen_scroll


class ItemBox(pygame.sprite.Sprite):
	def __init__(self, item_type, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.item_type = item_type
		self.image = item_boxes[self.item_type]
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))


	def update(self):
		self.rect.x += screen_scroll
		#проверка взял ли игрок коробку
		if pygame.sprite.collide_rect(self, player):
			#проверка какая это коробка
			if self.item_type == 'Health':
				player.health += 25
				if player.health > player.max_health:
					player.health = player.max_health
			elif self.item_type == 'Ammo':
				player.ammo += 15
			elif self.item_type == 'Grenade':
				player.grenades += 3
			#удаление этой коробки 
			self.kill()


class HealthBar():
	def __init__(self, x, y, health, max_health):
		self.x = x
		self.y = y
		self.health = health
		self.max_health = max_health

	def draw(self, health):
		#обновление ногого здоровья
		self.health = health
		#расчитать здоровье
		ratio = self.health / self.max_health
		pygame.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, 154, 24))
		pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
		pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * ratio, 20))


class Bullet(pygame.sprite.Sprite):
	def __init__(self, x, y, direction):
		pygame.sprite.Sprite.__init__(self)
		self.speed = 10
		self.image = bullet_img
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.direction = direction

	def update(self):
		#движение пули
		self.rect.x += (self.direction * self.speed) + screen_scroll
		#проверьте, не исчезла ли пуля с экрана
		if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
			self.kill()
		#проверка столкновения с текстурами
		for tile in world.obstacle_list:
			if tile[1].colliderect(self.rect):
				self.kill()

		#проверка столкновения с персами
		if pygame.sprite.spritecollide(player, bullet_group, False):
			if player.alive:
				player.health -= 5
				self.kill()
		for enemy in enemy_group:
			if pygame.sprite.spritecollide(enemy, bullet_group, False):
				if enemy.alive:
					enemy.health -= 25
					self.kill()



class Grenade(pygame.sprite.Sprite):
	def __init__(self, x, y, direction):
		pygame.sprite.Sprite.__init__(self)
		self.timer = 100
		self.vel_y = -11
		self.speed = 7
		self.image = grenade_img
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.width = self.image.get_width()
		self.height = self.image.get_height()
		self.direction = direction

	def update(self):
		self.vel_y += GRAVITY
		dx = self.direction * self.speed
		dy = self.vel_y

		#проверка на столкновение с уровнем
		for tile in world.obstacle_list:
			#проверка на столкновение со стенами
			if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
				self.direction *= -1
				dx = self.direction * self.speed
			#проверка столкновений по y
			if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
				self.speed = 0
				if self.vel_y < 0:
					self.vel_y = 0
					dy = tile[1].bottom - self.rect.top
				elif self.vel_y >= 0:
					self.vel_y = 0
					dy = tile[1].top - self.rect.bottom	


		#обновление позиции гранаты
		self.rect.x += dx + screen_scroll
		self.rect.y += dy

		#обратный отчёт
		self.timer -= 1
		if self.timer <= 0:
			self.kill()
			grenade_fx.play()
			explosion = Explosion(self.rect.x, self.rect.y, 0.5)
			explosion_group.add(explosion)
			#нанесение дамага гранаты по области
			if abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 2 and \
				abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 2:
				player.health -= 50
			for enemy in enemy_group:
				if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 2 and \
					abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 2:
					enemy.health -= 50



class Explosion(pygame.sprite.Sprite):
	def __init__(self, x, y, scale):
		pygame.sprite.Sprite.__init__(self)
		self.images = []
		for num in range(1, 6):
			img = pygame.image.load(f'img/explosion/exp{num}.png').convert_alpha()
			img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
			self.images.append(img)
		self.frame_index = 0
		self.image = self.images[self.frame_index]
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.counter = 0


	def update(self):
		self.rect.x += screen_scroll

		EXPLOSION_SPEED = 4
		#обновление анимации взрыва
		self.counter += 1

		if self.counter >= EXPLOSION_SPEED:
			self.counter = 0
			self.frame_index += 1
			#если анимация завершена, то удалите взрыв
			if self.frame_index >= len(self.images):
				self.kill()
			else:
				self.image = self.images[self.frame_index]


class ScreenFade():
	def __init__(self, direction, colour, speed):
		self.direction = direction
		self.colour = colour
		self.speed = speed
		self.fade_counter = 0


	def fade(self):
		fade_complete = False
		self.fade_counter += self.speed
		if self.direction == 1:#весь экран исчезает
			pygame.draw.rect(screen, self.colour, (0 - self.fade_counter, 0, SCREEN_WIDTH // 2, SCREEN_HEIGHT))
			pygame.draw.rect(screen, self.colour, (SCREEN_WIDTH // 2 + self.fade_counter, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
			pygame.draw.rect(screen, self.colour, (0, 0 - self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
			pygame.draw.rect(screen, self.colour, (0, SCREEN_HEIGHT // 1 +self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT))
		if self.direction == 2:#вертикальный экран постепенно исчезает
			pygame.draw.rect(screen, self.colour, (0, 0, SCREEN_WIDTH, 0 + self.fade_counter))
		if self.fade_counter >= SCREEN_WIDTH:
			fade_complete = True

		return fade_complete


#создание затухания экрана
intro_fade = ScreenFade(1, BLACK, 4)
death_fade = ScreenFade(2, PINK, 4)


#создание ккнопок
start_button = button.Button(SCREEN_WIDTH // 2 - 90, SCREEN_HEIGHT // 2 - 200, start_img, 1)
exit_button = button.Button(SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 + 100, exit_img, 1)
levels_button = button.Button(SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 2 - 50, levels_img, 1)
restart_button = button.Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, restart_img, 2)

#создание групп спрайтов
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()



#создать пустой список плиток
world_data = []
for row in range(ROWS):
	r = [-1] * COLS
	world_data.append(r)
#загружайте данные об уровне и создавайте мир
with open(f'level{level}_data.csv', newline='') as csvfile:
	reader = csv.reader(csvfile, delimiter=',')
	for x, row in enumerate(reader):
		for y, tile in enumerate(row):
			world_data[x][y] = int(tile)
world = World()
player, health_bar = world.process_data(world_data)



run = True
while run:

	clock.tick(FPS)

	if start_game == False:
		#меню рисования
		screen.blit(bg4, (bg_x, 0))
		screen.blit(bg3, (bg_x, 200))
		screen.blit(bg2, (bg_x, 300))
		screen.blit(bg1, (bg_x, 400))
		#добавить кнопки
		if levels_button.draw(screen):
			level_game = True
		if start_button.draw(screen):
			start_game = True
			start_intro = True
		if exit_button.draw(screen):
			run = False

	else:
		#обновление заднего фона
		draw_bg()
		#нарисуйте карту мира
		world.draw()
		#показать состояние здоровья игрока
		health_bar.draw(player.health)
		#кол-во боеприпасов на экране
		draw_text('AMMO: ', font, WHITE, 10, 35)
		for x in range(player.ammo):
			screen.blit(bullet_img, (90 + (x * 10), 40))
		#кол-во грен на экране
		draw_text('GRENADES: ', font, WHITE, 10, 60)
		for x in range(player.grenades):
			screen.blit(grenade_img, (135 + (x * 15), 60))


		player.update()
		player.draw()

		for enemy in enemy_group:
			enemy.ai()
			enemy.update()
			enemy.draw()

		#обновляйте и рисуйте группы
		bullet_group.update()
		grenade_group.update()
		explosion_group.update()
		item_box_group.update()
		decoration_group.update()
		water_group.update()
		exit_group.update()
		bullet_group.draw(screen)
		grenade_group.draw(screen)
		explosion_group.draw(screen)
		item_box_group.draw(screen)
		decoration_group.draw(screen)
		water_group.draw(screen)
		exit_group.draw(screen)

		#интро
		if start_intro == True:
			if intro_fade.fade():
				start_intro = False
				intro_fade.fade_counter = 0


		#обновлять действия игрока
		if player.alive:
			if shoot:
				player.shoot()
			elif grenade and grenade_thrown == False and player.grenades > 0:
				grenade = Grenade(player.rect.centerx + (0.5 * player.rect.size[0] * player.direction),\
				 			player.rect.top, player.direction)
				grenade_group.add(grenade)
				player.grenades -= 1
				grenade_thrown = True
			if player.in_air:
				player.update_action(2)#2: прыжок
			elif moving_left or moving_right:
				player.update_action(1)#1: бег
			else:
				player.update_action(0)#0: афк
			screen_scroll, level_complete = player.move(moving_left, moving_right)
			bg_scroll -= screen_scroll
			#проверьте, прошел ли игрок уровень
			if level_complete:
				start_intro = True
				level += 1
				bg_scroll = 0
				world_data = reset_level()
				if level <= MAX_LEVELS:
					#загружайте данные об уровне и создавайте мир
					with open(f'level{level}_data.csv', newline='') as csvfile:
						reader = csv.reader(csvfile, delimiter=',')
						for x, row in enumerate(reader):
							for y, tile in enumerate(row):
								world_data[x][y] = int(tile)
					world = World()
					player, health_bar = world.process_data(world_data)	
		else:
			screen_scroll = 0
			if death_fade.fade():
				if restart_button.draw(screen):
					death_fade.fade_counter = 0
					start_intro = True
					bg_scroll = 0
					world_data = reset_level()
					#загрузка днных об уровне и мире
					with open(f'level{level}_data.csv', newline='') as csvfile:
						reader = csv.reader(csvfile, delimiter=',')
						for x, row in enumerate(reader):
							for y, tile in enumerate(row):
								world_data[x][y] = int(tile)
					world = World()
					player, health_bar = world.process_data(world_data)


	for event in pygame.event.get():
		#выход из игры
		if event.type == pygame.QUIT:
			run = False

		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_a:
				moving_left = True
			if event.key == pygame.K_d:
				moving_right = True
			if event.key == pygame.K_SPACE:
				shoot = True
			if event.key == pygame.K_g:
				grenade = True
			if event.key == pygame.K_w and player.alive:
				player.jump = True
				jump_fx.play()
			if event.key == pygame.K_ESCAPE:
				run = False


		#отпущена кнопка клавиатуры
		if event.type == pygame.KEYUP:
			if event.key == pygame.K_a:
				moving_left = False
			if event.key == pygame.K_d:
				moving_right = False
			if event.key == pygame.K_SPACE:
				shoot = False
			if event.key == pygame.K_g:
				grenade = False
				grenade_thrown = False


	pygame.display.update()

pygame.quit()