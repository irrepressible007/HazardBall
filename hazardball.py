from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random

# Variables
W_WIDTH, W_HEIGHT = 1000, 900

GRID_LENGTH = 1200
GRID_CELL_SIZE = 50

fovY = 60
camera_angle_h = 0.0     
camera_angle_v = 0.5      
camera_zoom = 800         
is_first_person = False   

player_pos = [0, 0, 20] 
player_vel = [0, 0, 0]    
player_acc = 1.0         
friction = 0.97           
gravity = 1.5             
ball_radius = 20

# Game State
game_over = False
falling = False
time_count = 0
score = 0
lives = 3
powerup_active = False
powerup_timer = 0
keys_pressed = set()

# Progression
level = 1
diamonds_collected = 0
diamonds_needed = 5
has_won_level = False
has_won_level = False
portal_pos = None

# Level 3-5 Features
moving_objects = [] # List of dicts: {type, pos: [x,y], axis, range: [min,max], vel}
crumble_timer = 0

map_data = {}


def init_map():
    global map_data, level, diamonds_collected, diamonds_needed, has_won_level, portal_pos, moving_objects, crumble_timer
    map_data = {} 
    moving_objects = []
    diamonds_collected = 0
    has_won_level = False
    crumble_timer = 0
    
    # Scale difficulty: More holes as levels increase
    hole_prob = 0.10 + (level * 0.02)
    obstacle_prob = 0.15
    
    special_spawned = False
    
    for x in range(-GRID_LENGTH, GRID_LENGTH, GRID_CELL_SIZE):
        for y in range(-GRID_LENGTH, GRID_LENGTH, GRID_CELL_SIZE):
            
            # Safe zone (starting area)
            if -150 < x < 150 and -150 < y < 150:
                map_data[(x, y)] = 0 
            else:
                rng = random.random()
                
                # Level 3+ Dynamic Objects
                is_dynamic = False
                if level >= 3 and rng < 0.025: # 2.5% Chance (Reduced from 5%)
                    is_dynamic = True
                    # Determine type: wall (L3+) or hole (L4+)
                    m_type = 2 # Wall
                    if level >= 4 and random.random() < 0.5:
                        m_type = 1 # Hole
                    
                    # Axis and Range
                    axis = 0 if random.random() < 0.5 else 1
                    dist = 200
                    r_min = (x if axis==0 else y) - dist
                    r_max = (x if axis==0 else y) + dist
                    
                    moving_objects.append({
                        'type': m_type,
                        'pos': [float(x), float(y)],
                        'axis': axis,
                        'range': [r_min, r_max],
                        'vel': 2.0
                    })
                    # Do NOT set map_data here, they are separate entities
                
                if not is_dynamic:
                    if rng < hole_prob:     # Hole
                        map_data[(x, y)] = 1 
                    elif rng < obstacle_prob:   # Obstacle
                        map_data[(x, y)] = 2
                    else:
                        map_data[(x, y)] = 0 # Safe Floor
                    
                    # Randomly spawn items on safe floor
                    item_rng = random.random()
                    
                    # Ensure Portal Spawns (Type 6)
                    # force it at a specific far location if not spawned randomly
                    
                    if item_rng < 0.03:    # Diamond (Points) -> Type 3
                        map_data[(x, y)] = 3
                    elif item_rng < 0.035: # Speed Boost -> Type 4
                        map_data[(x, y)] = 4
                    elif item_rng < 0.037: # Extra Life -> Type 5
                        map_data[(x, y)] = 5
    
    # Force Spawn Portal far away
    # Ensure it's on a valid coordinate
    px = GRID_LENGTH - 100
    py = GRID_LENGTH - 100
    map_data[(px, py)] = 6 # Portal Type
    portal_pos = (px, py)


init_map()


# Drawing Functions
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_12):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, W_WIDTH, 0, W_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_bar(x, y, width, height, progress, color=(1.0, 1.0, 1.0)):
    """Draws a 2D progress bar."""
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, W_WIDTH, 0, W_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Background (Dark)
    glColor3f(0.2, 0.2, 0.2)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()

    # Foreground (Progress)
    fill_width = width * progress
    glColor3f(*color)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + fill_width, y)
    glVertex2f(x + fill_width, y + height)
    glVertex2f(x, y + height)
    glEnd()
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_diamond():
    # Draw a diamond using a rotated cube
    glPushMatrix()
    glColor3f(0.0, 1.0, 1.0) # Cyan (Points)
    glRotatef(45, 1, 1, 0)
    glutSolidCube(20)
    glPopMatrix()

def draw_powerups(type):
    glPushMatrix()
    if type == 4: # Speed Boost
        glColor3f(1.0, 0.0, 1.0) # Magenta (Distinct from Player)
        gluSphere(gluNewQuadric(), 15, 20, 20)
    elif type == 5: # Extra Life
        glColor3f(0.2, 1.0, 0.2) # Lime Green
        glutSolidCube(20)
    glPopMatrix()


def draw_grid_and_walls():
    
    # Draw Floor
    glBegin(GL_QUADS)
    for x in range(-GRID_LENGTH, GRID_LENGTH, GRID_CELL_SIZE):
        for y in range(-GRID_LENGTH, GRID_LENGTH, GRID_CELL_SIZE):
            
            tile_type = map_data.get((x, y), 0)
            
            if tile_type == 1: # Hole so Don't draw
                continue
            
            # Solid Floor Color (Dark Slate)
            glColor3f(0.15, 0.15, 0.2)
            
            glVertex3f(x, y, 0)
            glVertex3f(x + GRID_CELL_SIZE, y, 0)
            glVertex3f(x + GRID_CELL_SIZE, y + GRID_CELL_SIZE, 0)
            glVertex3f(x, y + GRID_CELL_SIZE, 0)
    glEnd()

    # Draw Obstacles and Items
    for (x, y), type in map_data.items():
        if type == 2: # Obstacle
            glPushMatrix()
            glColor3f(1.0, 0.2, 0.2) # Bright Red
            glTranslatef(x + GRID_CELL_SIZE/2, y + GRID_CELL_SIZE/2, 25)                     
            glutSolidCube(50)
            glPopMatrix()
        elif type == 3: # Diamond
            glPushMatrix()
            glTranslatef(x + GRID_CELL_SIZE/2, y + GRID_CELL_SIZE/2, 25)
            # Add a simple rotation animation based on time_count if available, else static
            glRotatef(time_count * 2, 0, 0, 1) 
            draw_diamond()
            glPopMatrix()
        elif type == 4 or type == 5: # Power-ups
            glPushMatrix()
            glTranslatef(x + GRID_CELL_SIZE/2, y + GRID_CELL_SIZE/2, 25)
            draw_powerups(type)
            glPopMatrix()
        elif type == 6: # Portal
            glPushMatrix()
            # 1. Translate to position
            glTranslatef(x + GRID_CELL_SIZE/2, y + GRID_CELL_SIZE/2, 25)
            
            # 2. Rotate in place (if active)
            if diamonds_collected >= diamonds_needed:
                glColor3f(1.0, 0.84, 0.0) # Gold (Active)
                glRotatef(time_count * 5, 0, 1, 0) # Spin fast
            else:
                glColor3f(0.5, 0.5, 0.5) # Grey (Inactive)
            
            glutSolidCube(40) # Allowed portal shape
            glPopMatrix()
            
    # Draw Moving Objects & Guidelines
    for obj in moving_objects:
        px, py = obj['pos']
        
        # Guide Line (Yellow)
        glColor3f(1.0, 1.0, 0.0) 
        glBegin(GL_LINES)
        if obj['axis'] == 0:
            glVertex3f(obj['range'][0], py + 25, 5)
            glVertex3f(obj['range'][1], py + 25, 5)
        else:
            glVertex3f(px + 25, obj['range'][0], 5)
            glVertex3f(px + 25, obj['range'][1], 5)
        glEnd()
        
        # Draw Object
        glPushMatrix()
        glTranslatef(px + GRID_CELL_SIZE/2, py + GRID_CELL_SIZE/2, 25)
        
        if obj['type'] == 2: # Wall
            # Pulsing Warning Color
            pulse = abs(math.sin(time_count * 0.1))
            glColor3f(1.0, pulse, pulse) # Pulses Red to White
            glutSolidCube(50)
        elif obj['type'] == 1: # Moving Hole (Black Box representing void)
            # Pulsing Void Color
            pulse = abs(math.sin(time_count * 0.1)) * 0.3
            glColor3f(pulse, 0.0, pulse) # Pulses Dark Purple
            glScalef(1.0, 1.0, 0.1) # Flat
            glutSolidCube(50)
            
        glPopMatrix()

    # Draw Walls
    wall_h = 50
    # Steel Blue Walls
    wall_color = (0.3, 0.4, 0.6) 
    
    glColor3f(*wall_color) # Left
    glBegin(GL_QUADS)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0); glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, wall_h); glVertex3f(-GRID_LENGTH, -GRID_LENGTH, wall_h)
    glEnd()
    
    glColor3f(*wall_color) #Right
    glBegin(GL_QUADS)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0); glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, wall_h); glVertex3f(-GRID_LENGTH, GRID_LENGTH, wall_h)
    glEnd()

    glColor3f(*wall_color) #Back
    glBegin(GL_QUADS)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0); glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, wall_h); glVertex3f(GRID_LENGTH, -GRID_LENGTH, wall_h)
    glEnd()
    
    glColor3f(*wall_color) #Front
    glBegin(GL_QUADS)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0); glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, wall_h); glVertex3f(-GRID_LENGTH, -GRID_LENGTH, wall_h)
    glEnd()

def draw_player():
    global player_pos, time_count, falling
    
    glPushMatrix()
    glTranslatef(player_pos[0], player_pos[1], player_pos[2])
    
    if falling:
        glColor3f(1, 0, 0)
    else:
        glColor3f(1.0, 0.7, 0.0) # Golden Orange
        
    gluSphere(gluNewQuadric(), ball_radius, 32, 30)
    glPopMatrix()


# Physics
def check_collisions():
    global player_pos, player_vel, falling, game_over, score, lives, powerup_active, powerup_timer, level, diamonds_collected, diamonds_needed, has_won_level, portal_pos, moving_objects
    
    if player_pos[0] > GRID_LENGTH - ball_radius:#hit with Boundaries
        player_pos[0] = GRID_LENGTH - ball_radius
        player_vel[0] *= -0.8#bounce back
    elif player_pos[0] < -GRID_LENGTH + ball_radius:
        player_pos[0] = -GRID_LENGTH + ball_radius
        player_vel[0] *= -0.8
        
    if player_pos[1] > GRID_LENGTH - ball_radius:
        player_pos[1] = GRID_LENGTH - ball_radius
        player_vel[1] *= -0.8
    elif player_pos[1] < -GRID_LENGTH + ball_radius:
        player_pos[1] = -GRID_LENGTH + ball_radius
        player_vel[1] *= -0.8

    # hit with holes or obstecal
    gx = int(player_pos[0] // GRID_CELL_SIZE) * GRID_CELL_SIZE
    gy = int(player_pos[1] // GRID_CELL_SIZE) * GRID_CELL_SIZE
    
    tile_type = map_data.get((gx, gy), 0)
    
    if tile_type == 1: # Hole
        falling = True
    elif tile_type == 2: # Obstacle
        player_vel[0] *= -1.2#bounce back
        player_vel[1] *= -1.2
        player_pos[0] += player_vel[0] * 2
        player_pos[1] += player_vel[1] * 2
    elif tile_type == 3: # Diamond
        score += 10
        diamonds_collected += 1
        map_data[(gx, gy)] = 0 # Remove item
        print(f"Score: {score} | Diamonds: {diamonds_collected}/{diamonds_needed}")
    elif tile_type == 4: # Speed Boost
        powerup_active = True
        powerup_timer = 600 # frames
        map_data[(gx, gy)] = 0
        print("Speed Boost Activated!")
    elif tile_type == 5: # Extra Life
        lives += 1
        map_data[(gx, gy)] = 0
        print(f"Extra Life! Lives: {lives}")
    elif tile_type == 6: # Portal
        if diamonds_collected >= diamonds_needed:
            # Level Complete!
            print(f"Level {level} Complete!")
            level += 1
            game_over = False 
            falling = False
            player_pos = [0, 0, 20]
            player_vel = [0, 0, 0]
            init_map()
        else:
            print(f"Portal Locked! Need {diamonds_needed - diamonds_collected} more cores.")

    # Collision with Moving Objects
    for obj in moving_objects:
        ox, oy = obj['pos']
        # Simple AABB
        if (player_pos[0] > ox and player_pos[0] < ox + GRID_CELL_SIZE and
            player_pos[1] > oy and player_pos[1] < oy + GRID_CELL_SIZE):
            
            if obj['type'] == 2: # Moving Wall -> Push
                # Push player in direction of movement
                if obj['axis'] == 0:
                    player_pos[0] += obj['vel']
                else:
                    player_pos[1] += obj['vel']
            elif obj['type'] == 1: # Moving Hole -> Fall
                falling = True


def idle():
    global player_pos, player_vel, falling, game_over, time_count, lives, powerup_active, powerup_timer, crumble_timer
    
    if game_over:
        return
    time_count += 1
    
    if falling:
        player_pos[2] -= gravity * 4
        player_vel[0] *= 0.99
        player_vel[1] *= 0.99
        if player_pos[2] < -700:
            if lives > 0:
                # Respawn logic
                lives -= 1
                falling = False
                player_pos = [0, 0, 20]
                player_vel = [0, 0, 0]
                print(f"Respawned! Lives left: {lives}")
            else:
                game_over = True
    else:
        # Handle Power-up Timer
        current_acc = player_acc
        current_friction = friction
        if powerup_active:
            if powerup_timer > 0:
                powerup_timer -= 1
                current_acc = player_acc * 2.0 # Double acceleration
                current_friction = 0.985 # Less friction
            else:
                powerup_active = False
                print("Speed Boost Ended")

        player_vel[0] *= current_friction
        player_vel[1] *= current_friction
        
        
        player_pos[0] += player_vel[0]
        player_pos[1] += player_vel[1]
        
        check_collisions()

        # Continuous Input Handling (Smooth Movement)
        eff_acc = player_acc * 0.15 # Reduced acceleration since it applies every frame
        if powerup_active:
             eff_acc *= 2.0
             

    # Update Moving Objects
    for obj in moving_objects:
        a = obj['axis']
        obj['pos'][a] += obj['vel']
        
        if obj['pos'][a] > obj['range'][1] or obj['pos'][a] < obj['range'][0]:
            obj['vel'] *= -1

    # Level 5: Meltdown
    if level >= 5 and not falling and not game_over:
        crumble_timer += 1
        if crumble_timer > 120: # Every ~2 seconds 
            crumble_timer = 0
            # Pick a safe spot nearby and destroy it
            cx = (player_pos[0] // GRID_CELL_SIZE) * GRID_CELL_SIZE
            cy = (player_pos[1] // GRID_CELL_SIZE) * GRID_CELL_SIZE 
            
            # Try 5 times to find a safe spot
            for _ in range(5):
                off_x = random.randint(-4, 4) * GRID_CELL_SIZE
                off_y = random.randint(-4, 4) * GRID_CELL_SIZE
                target = (cx + off_x, cy + off_y)
                
                if map_data.get(target) == 0:
                    map_data[target] = 1 # Turning into Hole!
                    break

    glutPostRedisplay()


#Controls
def keyboardListener(key, x, y):
    global player_vel, game_over, player_pos, falling, is_first_person, score, lives, powerup_active, powerup_timer

    # Track key press
    # Discrete Input Logic
    eff_acc = player_acc 
    if powerup_active: eff_acc *= 2.0
    
    if not game_over and not falling:
        if key == b'w': player_vel[0] += eff_acc
        if key == b's': player_vel[0] -= eff_acc
        if key == b'a': player_vel[1] += eff_acc
        if key == b'd': player_vel[1] -= eff_acc

    if key == b'r':#reset

        score = 0
        lives = 3
        game_over = False
        falling = False
        level = 1 # Reset level
        
        player_pos = [0, 0, 20]
        player_vel = [0, 0, 0]
        powerup_active = False
        powerup_timer = 0
        
        init_map() 
        print("Game Restarted (Level 1)")
        
    glutPostRedisplay()

def keyboardUpListener(key, x, y):
    # Track key release
    if key in keys_pressed:
        keys_pressed.remove(key)
    glutPostRedisplay()

def specialKeyListener(key, x, y):
    global camera_angle_h, camera_angle_v
    if key == GLUT_KEY_UP:
        camera_angle_v = min(1.5, camera_angle_v + 0.05)
    if key == GLUT_KEY_DOWN:
        camera_angle_v = max(0.1, camera_angle_v - 0.05)
    if key == GLUT_KEY_RIGHT:
        camera_angle_h -= 0.05
    if key == GLUT_KEY_LEFT:
        camera_angle_h += 0.05
    glutPostRedisplay()

def mouseListener(button, state, x, y):
    global is_first_person
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        is_first_person = not is_first_person
    glutPostRedisplay()

def setupCamera():
    global camera_angle_h, camera_angle_v, camera_zoom, is_first_person, player_pos
    
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, W_WIDTH/W_HEIGHT, 0.1, 4500)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if is_first_person:#first person
        eyeX = player_pos[0]
        eyeY = player_pos[1]
        eyeZ = player_pos[2] + ball_radius + 5#camera at top of the ball
        
        
        targetX = eyeX + math.cos(camera_angle_h) * 200
        targetY = eyeY + math.sin(camera_angle_h) * 200
        targetZ = eyeZ + (camera_angle_v - 0.5) * 200 
        
        gluLookAt(eyeX, eyeY, eyeZ, 
                  targetX, targetY, targetZ,
                  0, 0, 1)
    else:
        
        eyeX = player_pos[0] - math.cos(camera_angle_h) * camera_zoom#THIRD PERSON
        eyeY = player_pos[1] - math.sin(camera_angle_h) * camera_zoom
        eyeZ = camera_zoom * camera_angle_v
        
        gluLookAt(eyeX, eyeY, eyeZ,
                   player_pos[0], player_pos[1], 0, 
                   0, 0, 1)

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    setupCamera()

    draw_grid_and_walls()
    draw_player()
    
    draw_text(700, 860, "Controls: W,A,S,D Move/Camera control: Arrow keys ")
    draw_text(700, 880, "Right click: Toggle Camera (1st/3rd Person)")

    # HUD
    draw_text(10, 880, f"Score: {score}")
    draw_text(10, 860, f"Lives: {lives} | Level: {level}")
    
    if diamonds_collected < diamonds_needed:
        draw_text(10, 780, f"Cores Needed: {diamonds_collected}/{diamonds_needed}")
    else:
        glColor3f(1, 1, 0)
        draw_text(10, 780, "PORTAL ACTIVE! FIND THE EXIT!")
        
    if powerup_active:
        draw_text(10, 840, "SPEED BOOST")
        # Draw Bar at top left, below text
        # progress 0.0 to 1.0
        prog = powerup_timer / 600.0
        draw_bar(10, 820, 200, 15, prog, color=(1.0, 0.0, 1.0))
    
    if game_over:
        draw_text(400, 800, "GAME OVER! PRESS 'R'")

    glutSwapBuffers()


def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(W_WIDTH, W_HEIGHT)
    glutInitWindowPosition(100, 10)
    glutCreateWindow(b"Hazard Ball")

    glEnable(GL_DEPTH_TEST)

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)

    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    print("Hazard Ball")
    print("Press 'R' to restart with a NEW random map.")
    glutMainLoop()

if __name__ == "__main__":
    main()
