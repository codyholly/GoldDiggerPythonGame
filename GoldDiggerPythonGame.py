#Gold Digger is a 2D mining exploration game where players take on the role of a miner 
#searching for treasure and artifacts in a procedurally generated underground world.

#Created by Cody Holly - codyholly.com

#Import required libraries
import pygame
import random
import time
import sys

# Initialize Pygame with error handling
try:
    pygame.init()
except pygame.error as e:
    print(f"Failed to initialize Pygame: {e}")
    sys.exit(1)

# Game window and grid for blocks
WINDOW_WIDTH = 840
WINDOW_HEIGHT = 600
BLOCK_SIZE = 30
GOLD_CHANCE = 0.03
GRID_SIZE = 50
BASE_DIG_TIME = 10.0
MOVEMENT_DELAY = 0.05

# Mining time for different block types (seconds)
DIRT_MINE_TIME = .5
STONE_MINE_TIME = .75
HARD_STONE_MINE_TIME = 1.5
VERYHARD_STONE_MINE_TIME = 2

# Color definitions
BLACK = (0, 0, 0)
DARKGRAY = (80, 80, 80)
TAN = (115, 90, 50)
BROWN = (100, 69, 19)
GOLD = (255, 215, 0)
BLUE = (0, 0, 255)
SKY_BLUE = (135, 206, 235)
GRAY = (96, 96, 96)
RED = (255, 0, 0)
GREEN = (10, 255, 10)
WHITE = (255, 255, 255)

# Depth thresholds for different types of blocks
DEPTH_THRESHOLD = 20 # Depth where stone starts appearing more frequently
DEPTH_THRESHOLD2 = 30 # Depth where very hard stone starts appearing

class Player:
    #Class representing the player character
    # Initialize player position and stats
    def __init__(self, x, y):
        self.grid_x = x
        self.grid_y = y + 3
        self.score = 0
        self.dig_time_remaining = BASE_DIG_TIME
        self.bonus_time = 0
        self.mining_target = None
        self.mining_start_time = 0
        self.moving_direction = None
        self.mining_elapsed_time = 0
        self.last_move_time = 0
        self.blocks = {}
        self.found_artifact = False
        
    #Start mining a block at the given position
    def start_mining(self, block_pos, current_time, block_progress):
        self.mining_target = block_pos
        self.mining_start_time = current_time
        self.mining_elapsed_time = block_progress * self.blocks[self.mining_target].get_mine_time()
    
    #Stop mining and reset mining-related variables
    def stop_mining(self):
        self.mining_target = None
        self.moving_direction = None
        self.mining_elapsed_time = 0
    
    #Get the coordinates of the block the player is trying to mine based on direction
    def get_target_block(self):
        if self.moving_direction == "RIGHT":
            return (self.grid_x + 1, self.grid_y)
        elif self.moving_direction == "LEFT":
            return (self.grid_x - 1, self.grid_y)
        elif self.moving_direction == "DOWN":
            return (self.grid_x, self.grid_y + 1)
        elif self.moving_direction == "UP":
            return (self.grid_x, self.grid_y - 1)
        return None
        
    #Move player to new coordinates within grid boundaries
    def move_to(self, x, y):
        self.grid_x = max(0, min(x, GRID_SIZE - 1))
        self.grid_y = max(3, min(y, GRID_SIZE - 1))
        
    #Check if enough time has passed to allow movement
    def can_move(self, current_time):
        return current_time - self.last_move_time >= MOVEMENT_DELAY

    #Draw the player on the screen
    def draw(self, screen, camera_x, camera_y):
        screen_x = int(self.grid_x * BLOCK_SIZE - camera_x)
        screen_y = int(self.grid_y * BLOCK_SIZE - camera_y)
        pygame.draw.rect(screen, BLUE, (screen_x, screen_y, BLOCK_SIZE, BLOCK_SIZE))

class Block:
    #Class representing a single block in the game world
    # Initialize block properties
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.is_gold = random.random() < GOLD_CHANCE
        self.is_veryhard_stone = False
        self.is_artifact = False
        
        # Determine block type based on depth
        if y > DEPTH_THRESHOLD:
            if not self.is_gold:
                self.is_stone = True
                self.is_hard_stone = random.random() < 0.2
                if y > DEPTH_THRESHOLD2:
                    self.is_veryhard_stone = random.random() < 0.7
            else:
                self.is_stone = False
                self.is_hard_stone = False
        else:
            self.is_stone = random.random() < 0.2
            self.is_hard_stone = False
        self.is_dug = False
        self.mining_progress = 0.0
    
    #Get the time required to mine this block based on its type
    def get_mine_time(self):
        if self.is_veryhard_stone:
            return VERYHARD_STONE_MINE_TIME
        elif self.is_hard_stone:
            return HARD_STONE_MINE_TIME
        elif self.is_stone:
            return STONE_MINE_TIME
        return DIRT_MINE_TIME
    #Draw the block on the screen with appropriate color and mining progress
    def draw(self, screen, camera_x, camera_y):
        screen_x = self.x * BLOCK_SIZE - int(camera_x)
        screen_y = self.y * BLOCK_SIZE - int(camera_y)
        
        # Only draw blocks that are visible on screen and color
        if 0 <= screen_x <= WINDOW_WIDTH and 0 <= screen_y <= WINDOW_HEIGHT:
            if not self.is_dug:
                if self.is_artifact:
                    color = GREEN
                elif self.is_gold:
                    color = GOLD
                elif self.is_veryhard_stone:
                    color = DARKGRAY
                elif self.is_hard_stone:
                    color = GRAY
                elif self.is_stone:
                    color = BROWN
                else:
                    color = TAN if self.y <= DEPTH_THRESHOLD else GRAY
                pygame.draw.rect(screen, color, (screen_x, screen_y, BLOCK_SIZE, BLOCK_SIZE))
                
                # Draw mining progress overlay
                if self.mining_progress > 0:
                    progress_height = int(BLOCK_SIZE * self.mining_progress)
                    pygame.draw.rect(screen, SKY_BLUE, (screen_x, screen_y, BLOCK_SIZE, progress_height))

class Game:
    #Main game class handling game logic and rendering
    #Display welcome message at start of game
    def show_welcome_dialog(self):
        dialog_width = 500
        dialog_height = 350
        dialog_x = (WINDOW_WIDTH - dialog_width) // 2
        dialog_y = (WINDOW_HEIGHT - dialog_height) // 2
        
        # Create dialog surface
        dialog_surface = pygame.Surface((dialog_width, dialog_height))
        dialog_surface.fill(WHITE)
        pygame.draw.rect(dialog_surface, BLACK, (0, 0, dialog_width, dialog_height), 2)
        
        # Set up fonts
        font = pygame.font.Font(None, 32)
        title_font = pygame.font.Font(None, 48)
        
        # Prepare text elements
        title = title_font.render("Welcome to Gold Digger!", True, BLACK)
        message = [
            "Use the arrow keys to mine Gold.",
            "",
            "There is a rumor that a secret artifact",
            "is hidden in the depths...",
            "",
            "Press Enter to continue",
            "",
            "CodyHolly.com",
        ]

        # Draw title
        title_rect = title.get_rect(centerx=dialog_width//2, top=20)
        dialog_surface.blit(title, title_rect)

        # Draw message lines
        y_offset = 70
        for line in message:
            text = font.render(line, True, BLACK)
            text_rect = text.get_rect(centerx=dialog_width//2, top=y_offset)
            dialog_surface.blit(text, text_rect)
            y_offset += 30
        
        # Wait for user input
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        waiting = False

            self.screen.fill(SKY_BLUE)
            self.screen.blit(dialog_surface, (dialog_x, dialog_y))
            pygame.display.flip()
            self.clock.tick(60)
    
    # Initialize pygame and create game window
    def __init__(self):
        pygame.init()  # Initialize pygame again to ensure it's ready
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Gold Digger")
        
        # Initialize game components       
        self.clock = pygame.time.Clock()
        self.starting_x = GRID_SIZE // 2
        self.starting_y = 0
        self.player = Player(self.starting_x, self.starting_y)
        self.camera_x = 0
        self.camera_y = 0
        # Create game world
        self.blocks = {}
        self.create_world()
        # Set up game state        
        self.player.blocks = self.blocks
        self.show_game_over = False
        self.game_over_alpha = 0
        self.popup_shown = False
        
        # Show welcome dialog when game starts
        self.show_welcome_dialog()
    
    #Generate the game world with blocks
    def create_world(self):
        #Create regular blocks
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if y > 3:
                    self.blocks[(x, y)] = Block(x, y)

        # Place the special artifact block near the bottom
        artifact_y = GRID_SIZE - 2
        artifact_x = GRID_SIZE // 6
        self.blocks[(artifact_x, artifact_y)] = Block(artifact_x, artifact_y)
        self.blocks[(artifact_x, artifact_y)].is_artifact = True
    
    #Display dialog when player finds the artifact
    def show_artifact_dialog(self):
        dialog_width = 600
        dialog_height = 200
        dialog_x = (WINDOW_WIDTH - dialog_width) // 2
        dialog_y = (WINDOW_HEIGHT - dialog_height) // 2

        dialog_surface = pygame.Surface((dialog_width, dialog_height))
        dialog_surface.fill(WHITE)
        pygame.draw.rect(dialog_surface, BLACK, (0, 0, dialog_width, dialog_height), 2)

        font = pygame.font.Font(None, 24)
        message = [
            "You found where the Alien Artifact lives!",
            "You saw how it looks like and became self actualized.",
            "Content to never dig again...",
            "",
            "Press Enter to start over"
        ]

        y_offset = 30
        for line in message:
            text = font.render(line, True, BLACK)
            text_rect = text.get_rect(centerx=dialog_width//2, top=y_offset)
            dialog_surface.blit(text, text_rect)
            y_offset += 30

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.reset_game()
                        waiting = False

            self.screen.blit(dialog_surface, (dialog_x, dialog_y))
            pygame.display.flip()
            self.clock.tick(60)

        return True
    
    #Display dialog for purchasing drill bit durability
    def show_purchase_dialog(self):
        dialog_width = 400
        dialog_height = 300
        dialog_x = (WINDOW_WIDTH - dialog_width) // 2
        dialog_y = (WINDOW_HEIGHT - dialog_height) // 2
        
        input_text = ""
        input_active = True
        dialog_done = False
        
        while not dialog_done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        try:
                            gold_to_spend = int(input_text) if input_text else 0
                            if 0 <= gold_to_spend <= self.player.score:
                                seconds_to_buy = gold_to_spend // 100
                                if seconds_to_buy > 0:
                                    self.player.bonus_time += seconds_to_buy
                                    self.player.score -= seconds_to_buy * 100
                                dialog_done = True
                        except ValueError:
                            pass
                    elif event.key == pygame.K_ESCAPE:
                        dialog_done = True
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    elif event.unicode.isdigit():
                        input_text += event.unicode

            dialog_surface = pygame.Surface((dialog_width, dialog_height))
            dialog_surface.fill(WHITE)
            pygame.draw.rect(dialog_surface, BLACK, (0, 0, dialog_width, dialog_height), 2)
            
            font = pygame.font.Font(None, 36)
            title_text = font.render("Increase Drill Bit Durability?", True, BLACK)
            cost_text = font.render(f"Current Gold: {self.player.score}", True, BLACK)
            info_text = font.render("$100 Gold = +1% Durability", True, BLACK)
            input_prompt = font.render("Enter gold amount:", True, BLACK)
            input_display = font.render(input_text + "|" if input_active else input_text, True, BLACK)
            confirm_text = font.render("Press Enter to confirm", True, BLACK)
            cancel_text = font.render("Press Esc to cancel", True, BLACK)
            
            dialog_surface.blit(title_text, (dialog_width//2 - title_text.get_width()//2, 20))
            dialog_surface.blit(cost_text, (dialog_width//2 - cost_text.get_width()//2, 60))
            dialog_surface.blit(info_text, (dialog_width//2 - info_text.get_width()//2, 100))
            dialog_surface.blit(input_prompt, (20, 140))
            dialog_surface.blit(input_display, (20, 180))
            dialog_surface.blit(confirm_text, (dialog_width//2 - confirm_text.get_width()//2, 210))
            dialog_surface.blit(cancel_text, (dialog_width//2 - cancel_text.get_width()//2, 230))
            
            self.screen.blit(dialog_surface, (dialog_x, dialog_y))
            pygame.display.flip()
            self.clock.tick(60)
        
        return True
    
    #Reset game state to initial conditions
    def reset_game(self):
        self.player = Player(self.starting_x, self.starting_y)
        self.create_world()
        self.player.blocks = self.blocks
        self.show_game_over = False
        self.game_over_alpha = 0
        self.popup_shown = False

    #Update camera position to follow player
    def update_camera(self):
        self.camera_x = self.player.grid_x * BLOCK_SIZE - WINDOW_WIDTH // 2
        self.camera_y = self.player.grid_y * BLOCK_SIZE - WINDOW_HEIGHT // 2
        self.camera_x = max(0, min(self.camera_x, GRID_SIZE * BLOCK_SIZE - WINDOW_WIDTH))
        self.camera_y = max(0, min(self.camera_y, GRID_SIZE * BLOCK_SIZE - WINDOW_HEIGHT))
    
    #Display popup message when drill bit breaks
    def draw_game_over_message(self):
        if self.show_game_over:
            font = pygame.font.Font(None, 48)
            text1 = font.render("Your drill bit broke!", True, BLACK)
            text2 = font.render("Resurface to get a new one.", True, BLACK)
            
            padding = 20
            max_text_width = max(text1.get_width(), text2.get_width())
            rect_width = max_text_width + padding * 2
            rect_height = text1.get_height() + text2.get_height() + padding * 3
            
            rect_x = (WINDOW_WIDTH - rect_width) // 2
            rect_y = padding
            
            text_surface = pygame.Surface((rect_width, rect_height), pygame.SRCALPHA)
            text_surface.fill((135, 206, 235, self.game_over_alpha))
            
            text1_rect = text1.get_rect(centerx=rect_width//2, top=padding)
            text2_rect = text2.get_rect(centerx=rect_width//2, top=text1_rect.bottom + padding)
            
            text_surface.blit(text1, text1_rect)
            text_surface.blit(text2, text2_rect)
            
            self.screen.blit(text_surface, (rect_x, rect_y))
    
    #Main game loop
    def run(self):
        running = True
        last_time = time.time()

        while running:
            current_time = time.time()
            delta_time = current_time - last_time
            last_time = current_time

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYUP:
                    if self.player.mining_target:
                        block = self.blocks[self.player.mining_target]
                        block.mining_progress = min(self.player.mining_elapsed_time / block.get_mine_time(), 1.0)
                    self.player.stop_mining()
            
            keys = pygame.key.get_pressed()
            if not self.show_game_over:
                if keys[pygame.K_RIGHT]:
                    self.player.moving_direction = "RIGHT"
                elif keys[pygame.K_LEFT]:
                    self.player.moving_direction = "LEFT"
                elif keys[pygame.K_DOWN]:
                    self.player.moving_direction = "DOWN"
                elif keys[pygame.K_UP]:
                    self.player.moving_direction = "UP"
            
            if self.player.moving_direction:
                target_pos = self.player.get_target_block()
                
                if target_pos in self.blocks:
                    block = self.blocks[target_pos]
                    if not block.is_dug:
                        if self.player.dig_time_remaining > 0:
                            if block.is_artifact:
                                block.is_dug = True
                                self.show_artifact_dialog()
                                continue
                                
                            if self.player.mining_target != target_pos:
                                self.player.start_mining(target_pos, current_time, block.mining_progress)
                            
                            self.player.mining_elapsed_time += delta_time
                            mine_time = block.get_mine_time()
                            block.mining_progress = min(self.player.mining_elapsed_time / mine_time, 1.0)
                            
                            self.player.dig_time_remaining -= delta_time
                            
                            if block.mining_progress >= 1.0:
                                block.is_dug = True
                                if block.is_gold:
                                    self.player.score += 100
                                self.player.move_to(target_pos[0], target_pos[1])
                                self.player.stop_mining()
                    elif block.is_dug and self.player.can_move(current_time):
                        self.player.move_to(target_pos[0], target_pos[1])
                        self.player.last_move_time = current_time
                        self.player.stop_mining()
                elif target_pos not in self.blocks and self.player.can_move(current_time):
                    self.player.move_to(target_pos[0], target_pos[1])
                    self.player.last_move_time = current_time
                    self.player.stop_mining()
            
            # Handle game over state
            if self.player.dig_time_remaining <= 0 and not self.show_game_over and not self.popup_shown:
                self.show_game_over = True
                self.game_over_alpha = 0
                
            if self.show_game_over:
                self.game_over_alpha = min(self.game_over_alpha + 5, 255)
                if self.game_over_alpha >= 255 and not self.popup_shown:
                    self.popup_shown = True
                    self.show_purchase_dialog()
                    self.show_game_over = False
            
            # Reset game state when reaching surface
            if self.player.grid_y == 3 and (self.popup_shown or self.show_game_over):
                self.player.dig_time_remaining = BASE_DIG_TIME + self.player.bonus_time
                self.player.stop_mining()
                self.show_game_over = False
                self.game_over_alpha = 0
                self.popup_shown = False  # Reset for next round
            
            self.update_camera()
            self.screen.fill(SKY_BLUE)
            
            # Draw blocks and player
            start_x = max(0, int(self.camera_x // BLOCK_SIZE - 1))
            end_x = min(GRID_SIZE, int((self.camera_x + WINDOW_WIDTH) // BLOCK_SIZE + 1))
            start_y = max(0, int(self.camera_y // BLOCK_SIZE - 1))
            end_y = min(GRID_SIZE, int((self.camera_y + WINDOW_HEIGHT) // BLOCK_SIZE + 1))
            
            for y in range(start_y, end_y):
                for x in range(start_x, end_x):
                    if (x, y) in self.blocks:
                        self.blocks[(x, y)].draw(self.screen, self.camera_x, self.camera_y)
            
            self.player.draw(self.screen, self.camera_x, self.camera_y)
            
            # Draw UI
            font = pygame.font.Font(None, 36)
            score_text = font.render(f'Gold: ${self.player.score}', True, BLACK)
            time_text = font.render(f'Drill bit condition: {self.player.dig_time_remaining:.1f}%', True, BLACK)
            bonus_text = font.render(f'Bonus Durability: {self.player.bonus_time}%', True, BLACK)
            self.screen.blit(score_text, (10, 10))
            self.screen.blit(time_text, (10, 50))
            self.screen.blit(bonus_text, (10, 90))
            
            if self.show_game_over:
                self.draw_game_over_message()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()

#Start the game when the script is run
if __name__ == "__main__":
    game = Game()
    game.run()