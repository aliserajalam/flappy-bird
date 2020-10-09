# Import modules
import pygame
import neat
import time
import os
import random

pygame.font.init()

# Set window width and height
WIN_WIDTH = 500
WIN_HEIGHT = 800

# Load game assets
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("images", "bird1.png"))), pygame.transform.scale2x(
    pygame.image.load(os.path.join('images', 'bird2.png'))), pygame.transform.scale2x(pygame.image.load(os.path.join('images', 'bird3.png')))]
PIPE_IMG = pygame.transform.scale2x(
    pygame.image.load(os.path.join('images', 'pipe.png')))
BASE_IMG = pygame.transform.scale2x(
    pygame.image.load(os.path.join('images', 'base.png')))
BACKGROUND_IMG = pygame.transform.scale2x(
    pygame.image.load(os.path.join('images', 'background.png')))

STAT_FONT = pygame.font.SysFont('comicsans', 50)


class Bird:
    """
    Represents a bird object 
    """
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25   # Max rotation or tilt of the bird
    ROT_VEL = 20    # Rotation speed each frame
    ANIMATION_TIME = 5  # Duration of animation

    def __init__(self, x, y):
        """
        Initialise the bird object
        :param x: starting horizontal pos (int)
        :param y: starting vertical pos (int)
        :return: None
        """
        # Define the initial starting position of the bird
        self.x = x
        self.y = y
        self.tilt = 0   # Angle of the bird
        self.tick_count = 0  # Bird physics tracking height
        self.vel = 0    # Speed of the bird
        self.height = self.y
        self.img_count = 0  # Track which bird image is shown
        self.img = self.IMGS[0]

    def jump(self):
        """
        Makes the bird jump
        :return: None
        """
        self.vel = -10.5    # Movement up
        self.tick_count = 0  # Reset to 0, Track change in direction or velocity
        self.height = self.y    # Where the bird started it's jump from

    # Called each frame in the game loop
    def move(self):
        """
        Makes the bird move
        :return: None
        """
        self.tick_count += 1  # Track how many frames has passed

        # Displacement, track pixel changes current frame
        displacement = self.vel * self.tick_count + 1.5*self.tick_count**2

        # Terminal velocity
        if displacement >= 16:
            displacement = 16

        if displacement < 0:
            displacement -= 2

        # Change vertical movement based on displacement
        self.y = self.y + displacement

        # Tilting the bird
        # Bird is moving upwards
        if displacement < 0 or self.y < self.height + 50:
            # Tilt the bird up
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        # Bird is falling
        else:
            # Tilt the bird down
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        """
        Draw the bird
        :param win: Pygame window
        :return: None
        """
        # Keep track of how many frames the bird has been shown
        self.img_count += 1

        # Animating the bird wing flap based on the current game frame
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        # If the bird is falling downwards, it shouldn't be flapping
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2

        # Rotate an image around its centre
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(
            center=self.img.get_rect(topleft=(self.x, self.y)).center)

        win.blit(rotated_image, new_rect.topleft)

    # Collision
    def get_mask(self):
        """
        Pygame mask of the current image of the bird
        :return: pygame.mask
        """
        return pygame.mask.from_surface(self.img)


class Pipe:
    """
    Represents a pipe object
    """
    GAP = 200   # Distance between top and bottom pipes
    VEL = 5     # Speed of the pipes moving

    def __init__(self, x):
        """
        Initialise pipe object
        :param x: int
        :return: None
        """
        self.x = x
        self.height = 0

        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        # Tracks if the bird has passed the pipe
        self.passed = False
        # Set random height
        self.set_height()

    def set_height(self):
        """
        Sets the height of the pipe, from the top of the screen
        :return: None
        """
        # Sets the top and bottom pipe height randomly with gap inbetween
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        """
        Pipe's movement
        :return: None
        """
        self.x -= self.VEL  # Moves the pipe from right to left based on the velocity defined in class

    def draw(self, win):
        """
        Draws the top and bottom pipe in the game window
        :param win: Pygame window
        :return: None
        """
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    # Collision detection
    def collide(self, bird):
        """
        Returns if collision is detected between the bird and pipe
        :param bird: Bird object
        :return: Bool
        """
        bird_mask = bird.get_mask()  # Retrieve the bird pixels bounding box
        # Get the top pipe's bounding box
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        # Get the bottom pipe's bounding box
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        # How far apart the pixels are apart from each other - offset
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        # Point of collision / overlap
        t_point = bird_mask.overlap(top_mask, top_offset)
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)

        # If bird has collided with the top or bottom pipe
        if t_point or b_point:
            return True

        return False


class Base:
    """
    Represents the moving floor of the game    
    """
    VEL = 5  # Same velocity as pipe
    WIDTH = BASE_IMG.get_width()    # Image width
    IMG = BASE_IMG

    def __init__(self, y):
        """
        Initialise the object
        :param y: int
        :return: None
        """
        self.y = y
        # Initialise two images to shift for an infinite loop visual
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        """
        Floor movement with swapping two images, gives the illusion of infinite floor
        :return: None 
        """
        # Move both images at the same velocity
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        # Cycle image based on the position of the image
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        """
        Draw the floor composed of two identical images
        :return: None
        """
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def draw_window(win, bird, pipes, base, score):
    """
    Draws the window of the game loop
    :param win: Pygame window surface
    :param bird: Bird object
    :param pipes: List of pipes
    :param base: Floor object
    :param score: Score of the game (int)
    :return None:
    """
    win.blit(BACKGROUND_IMG, (0, 0))

    for pipe in pipes:
        pipe.draw(win)

    text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

    base.draw(win)
    bird.draw(win)
    pygame.display.update()


def main():
    """
    Initialise game assets and runs the game
    :return: None
    """
    bird = Bird(230, 350)
    base = Base(730)
    pipes = [Pipe(600)]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

    clock = pygame.time.Clock()

    score = 0

    run = True
    # Game loop
    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            # Implement user controls

        # bird.move()
        add_pipe = False
        rem = []  # Removal array, tracks pipes that have passed the screen
        for pipe in pipes:
            # If bird has collided with the pipe
            if pipe.collide(bird):
                pass

            # If pipe has passed the screen
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            # Bird has passed the pipe
            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True

            pipe.move()

        # Add a pipe
        if add_pipe:
            score += 1
            pipes.append(Pipe(600))

        # Remove pipes in removal array
        for r in rem:
            pipes.remove(r)

        # Bird collides with the floor
        if bird.y + bird.img.get_height() >= 730:
            pass

        base.move()
        draw_window(win, bird, pipes, base, score)
    pygame.quit()
    quit()


main()
