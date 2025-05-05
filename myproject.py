# Import necessary libraries
import random  # For random number generation
import math  # For mathematical calculations
from OpenGL.GL import *  # OpenGL functions for rendering
from OpenGL.GLUT import *  # GLUT functions for window and input handling
from OpenGL.GLU import *  # GLU functions for higher-level utilities
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18  # Font for rendering text

# Global variables for game state and settings
cheat_mode = False  # Cheat mode toggle
teapot = None  # Stores the teapot's position and state
teapot_rotation = 0.0  # Rotation angle for the teapot
teapot_invincibility = False  # Whether the player is invincible
teapot_timer = 0.0  # Timer to track invincibility duration
teapot_respawn_timer = 0.0  # Teapot respawn timer

# Bullet-related variables
active_bullets = []  # List to store active bullets
bullet_speed = 0.4  # Speed of bullets
bullet_size = 0.1  # Size of bullets
bullets = 5  # Initial bullet count

# Player and game state variables
initial_zpos = 2.0  # Initial z-position of the player
distanceCovered = 0.0  # Distance covered by the player
movementSpeed = 0.001  # Initial movement speed of the player
speed_increment = 0.00007  # Speed increment per frame
max_speed = 0.22  # Maximum movement speed
coins = []  # List to store coins
coinCount = 0  # Number of coins collected
trees = []  # List to store tree positions
tree_spacing = 8.5  # Spacing between trees
max_tree_distance = 50.0  # Maximum distance for trees
debris = []  # List to store debris
debris_spawn_distance = 30.0  # Distance to spawn debris
debris_spacing = 3.0  # Spacing between debris
game_over = False  # Game over state
camera_mode = "third"  # Camera mode (third-person or first-person)
score = 0  # Player's score

# Window dimensions
width, height = 800, 600  # Width and height of the window

# Player dimensions and position
player_x, player_z = 0.0, 2.0  # Initial x and z positions of the player
player_size = 0.2  # Size of the player
move_speed = 0.2  # Speed of player movement

# Road parameters
road_segment_length = 4.0  # Length of each road segment
road_width = 5.3  # Width of the road
num_segments = 10  # Number of road segments
visible_range = 60.0  # Visible range of the road

# Road and vehicle data
segments = []  # List to store road segments
vehicles = []  # List to store vehicles

# Vehicle parameters
vehicle_size = 0.4  # Size of vehicles
vehicle_speed = 2  # Speed of vehicles

# Initialize OpenGL settings and road segments
def init():
    glClearColor(0.1, 0.1, 0.2, 1.0)  # Set background color (dark blue)
    glEnable(GL_DEPTH_TEST)  # Enable depth testing for 3D rendering
    glMatrixMode(GL_PROJECTION)  # Set projection matrix mode
    glLoadIdentity()  # Reset the projection matrix
    gluPerspective(45, width / height, 0.4, 100)  # Set perspective projection
    glMatrixMode(GL_MODELVIEW)  # Set model-view matrix mode

    # Initialize road segments
    for i in range(num_segments):
        segments.append({
            "z_position": i * road_segment_length,  # Position of the segment
            "active": True,  # Whether the segment is active
            "vehicle_present": False,  # Whether a vehicle is present
            "coin_present": False  # Whether a coin is present
        })

# Function to spawn a vehicle
def spawn_vehicle():
    side = random.choice(["left", "right"])  # Randomly choose left or right side
    eligible_segments = [s for s in segments if s["z_position"] > player_z and not s["vehicle_present"]]
    if not eligible_segments:
        return  # Exit if no eligible segments

    segment = random.choice(eligible_segments)  # Choose a random eligible segment
    z_position = segment["z_position"]  # Get the z-position of the segment
    segment["vehicle_present"] = True  # Mark the segment as having a vehicle

    # Set vehicle position and direction based on the side
    if side == "left":
        x_position = -road_width / 2 + vehicle_size / 2
        direction = "right"
    else:
        x_position = road_width / 2 - vehicle_size / 2
        direction = "left"

    # Calculate vehicle speed based on score
    base_speed = 0.005 + min(score * 0.0002, 0.015)
    speed = random.uniform(base_speed, base_speed + 0.005)

    # Add the vehicle to the list
    vehicles.append({
        "x_position": x_position,
        "z_position": z_position,
        "direction": direction,
        "speed": speed
    })

# Function to update the road and vehicles
def update_road():
    global segments, vehicles, player_x, player_z, game_over

    if game_over:
        return  # Exit if the game is over

    # Remove road segments that are too far behind
    if segments[0]["z_position"] + road_segment_length < player_z - visible_range:
        segments.pop(0)

    # Add new road segments ahead
    if segments[-1]["z_position"] < player_z + visible_range:
        segments.append({
            "z_position": segments[-1]["z_position"] + road_segment_length,
            "active": True,
            "vehicle_present": False,
            "coin_present": False
        })

    # Spawn vehicles randomly based on score
    spawn_chance = min(0.02 + score * 0.0005, 0.1)
    if random.random() < spawn_chance:
        spawn_vehicle()

    # Update vehicle positions
    for vehicle in vehicles:
        if vehicle["direction"] == "left":
            vehicle["x_position"] -= vehicle["speed"]
        else:
            vehicle["x_position"] += vehicle["speed"]

    # Remove vehicles that are out of bounds
    vehicles = [v for v in vehicles if (-road_width / 2 - vehicle_size) <= v["x_position"] <= (road_width / 2 + vehicle_size)]

    # Check for collision with the player
    for vehicle in vehicles:
        if not teapot_invincibility and \
           abs(vehicle["x_position"] - player_x) < (vehicle_size / 2 + player_size / 2) and \
           abs(vehicle["z_position"] - player_z) < (vehicle_size / 2 + player_size / 2):
            print("Game Over! The player was hit by a car.")
            game_over = True  # Set game over state
            return  # Exit the function
        
def draw_starting():
    glPushMatrix()
    glColor3f(48 / 255, 93 / 255, 75 / 255)  # Set the color for the starting area
    glRotatef(-90, 1, 0, 0)  # Rotate the starting area to align with the road
    glTranslatef(-3, 0, 0)  # Translate the starting area to the correct position
    glBegin(GL_QUADS)  # Begin drawing a quadrilateral
    glVertex3f(0, 200, 0)  # Define the first vertex
    glVertex3f(0, 0, 0)  # Define the second vertex
    glVertex3f(800, 0, 0)  # Define the third vertex
    glVertex3f(200, 0, 0)  # Define the fourth vertex
    glEnd()  # End drawing the quadrilateral
    glPopMatrix()  # Restore the previous matrix state

def update_bullets():
    global active_bullets, vehicles

    # Move bullets forward
    for bullet in active_bullets:
        bullet["z_position"] += bullet_speed

    # Check for collisions with vehicles
    for bullet in active_bullets[:]:
        for vehicle in vehicles[:]:
            collision_range = 0.2  # Define the collision range for vehicles

            # Check if the bullet collides with a vehicle
            if abs(bullet["x_position"] - vehicle["x_position"]) < (vehicle_size / 2 + collision_range) and \
               abs(bullet["z_position"] - vehicle["z_position"]) < (vehicle_size / 2 + collision_range):
                vehicles.remove(vehicle)  # Remove the hit vehicle
                active_bullets.remove(bullet)  # Remove the bullet
                print("Shot a car!")
                break

    # Remove bullets that go out of bounds
    active_bullets = [b for b in active_bullets if b["z_position"] < player_z + visible_range]

def draw_road():
    draw_starting()  # Draw the starting area
    glPushMatrix()
    for segment in segments:
        is_road = int(segment["z_position"] / road_segment_length) % 2 == 0

        if is_road:
            glColor3f(36 / 255, 33 / 255, 42 / 255)  # Set the road color
        else:
            glColor3f(48 / 255, 93 / 255, 75 / 255)  # Set the grass color

        # Draw road or grass
        glBegin(GL_QUADS)
        glVertex3f(-road_width / 2, -0.05, segment["z_position"])
        glVertex3f(road_width / 2, -0.05, segment["z_position"])
        glVertex3f(road_width / 2, -0.05, segment["z_position"] + road_segment_length)
        glVertex3f(-road_width / 2, -0.05, segment["z_position"] + road_segment_length)
        glEnd()

        # Draw dashed white road markings
        if is_road:
            glColor3f(1.0, 1.0, 1.0)  # Set the color for road markings
            mark_width = 0.6  # Width of each marking
            mark_thickness = 0.1  # Thickness of each marking
            mark_gap = 0.7  # Gap between markings

            start_x = -road_width / 2 + mark_gap  # Start a bit inside
            end_x = road_width / 2 - mark_width - mark_gap  # End a bit inside

            x = start_x
            while x <= end_x:
                glBegin(GL_QUADS)
                glVertex3f(x, -0.04, segment["z_position"] + road_segment_length / 2 - mark_thickness / 2)
                glVertex3f(x + mark_width, -0.04, segment["z_position"] + road_segment_length / 2 - mark_thickness / 2)
                glVertex3f(x + mark_width, -0.04, segment["z_position"] + road_segment_length / 2 + mark_thickness / 2)
                glVertex3f(x, -0.04, segment["z_position"] + road_segment_length / 2 + mark_thickness / 2)
                glEnd()

                x += mark_width + mark_gap  # Move to the next marking
    glPopMatrix()

def draw_player():
    glPushMatrix()  # Save the current transformation matrix
    glTranslatef(player_x, 0.0, player_z)  # Move to the player's position
    glRotatef(-90, 1, 0, 0)  # Rotate the player to face forward
    glColor3f(1.0, 1.0, 1.0)  # Set the player's body color to white
    glutSolidCone(0.1, 0.4, 32, 32)  # Draw the player's body as a cone
    glPopMatrix()  # Restore the previous transformation matrix

    # Draw the player's head
    glPushMatrix()
    glTranslatef(player_x, 0.4, player_z)  # Position the head above the body
    glColor3f(1, 1, 1)  # Set the head color to white
    glutSolidSphere(0.080, 32, 32)  # Draw the head as a sphere
    glPopMatrix()

    # Draw the player's hat
    glPushMatrix()
    glTranslate(player_x, 0.40, player_z)  # Position the hat on top of the head
    glRotatef(-90, 1, 0, 0)  # Rotate the hat to align with the head
    glColor3f(200 / 255, 54 / 255, 67 / 255)  # Set the hat color to red
    glutSolidCone(0.08, 0.25, 32, 32)  # Draw the hat as a cone
    glPopMatrix()


def draw_circle(x, y, z, radius, slices=30):
    glBegin(GL_POLYGON)  # Begin drawing a filled circle
    for i in range(slices):  # Divide the circle into slices for smoothness
        angle = 2 * math.pi * i / slices  # Calculate the angle for each slice
        glVertex3f(x + radius * math.cos(angle), y, z + radius * math.sin(angle))  # Calculate the vertex position
    glEnd()  # End drawing the circle

def draw_wheel(x, y, z, radius, rotation_angle):
    glPushMatrix()  # Save the current transformation matrix
    glTranslatef(x, y, z)  # Move to the wheel's position
    glColor3f(36 / 255, 75 / 255, 117 / 255)  # Set the wheel color
    glRotatef(rotation_angle, 1, 0, 0)  # Rotate the wheel around the X-axis
    draw_circle(0, 0, 0, radius)  # Draw the wheel as a circle
    glPopMatrix()  # Restore the previous transformation matrix

def draw_vehicles():
    for vehicle in vehicles:  # Iterate through all vehicles
        sf = 0.09  # Scale factor for the vehicle

        # Draw the main body of the vehicle
        glPushMatrix()
        glTranslatef(vehicle["x_position"], 0.0, vehicle["z_position"])  # Move to the vehicle's position
        glColor3f(189 / 255, 67 / 255, 54 / 255)  # Set the vehicle's body color
        glScalef(2, 1.0, 0.79)  # Scale the vehicle's body
        glutSolidCube(0.4)  # Draw the body as a cube
        glPopMatrix()

        # Draw the upper part of the vehicle
        glPushMatrix()
        glTranslatef(vehicle["x_position"], 0.0, vehicle["z_position"])  # Move to the vehicle's position
        glColor3f(210 / 255, 209 / 255, 185 / 255)  # Set the upper part's color
        glTranslatef(0, 0.34, 0)  # Move the upper part above the body
        glScalef(1.5, 1.0, 0.79)  # Scale the upper part
        glutSolidCube(0.25)  # Draw the upper part as a cube
        glPopMatrix()

        # Draw the wheels of the vehicle
        wheel_radius = 0.1  # Radius of the wheels
        wheel_offset = 0.2  # Offset of the wheels from the center
        wheel_rotation = 90  # Rotation angle of the wheels

        # Front left wheel
        draw_wheel(vehicle["x_position"] - wheel_offset, 0.03, vehicle["z_position"] - 0.35, wheel_radius, wheel_rotation)

        # Rear right wheel
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
        glTranslatef(bullet["x_position"], 0.2, bullet["z_position"])  #Adjust height
        glutSolidSphere(bullet_size, 16, 16) 
        glPopMatrix()

def draw_debris():
    for d in debris:  # Iterate through all debris objects
        glPushMatrix()  # Save the current transformation matrix
        glTranslatef(d["x"], 0.0, d["z"])  # Move to the debris's position

        # Check the type of debris and draw accordingly
        if d["type"] == "rock":
            glColor3f(0.3, 0.3, 0.3)  # Set the color for rocks (gray)
            glutSolidSphere(d["size"], 8, 8)  # Draw the rock as a sphere
        elif d["type"] == "bone":
            glColor3f(102 / 255, 51 / 255, 0 / 255)  # Set the color for bones (brown)
            glScalef(0.1, 0.1, 0.5)  # Scale the bone to make it elongated
            glutSolidCube(d["size"] * 10)  # Draw the bone as a scaled cube

        glPopMatrix()  # Restore the previous transformation matrix

def update_debris():
    global debris

    # Find the farthest z-position among existing debris
    farthest_z = max([d["z"] for d in debris], default=player_z)

    # Generate new debris ahead of the player
    while farthest_z < player_z + debris_spawn_distance:
        farthest_z += debris_spacing  # Increment the z-position for the next debris

        # Randomly choose the side (left or right) for the debris
        side = random.choice([-1, 1])
        x_pos = side * random.uniform(3.0, 15.0)  # Random x-position within a range

        # Add a new debris object to the list
        debris.append({
            "x": x_pos,
            "z": farthest_z,
            "size": random.uniform(0.1, 0.9),  # Random size for the debris
            "type": random.choice(["rock", "bone"])  # Randomly choose the type
        })

    # Remove debris that are too far behind the player
    debris = [d for d in debris if d["z"] > player_z - 10.0]

def fire_bullet():
    global bullets, active_bullets, game_over

    # Add a new bullet at the player's position
    active_bullets.append({
        "x_position": player_x,  # Bullet starts at the player's x-position
        "z_position": player_z + 0.5,  # Bullet starts slightly ahead of the player
    })

    bullets -= 1  # Reduce the bullet count by 1
    print(f"Bullets left: {bullets}")  # Print the remaining bullet count

    # Check if bullets are finished
    if bullets == 0:
        print("No bullets left!")  # Notify the player that no bullets are left

def draw_distance():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, width, 0, height)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # # Display distance
    # glColor3f(1.0, 1.0, 1.0)
    # distance_text = f"Distance: {int(distanceCovered)}"
    # glRasterPos2f(10, height - 30)
    # for ch in distance_text:
    #     glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    # Display coins
    glColor3f(1.0, 1.0, 0.0)  # Yellow color for coins
    coins_text = f"Coins: {coinCount}"
    glRasterPos2f(10, height - 25)
    for ch in coins_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    # Display bullets
    glColor3f(0.0, 1.0, 0.0)  # Red color for bullets
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
    gluOrtho2D(0, width, 0, height)  # Set up orthographic projection

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Black background
    glDisable(GL_DEPTH_TEST)
    glColor3f(0.0, 0.0, 0.0)
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(width, 0)
    glVertex2f(width, height)
    glVertex2f(0, height)
    glEnd()

    # "YOU DIED" - Red text
    glColor3f(1.0, 0.0, 0.0)
    glRasterPos2f(width // 2 - 50, height // 2 + 10)
    for c in "YOU DIED":
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))

    # "PRESS R TO RESTART" - White text
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

    # Find eligible road segments for spawning coins
    eligible_segments = [
        s for s in segments
        if int(s["z_position"] / road_segment_length) % 2 == 0  # Only spawn on road segments
        and not s["coin_present"]  # Ensure no coins are already present
        and not s["vehicle_present"]  # Ensure no vehicles are present
        and s["z_position"] > player_z  # Ensure the segment is ahead of the player
    ]

    if not eligible_segments:
        return  # Exit if no eligible segments are found

    # Choose a random eligible segment
    segment = random.choice(eligible_segments)
    segment["coin_present"] = True  # Mark this segment as having coins

    # Determine the number of coins in the batch
    batch_size = random.randint(2, 5)  # Randomly choose between 2 and 5 coins
    gap = 0.5  # Gap between coins on the Z-axis
    x_pos = random.uniform(-road_width / 2 + 0.5, road_width / 2 - 0.5)  # Random X-position within road boundaries
    z_start = segment["z_position"] + road_segment_length / 2  # Start position for the coins

    # Add coins to the `coins` list
    for i in range(batch_size):
        z = z_start + i * gap  # Position each coin with a gap
        coins.append({
            "x": x_pos,  # X-position of the coin
            "z": z,  # Z-position of the coin
            "collected": False  # Mark the coin as not collected
        })

def draw_coins():
    for coin in coins:  # Iterate through all coins
        if not coin["collected"]:  # Only draw coins that have not been collected
            glPushMatrix()
            glTranslatef(coin["x"], 0.2, coin["z"])  # Position the coin slightly above the ground
            glColor3f(1.0, 0.84, 0.0)  # Set the coin color to gold
            glutSolidSphere(0.1, 16, 16)  # Draw the coin as a small sphere
            glPopMatrix()

def coin_collision():
    global coinCount
    for coin in coins:  # Iterate through all coins
        if not coin["collected"]:  # Only check for uncollected coins
            # Check if the player is close enough to collect the coin
            if abs(player_x - coin["x"]) < 0.25 and abs(player_z - coin["z"]) < 0.25:
                coin["collected"] = True  # Mark the coin as collected
                coinCount += 1  # Increment the coin count
                print(f"Coins collected: {coinCount}")  # Print the updated coin count

def spawn_teapot():
    global teapot, teapot_respawn_timer

    # Check if the respawn timer has elapsed
    if teapot is None and teapot_respawn_timer <= 0:
        # Spawn the teapot randomly after a certain distance
        if distanceCovered > 50 and random.random() < 0.1:
            teapot = {
                "x": random.uniform(-road_width / 2 + 0.5, road_width / 2 - 0.5),
                "z": player_z + visible_range - 10,  # Spawn ahead of the player
                "collected": False
            }
            print("Teapot spawned!")
    elif teapot is None:
        # Decrease the respawn timer
        teapot_respawn_timer -= 0.016  # Assuming ~60 FPS


def draw_teapot():
    global teapot, teapot_rotation

    if teapot and not teapot["collected"]:
        glPushMatrix()
        glTranslatef(teapot["x"], 0.5, teapot["z"])  # Position the teapot
        glRotatef(teapot_rotation, 0, 1, 0)  # Rotate around the Y-axis
        glColor3f(1.0, 0.5, 0.0)  # Orange color for the teapot
        glutSolidTeapot(0.3)  # Teapot size
        glPopMatrix()

        # Update rotation
        teapot_rotation += 2.0
        if teapot_rotation >= 360.0:
            teapot_rotation -= 360.0   

def teapot_collision():
    global teapot, teapot_invincibility, teapot_timer

    if teapot and not teapot["collected"]:
        # Check if the player is close enough to collect the teapot
        if abs(player_x - teapot["x"]) < 0.25 and abs(player_z - teapot["z"]) < 0.25:
            teapot["collected"] = True
            teapot_invincibility = True
            teapot_timer = 5.0  # 5 seconds of invincibility
            print("Teapot collected! Invincibility activated for 3 seconds.")   

def update_teapot():
    global teapot, teapot_invincibility, teapot_timer, teapot_respawn_timer

    # Reduce the invincibility timer if active
    if teapot_invincibility:
        teapot_timer -= 0.016  # Assuming ~60 FPS
        if teapot_timer <= 0:
            teapot_invincibility = False
            print("Invincibility expired.")
            teapot_timer = 0.0

    # Remove the teapot if it has been collected
    if teapot and teapot["collected"]:
        teapot = None
        teapot_respawn_timer = 5.0  # Set respawn timer to 5 seconds          
                
def draw_powerup_circle(x, y, radius, text, key):
    # Draw the circle border
    glColor3f(0.0, 0.0, 0.0)  # Black color for the border
    glBegin(GL_LINE_LOOP)
    for i in range(30):  # 30 slices for a smooth circle
        angle = 2 * math.pi * i / 30
        glVertex2f(x + radius * math.cos(angle), y + radius * math.sin(angle))
    glEnd()

    # Draw the text inside the circle
    glColor3f(1.0, 0.0, 0.0)  # Red color for the text
    lines = text.split()  # Split the text into lines if needed
    line_height = 12  # Adjust line spacing
    for i, line in enumerate(lines):
        text_width = len(line) * 7  # Approximate text width for smaller font
        glRasterPos2f(x - text_width / 2, y + (len(lines) - i - 1) * line_height - 5)  # Center each line
        for c in line:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(c))  # Use a smaller font for better fit

    # Draw the key label below the circle
    glColor3f(1.0, 0.0, 0.0)  # Black color for the key label
    glRasterPos2f(x - 5, y - radius - 15)  # Adjust key label position
    for c in key:  # Ensure the key is displayed in uppercase
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))


def draw_powerup_keys():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, width, 0, height)  # Set up orthographic projection

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Draw the power-up keys
    draw_powerup_circle(width - 300, 100, 30, "+1 Bullet", "j")  # Key J
    draw_powerup_circle(width - 200, 100, 30, "Halved Speed", "k")  # Key K
    draw_powerup_circle(width - 100, 100, 30, "Bomb", "l")  # Key L

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
    if game_over:
        # Display "Game Over" message
        glColor3f(1.0, 0.0, 0.0)  # Red color
        glRasterPos2f(-0.2, 0.0)  # Position the text
        for ch in "GAME OVER":
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        glutSwapBuffers()
        return  # Stop further rendering

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
    # draw_mouse_coords()
    draw_distance()
    draw_score()
    # Teapot logic
    spawn_teapot()
    update_teapot()
    teapot_collision()  # Check for teapot collision
    draw_teapot()
    # Draw power-up keys
    # draw_powerup_circle()
    draw_powerup_keys()
    glutSwapBuffers()

def keyboard(key, x, y):
    global player_x, player_z, bullets, game_over, vehicles, distanceCovered, initial_zpos, move_speed, movementSpeed, speed_increment, segments, coinCount, camera_mode, cheat_mode
    key = key.decode("utf-8").lower()  # Decode the key input and convert it to lowercase

    # Restart the game if 'r' is pressed and the game is over
    if game_over and key == 'r':
        player_x = 0.0  # Reset player position
        player_z = initial_zpos  # Reset player z-position
        bullets = 5  # Reset bullet count
        movementSpeed = 0.001  # Reset movement speed
        speed_increment = 0.0001  # Reset speed increment
        vehicles.clear()  # Clear all vehicles
        distanceCovered = 0.0  # Reset distance covered
        game_over = False  # Reset game over state
        cheat_mode = False  # Disable cheat mode
        coinCount = 0  # Reset coin count
        coins.clear()  # Clear all coins
        trees.clear()  # Clear all trees
        debris.clear()  # Clear all debris
        segments.clear()  # Clear all road segments

        # Reinitialize road segments
        for i in range(num_segments):
            segments.append({
                "z_position": i * road_segment_length,
                "active": True,
                "vehicle_present": False,
                "coin_present": False
            })

        return  # Exit the function

    # Handle key inputs if the game is not over
    if not game_over:
        if key == 'c':  # Toggle cheat mode
            cheat_mode = not cheat_mode
            print("CHEAT MODE:", cheat_mode)

        if key == 'w':  # Toggle camera mode
            camera_mode = "first" if camera_mode == "third" else "third"

        elif key == 'a':  # Move player left
            player_x += move_speed
            if player_x > road_width / 2 - player_size / 2:  # Clamp player within road boundaries
                player_x = road_width / 2 - player_size / 2

        elif key == 'd':  # Move player right
            player_x -= move_speed
            if player_x < -road_width / 2 + player_size / 2:  # Clamp player within road boundaries
                player_x = -road_width / 2 + player_size / 2

        elif key == ' ' and bullets > 0:  # Fire a bullet if spacebar is pressed and bullets are available
            fire_bullet()

        # Powerup 1: Increase bullet count by 1 (key: J)
        elif key == 'j':
            if cheat_mode == False:
                if coinCount >= 5 and bullets < 5:  # Check if enough coins are available and bullets are below max
                    bullets += 1
                    coinCount -= 5
                    print("Powerup Activated: +1 Bullet")
                elif bullets >= 5:
                    print("Max bullets reached!")
                else:
                    print("Not enough coins for Bullet Powerup!")
            else:  # Cheat mode allows unlimited coins
                if coinCount >= 0 and bullets < 5:
                    bullets += 1
                    print("Powerup Activated: +1 Bullet")
                elif bullets >= 5:
                    print("Max bullets reached!")
                else:
                    print("Not enough coins for Bullet Powerup!")

        # Powerup 2: Halve movement speed (key: K)
        elif key == 'k':
            if coinCount >= 10:  # Check if enough coins are available
                movementSpeed = max(movementSpeed / 2, 0.001)  # Halve the movement speed
                coinCount -= 10
                print("Powerup Activated: Halved Speed")
            else:
                print("Not enough coins for Slowdown Powerup!")

        # Powerup 3: Bomb - Destroy vehicles in range (key: L)
        elif key == 'l':
            if cheat_mode == False:
                if coinCount >= 20:  # Check if enough coins are available
                    bomb_radius = 15.0  # Define radius around the player
                    vehicles[:] = [v for v in vehicles if math.hypot(v["x_position"] - player_x, v["z_position"] - player_z) > bomb_radius]
                    coinCount -= 20
                    print("Powerup Activated: Bomb!")
                else:
                    print("Not enough coins for Bomb Powerup!")
            else:  # Cheat mode allows unlimited coins
                if coinCount >= 0:
                    bomb_radius = 15.0  # Define radius around the player
                    vehicles[:] = [v for v in vehicles if math.hypot(v["x_position"] - player_x, v["z_position"] - player_z) > bomb_radius]
                    coinCount -= 0
                    print("Powerup Activated: Bomb!")
                else:
                    print("Not enough coins for Bomb Powerup!")

    glutPostRedisplay()  # Request a redraw of the display


glutInit()
glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
glutInitWindowSize(width, height)
glutInitWindowPosition(100, 100)
glutCreateWindow(b"Run To Live 3D game")
init()
glutDisplayFunc(display)
glutKeyboardFunc(keyboard)
glutIdleFunc(display)
# glutPassiveMotionFunc(mouse_motion)
glutMainLoop()


