import random
import math
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
cheat_mode=False
# Teapot initial state
teapot = None 
teapot_rotation = 0.0  
teapot_invincibility = False 
teapot_timer = 0.0  
teapot_respawn_timer = 0.0  

active_bullets = []  
bullet_speed = 0.4   
bullet_size = 0.1
bullets = 5    
initial_zpos=2.0
distanceCovered=0.0
movementSpeed=0.0005
speed_increment=0.00009
max_speed= 0.15
coins= []
coinCount= 0
trees = []
tree_spacing = 8.5  
max_tree_distance = 50.0  
debris = []
debris_spawn_distance = 30.0
debris_spacing = 3.0
game_over = False
camera_mode = "third" 
score=0

width, height = 800, 600

player_x, player_z = 0.0, 2.0
player_size = 0.2
move_speed = 0.2
#road
road_segment_length = 4.0
road_width = 5.3
num_segments = 10
visible_range = 60.0
#road and vehicle
segments = []
vehicles = []
vehicle_size = 0.4
vehicle_speed = 2


def init():
    glClearColor(0.1, 0.1, 0.2, 1.0)
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, width / height, 0.4, 100)
    glMatrixMode(GL_MODELVIEW)

    for i in range(num_segments):
        segments.append({
            "z_position": i * road_segment_length,
            "active": True,
            "vehicle_present": False,
            "coin_present": False})



def spawn_vehicle():
    side = random.choice(["left", "right"])
    eligible_segments = [s for s in segments if s["z_position"] > player_z and not s["vehicle_present"]]
    if not eligible_segments:
        return

    segment = random.choice(eligible_segments)
    z_position = segment["z_position"]
    segment["vehicle_present"] = True

    if side == "left":
        x_position = -road_width / 2 + vehicle_size / 2
        
        direction = "right"
    else:
        x_position = road_width / 2 - vehicle_size / 2
        
        direction = "left"

    base_speed = 0.005 + min(score * 0.0002, 0.015)  
    speed = random.uniform(base_speed, base_speed + 0.005)

    vehicles.append({
        "x_position": x_position,
        "z_position": z_position,
        "direction": direction,
        "speed": speed})

def update_road():
    global segments, vehicles, player_x, player_z, game_over

    if game_over:
        return 

    #remove road segments that are far behind
    if segments[0]["z_position"] + road_segment_length < player_z - visible_range:
        segments.pop(0)

    #add new road ahead
    if segments[-1]["z_position"] < player_z + visible_range:
        segments.append({
            "z_position": segments[-1]["z_position"] + road_segment_length,
            "active": True,
            "vehicle_present": False,
            "coin_present": False})

    #vehicle spawning on spawnchance
    spawn_chance = min(0.02 + score * 0.0005, 0.1)  
    if random.random() < spawn_chance:
        if spawn_chance>0.1:
            print("BRUHHHHHH")
        spawn_vehicle()

    spawn_chance_coin = min(0.04 + score * 0.0005, 0.15)

    #spawn coins on chance
    if random.random() < spawn_chance_coin:
        spawn_coin_batch()

    #updating vehicle positions
    for vehicle in vehicles:
        if vehicle["direction"] == "left":
            vehicle["x_position"] -= vehicle["speed"]
        else:
            vehicle["x_position"] += vehicle["speed"]

    #outofbounds remove
    vehicles = [v for v in vehicles if (-road_width / 2 - vehicle_size) <= v["x_position"] <= (road_width / 2 + vehicle_size)]

    #Update segment vehicle flags
    for segment in segments:
        segment["vehicle_present"] = any(abs(v["z_position"] - segment["z_position"]) < 0.01 for v in vehicles)

    #collision with the player
    for vehicle in vehicles:
        if not teapot_invincibility and \
           abs(vehicle["x_position"] - player_x) < (vehicle_size / 2 + player_size / 2) and \
           abs(vehicle["z_position"] - player_z) < (vehicle_size / 2 + player_size / 2):
            print("Game Over! The player was hit by a car.")
            game_over = True  
            return 
        
def draw_starting():
    glPushMatrix()
    glColor3f(48/255,93/255,75/255)
    glRotatef(-90,1,0,0)
    glTranslatef(-3,0,0)
    glBegin(GL_QUADS)
    glVertex3f(0,200,0)
    glVertex3f(0,0,0)
    glVertex3f(800,0,0)
    glVertex3f(200,0,0)
    glEnd()
    glPopMatrix()


def update_bullets():
    global active_bullets, vehicles

    #Move bullets forward
    for bullet in active_bullets:
        bullet["z_position"] += bullet_speed

    #Check for collisions with vehicles
    for bullet in active_bullets[:]:
        for vehicle in vehicles[:]:
            collision_range = 0.2 

            if abs(bullet["x_position"] - vehicle["x_position"]) < (vehicle_size / 2 + collision_range) and \
               abs(bullet["z_position"] - vehicle["z_position"]) < (vehicle_size / 2 + collision_range):
                vehicles.remove(vehicle)  
                active_bullets.remove(bullet)  
                print("Shot a car!")
                break

    #Remove bullets that go out of bounds
    active_bullets = [b for b in active_bullets if b["z_position"] < player_z + visible_range]

def draw_road():
    draw_starting()
    glPushMatrix()
    for segment in segments:
        is_road = int(segment["z_position"] / road_segment_length) % 2 == 0

        if is_road:
            glColor3f(36/255,33/255,42/255)  
        else:
            glColor3f(48/255,93/255,75/255)  

        # drawing
        glBegin(GL_QUADS)
        glVertex3f(-road_width / 2, -0.05, segment["z_position"])
        glVertex3f(road_width / 2, -0.05, segment["z_position"])
        glVertex3f(road_width / 2, -0.05, segment["z_position"] + road_segment_length)
        glVertex3f(-road_width / 2, -0.05, segment["z_position"] + road_segment_length)
        glEnd()

        #road marking
        if is_road:
            glColor3f(1.0, 1.0, 1.0)  
            mark_width = 0.6           
            mark_thickness = 0.1       
            mark_gap = 0.7             

            start_x = -road_width / 2 + mark_gap            
            end_x = road_width / 2 - mark_width - mark_gap  

            x = start_x
            while x <= end_x:
                glBegin(GL_QUADS)
                glVertex3f(x, -0.04, segment["z_position"] + road_segment_length / 2 - mark_thickness / 2)
                glVertex3f(x + mark_width, -0.04, segment["z_position"] + road_segment_length / 2 - mark_thickness / 2)
                glVertex3f(x + mark_width, -0.04, segment["z_position"] + road_segment_length / 2 + mark_thickness / 2)
                glVertex3f(x, -0.04, segment["z_position"] + road_segment_length / 2 + mark_thickness / 2)
                glEnd()

                x += mark_width + mark_gap
    glPopMatrix()



def draw_player():
    glPushMatrix()
    glTranslatef(player_x, 0.0, player_z)
    glRotatef(-90, 1, 0, 0)
    glColor3f(1.0, 1.0, 1.0)
    glutSolidCone(0.1,0.4,32,32)
    glPopMatrix()

    #head
    glPushMatrix()
    glTranslatef(player_x,0.4,player_z)
    glColor3f(1,1,1)
    glutSolidSphere(0.080,32,32)
    glPopMatrix()

    #hat
    glPushMatrix()
    glTranslate(player_x,0.40,player_z)
    glRotatef(-90, 1, 0, 0)
    glColor3f(200/255,54/255,67/255)
    glutSolidCone(0.08,0.25,32,32)
    glPopMatrix()

def draw_circle(x, y, z, radius, slices=30):
    glBegin(GL_POLYGON)
    for i in range(slices):
        angle = 2 * math.pi * i / slices
        glVertex3f(x + radius * math.cos(angle), y, z + radius * math.sin(angle))
    glEnd()


def draw_wheel(x, y, z, radius, rotation_angle):
    glPushMatrix()
    glTranslatef(x, y, z) 
    glColor3f(36/255, 75/255, 117/255)
    glRotatef(rotation_angle, 1, 0, 0)  
    
    draw_circle(0, 0, 0, radius)        
    glPopMatrix()


def draw_vehicles():
    for vehicle in vehicles:
        sf=0.09
        glPushMatrix()
        glTranslatef(vehicle["x_position"], 0.0, vehicle["z_position"])

        #mainbody
        glColor3f( 189/255,  67/255, 54/255)
        glTranslatef(0.0,0,0.0)
        glScalef(2,1.0,0.79)
        glutSolidCube(0.4)
        glPopMatrix()

        #left part
        glPushMatrix()
        glTranslatef(vehicle["x_position"], 0.0, vehicle["z_position"])
        glColor3f(210/255, 209/255, 185/255)
        glTranslatef(0,0.34,0)
        glScalef(1.5,1.0,0.79)
        glutSolidCube(0.25)
        glPopMatrix()
        
        wheel_radius = 0.1
        wheel_offset = 0.2  
        wheel_rotation = 90
        draw_wheel(vehicle["x_position"] - wheel_offset, 0.03, vehicle["z_position"] - 0.35, wheel_radius, wheel_rotation)

        #Rear right wheel
        draw_wheel(vehicle["x_position"] + wheel_offset, 0.03, vehicle["z_position"] - 0.35, wheel_radius, wheel_rotation)


def draw_trees():
    for tree in trees:
        glPushMatrix()
        glTranslatef(tree["x"], 0.0, tree["z"])

        #trunk
        glColor3f(76/255, 44/255, 44/255)  
        glPushMatrix()
        glTranslatef(0.0, 0.0, 0.0)
        glScalef(0.2, 3.0, 0.1)
        glutSolidCube(1.0)
        glPopMatrix()

        #leaves
        glColor3f(22/255, 113/255, 126/255)  
        glTranslatef(0.0, 1.75, 0.0)         #Moving to top of trunk

        num_fronds = 12
        frond_length = 1.5

        for i in range(num_fronds):
            glPushMatrix()

            downward_tilt = random.uniform(40, 45)

            glRotatef(downward_tilt, 1, 0, 0)

            #rotate around the trunk
            glRotatef((360 / num_fronds) * i, 0, 1, 0)

            glScalef(0.1, 0.1, frond_length)
            glutSolidSphere(1.0, 6, 6)

            glPopMatrix()

        glPopMatrix()



def update_trees():
    global trees

    #Find farthest z among existing trees
    farthest_z = max([tree["z"] for tree in trees], default=player_z)

    #generating trees ahead
    while farthest_z < player_z + max_tree_distance:
        farthest_z += tree_spacing

        trees.append({
            "x": -road_width / 2 - 1.0,
            "z": farthest_z
        })
        trees.append({
            "x": road_width / 2 + 1.0,
            "z": farthest_z
        })

    #Removing trees that are too far behind
    trees = [tree for tree in trees if tree["z"] > player_z - 10.0]

def draw_desert_ground():
    glPushMatrix()
    glColor3f(191/255,116/255,100/255) 
    glBegin(GL_QUADS)
    glVertex3f(-100.0, -0.06, player_z - 50.0)
    glVertex3f(100.0, -0.06, player_z - 50.0)
    glVertex3f(100.0, -0.06, player_z + 200.0)
    glVertex3f(-100.0, -0.06, player_z + 200.0)
    glEnd()
    glPopMatrix()




def draw_sunset():
    glPushMatrix()
    glDisable(GL_LIGHTING)

    #Sun position 
    sunset_distance = player_z + visible_range + 2.0  

    #background sky 
    glBegin(GL_QUADS)
    glColor3f(1.0, 0.5, 0.2)   
    glVertex3f(-100, -1.0, sunset_distance)
    glVertex3f(100, -1.0, sunset_distance)
    glColor3f(0.6, 0.0, 0.6)  
    glVertex3f(100, 40.0, sunset_distance)
    glVertex3f(-100, 40.0, sunset_distance)
    glEnd()

    #sun
    glColor3f(254/255,212/255,153/255)  
    glTranslatef(0.0, 1.0, sunset_distance - 0.5)  
    glutSolidSphere(5.0, 32, 32) 
    glPopMatrix()


def draw_mountain(x, y, z):
    glPushMatrix()
    glTranslatef(x, y, z)
    glScalef(3.0, 3.0, 1.0)
    glDisable(GL_DEPTH_TEST)  

    #Base layer 
    glColor3f(102/255, 49/255, 8/255)
    glBegin(GL_TRIANGLES)
    glVertex3f(-1.0, 0.0, 0.0)
    glVertex3f(1.0, 0.0, 0.0)
    glVertex3f(0.0, 1.0, 0.0)
    glEnd()

    #Middle layer
    glColor3f(93/255, 45/255, 8/255)
    glBegin(GL_TRIANGLES)
    glVertex3f(-0.8, 0.0, 0.01)
    glVertex3f(0.8, 0.0, 0.01)
    glVertex3f(0.0, 0.8, 0.01)
    glEnd()

    # Top layer 
    glColor3f(79/255, 45/255, 8/255)
    glBegin(GL_TRIANGLES)
    glVertex3f(-0.5, 0.0, 0.02)
    glVertex3f(0.5, 0.0, 0.02)
    glVertex3f(0.0, 0.5, 0.02)
    glEnd()
    glEnable(GL_DEPTH_TEST)  
    glPopMatrix()




def draw_mountain_range():
    global player_x,player_y
    spacing = 5
    z_base = player_z + 50  

    for i in range(-100, 101, spacing): 
        if i >5 or i<-5:
            draw_mountain(i, 0.0, z_base ) 
        


def draw_bullets():
    global active_bullets

    glColor3f(204/255, 0, 0.0)  
    for bullet in active_bullets:
        glPushMatrix()
        glTranslatef(bullet["x_position"], 0.2, bullet["z_position"])  #Adjusting height
        glutSolidSphere(bullet_size, 16, 16) 
        glPopMatrix()


def draw_debris():
    for d in debris:
        glPushMatrix()
        glTranslatef(d["x"], 0.0, d["z"])

        if d["type"] == "rock":
            glColor3f(0.3, 0.3, 0.3)
            glutSolidSphere(d["size"], 8, 8)
        elif d["type"] == "bone":
            glColor3f(102/255,51/255,0/255)
            glScalef(0.1, 0.1, 0.5)
            glutSolidCube(d["size"] * 10)

        glPopMatrix()



def update_debris():
    global debris

    farthest_z = max([d["z"] for d in debris], default=player_z)
    while farthest_z < player_z + debris_spawn_distance:
        farthest_z += debris_spacing

        #random left/right 
        side = random.choice([-1, 1])
        x_pos = side * random.uniform(3.0, 15.0)

        debris.append({
            "x": x_pos,
            "z": farthest_z,
            "size": random.uniform(0.1, 0.9),
            "type": random.choice(["rock", "bone"])})

    #removing debris from behind
    debris = [d for d in debris if d["z"] > player_z - 10.0]



def fire_bullet():
    global bullets, active_bullets, game_over

    # Add a new bullet at the player's position
    active_bullets.append({
        "x_position": player_x,
        "z_position": player_z + 0.5,})

    bullets -= 1 
    print(f"Bullets left: {bullets}")

    
    if bullets == 0:
        print("No bullets left!")
          
        
def draw_distance():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, width, 0, height)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    #coins
    glColor3f(1.0, 1.0, 0.0)  
    coins_text = f"Coins: {coinCount}"
    glRasterPos2f(10, height - 25)
    for ch in coins_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    #bullets
    glColor3f(0.0, 1.0, 0.0) 
    bullets_text = f"Bullets: {bullets}"
    glRasterPos2f(10, height - 75)
    for ch in bullets_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_score():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, width, 0, height)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(1.0, 1.0, 0.0)
    score_text = f"Score: {score}"
    glRasterPos2f(10, height - 50)

    for ch in score_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_game_over():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, width, 0, height)  

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glDisable(GL_DEPTH_TEST)
    glColor3f(0.0, 0.0, 0.0)
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(width, 0)
    glVertex2f(width, height)
    glVertex2f(0, height)
    glEnd()

    glColor3f(1.0, 0.0, 0.0)
    glRasterPos2f(width // 2 - 50, height // 2 + 10)

    for c in "YOU DIED":
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))

    glColor3f(1.0, 1.0, 1.0)
    glRasterPos2f(width // 2 - 90, height // 2 - 20)

    for c in "PRESS R TO RESTART":
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))

    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()


def spawn_coin_batch():
    global coins

    eligible_segments = [
        s for s in segments
        if int(s["z_position"] / road_segment_length) % 2 == 0
        and not s["coin_present"]
        and not s["vehicle_present"]
        and s["z_position"] > player_z]

    if not eligible_segments:
        return

    segment = random.choice(eligible_segments)
    segment["coin_present"] = True  

    batch_size = random.randint(2, 5)
    gap = 0.5  
    x_pos = random.uniform(-road_width / 2 + 0.5, road_width / 2 - 0.5)
    z_start = segment["z_position"] + road_segment_length / 2

    for i in range(batch_size):
        z = z_start + i * gap 
        coins.append({
            "x": x_pos,
            "z": z,
            "collected": False})

def draw_coins():
    for coin in coins:
        if not coin["collected"]:
            glPushMatrix()
            glTranslatef(coin["x"], 0.2, coin["z"])
            glColor3f(1.0, 0.84, 0.0)
            glutSolidSphere(0.1, 16, 16)
            glPopMatrix()


def coin_collision():
    global coinCount
    for coin in coins:
        if not coin["collected"]:
            if abs(player_x - coin["x"]) < 0.25 and abs(player_z - coin["z"]) < 0.25:
                coin["collected"] = True
                coinCount += 1
                print(f"Coins collected: {coinCount}")


def spawn_teapot():
    global teapot, teapot_respawn_timer

    if teapot is None and teapot_respawn_timer <= 0:
        if distanceCovered > 50 and random.random() < 0.1:
            teapot = {
                "x": random.uniform(-road_width / 2 + 0.5, road_width / 2 - 0.5),
                "z": player_z + visible_range - 10,
                "collected": False}
            print("Teapot spawned!")

    elif teapot is None:
        teapot_respawn_timer -= 0.016  


def draw_teapot():
    global teapot, teapot_rotation

    if teapot and not teapot["collected"]:
        glPushMatrix()
        glTranslatef(teapot["x"], 0.5, teapot["z"])  
        glRotatef(teapot_rotation, 0, 1, 0)  
        glColor3f(1.0, 0.5, 0.0)  
        glutSolidTeapot(0.3)
        glPopMatrix()

        #rotation update
        teapot_rotation += 2.0
        if teapot_rotation >= 360.0:
            teapot_rotation -= 360.0   



def teapot_collision():
    global teapot, teapot_invincibility, teapot_timer

    if teapot and not teapot["collected"]:
        if abs(player_x - teapot["x"]) < 0.25 and abs(player_z - teapot["z"]) < 0.25:
            teapot["collected"] = True
            teapot_invincibility = True
            teapot_timer = 5.0  
            print("Teapot collected! Invincibility activated for 3 seconds.")   


def update_teapot():
    global teapot, teapot_invincibility, teapot_timer, teapot_respawn_timer

    if teapot_invincibility:
        teapot_timer -= 0.016  
        if teapot_timer <= 0:
            teapot_invincibility = False
            print("Invincibility expired.")
            teapot_timer = 0.0

    if teapot and teapot["collected"]:
        teapot = None
        teapot_respawn_timer = 5.0 
        
                 
                
def draw_powerup_circle(x, y, radius, text, key):
    #circel
    glColor3f(0.0, 0.0, 0.0)  
    glBegin(GL_LINE_LOOP)
    for i in range(30):  
        angle = 2 * math.pi * i / 30
        glVertex2f(x + radius * math.cos(angle), y + radius * math.sin(angle))
    glEnd()

    # txt
    glColor3f(1.0, 0.0, 0.0)  
    lines = text.split()  
    line_height = 12  
    for i, line in enumerate(lines):
        text_width = len(line) * 7  
        glRasterPos2f(x - text_width / 2, y + (len(lines) - i - 1) * line_height - 5)  
        for c in line:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(c))  

    # jkl label
    glColor3f(1.0, 0.0, 0.0)  
    glRasterPos2f(x - 5, y - radius - 15)  
    for c in key:  
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))


def draw_powerup_keys():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, width, 0, height)  

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

   
    draw_powerup_circle(width - 300, 100, 30, "+1 Bullet", "j")  
    draw_powerup_circle(width - 200, 100, 30, "Halved Speed", "k")  
    draw_powerup_circle(width - 100, 100, 30, "Bomb", "l")

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)               

def display():
    global game_over,initial_zpos,distanceCovered,score,player_z,movementSpeed,vehicle_speed

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    if game_over:
        draw_game_over()
        glutSwapBuffers()
        return 

    distanceCovered=player_z-initial_zpos
    
    movementSpeed=min(movementSpeed+speed_increment,max_speed)
    player_z+=movementSpeed
    score=int(distanceCovered/10)
    # vehicle_speed+=speed_increment
    # vehicle_speed=min(vehicle_speed,1)


    if camera_mode == "third":
        cam_x = player_x
        cam_y = 1.5
        cam_z = player_z - 5
        gluLookAt(cam_x, cam_y, cam_z,
                player_x, 0.0, player_z,
                0.0, 1.0, 0.0)
    else:  
        cam_x = player_x
        cam_y = 0.5
        cam_z = player_z + 0.1  
        look_z = player_z + 5.0
        gluLookAt(cam_x, cam_y, cam_z,
                cam_x, cam_y, look_z,
                0.0, 1.0, 0.0)

    draw_sunset()
    draw_mountain_range()
    draw_desert_ground()
    update_debris()
    draw_debris()
    update_trees()
    draw_trees()

    update_road()
    draw_road()
    draw_vehicles()
    draw_player()
    update_bullets()
    draw_bullets()
    draw_coins()
    
    coin_collision()
    
    draw_distance()
    draw_score()
    # Teapot logic
    spawn_teapot()
    update_teapot()
    teapot_collision()  
    draw_teapot()
    # Draw power-up keys
    # draw_powerup_circle()
    draw_powerup_keys()
    glutSwapBuffers()



def keyboard(key, x, y):
    global player_x, player_z, bullets, game_over, vehicles, distanceCovered, initial_zpos, move_speed, movementSpeed, speed_increment, segments,coinCount, camera_mode,cheat_mode
    key = key.decode("utf-8").lower()

    if game_over and key == 'r':
        player_x = 0.0
        player_z = initial_zpos
        bullets = 5
        movementSpeed = 0.001
        speed_increment = 0.0001
        vehicles.clear()
        distanceCovered = 0.0
        game_over = False
        cheat_mode=False
        coinCount = 0
        coins.clear()
        trees.clear()
        debris.clear()
        segments.clear()
        for i in range(num_segments):
            segments.append({
                "z_position": i * road_segment_length,
                "active": True,
                "vehicle_present": False,
                "coin_present": False
            })

        return
    
    if not game_over:
        if key=='c':
            cheat_mode=not cheat_mode
            print("CHEAT MODE:",cheat_mode)
            print("CHEAT MODE:",cheat_mode)

        if key == 'w':  
            camera_mode = "first" if camera_mode == "third" else "third"
        elif key == 'a':
            player_x += move_speed  
            if player_x > road_width / 2 - player_size / 2:
                player_x = road_width / 2 - player_size / 2
        elif key == 'd':
            player_x -= move_speed  
            if player_x < -road_width / 2 + player_size / 2:
                player_x = -road_width / 2 + player_size / 2
        elif key == ' ' and bullets > 0:
            fire_bullet()
        # Powerup 1: Increase bullet count by 1
        elif key == 'j':
            if cheat_mode==False:
                if coinCount >= 5 and bullets < 5:
                    bullets += 1
                    coinCount -= 5
                    print("Powerup Activated: +1 Bullet")
                elif bullets >= 5:
                    print("Max bullets reached!")
                else:
                    print("Not enough coins for Bullet Powerup!")
            else:
                if coinCount >= 0 and bullets < 5:
                    bullets += 1
                    
                    print("Powerup Activated: +1 Bullet")
                elif bullets >= 5:
                    print("Max bullets reached!")
                else:
                    print("Not enough coins for Bullet Powerup!")


        # Powerup 2: Halve movement speed
        elif key == 'k':
            
            if coinCount >= 10:
                movementSpeed = max(movementSpeed / 2, 0.001)
                coinCount -= 10
                print("Powerup Activated: Halved Speed")
            else:
                print("Not enough coins for Slowdown Powerup!")

        # Powerup 3: Bomb - Destroy vehicles in range
        elif key == 'l':
            if cheat_mode==False:
                if coinCount >= 20:
                    bomb_radius = 15.0  
                    vehicles[:] = [v for v in vehicles if math.hypot(v["x_position"] - player_x, v["z_position"] - player_z) > bomb_radius]
                    coinCount -= 20
                    print("Powerup Activated: Bomb!")
                else:
                    print("Not enough coins for Bomb Powerup!")
            else:
                if coinCount >= 0:
                    bomb_radius = 15.0  
                    vehicles[:] = [v for v in vehicles if math.hypot(v["x_position"] - player_x, v["z_position"] - player_z) > bomb_radius]
                    coinCount -= 0
                    print("Powerup Activated: Bomb!")
                else:
                    print("Not enough coins for Bomb Powerup!")
                


    glutPostRedisplay()




glutInit()
glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
glutInitWindowSize(width, height)
glutInitWindowPosition(100, 100)
glutCreateWindow(b"Run To Survive 3D")

init()
glutDisplayFunc(display)
glutKeyboardFunc(keyboard)
glutIdleFunc(display)
glutMainLoop()


