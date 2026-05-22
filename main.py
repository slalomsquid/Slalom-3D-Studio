import pygame, math, utils, constants, os, numpy as np

# Force SDL to send raw touch events instead of converting them to mouse events
os.environ["SDL_MOUSE_TOUCH_EVENTS"] = "1"

pygame.init()

SCREEN = pygame.display.set_mode((constants.WIDTH, constants.HEIGHT))
pygame.display.set_caption("Slalom 3D Studio")

def main():
    clock = pygame.time.Clock()

    points = [
        [-1,-1,1],
        [1,-1,1],
        [1,-1,-1],
        [-1,-1,-1],
        [-1,1,1],
        [1,1,1],
        [1,1,-1],
        [-1,1,-1],
    ]
    lines = [
        [0,1],
        [1,2],
        [2,3],
        [3,0],

        [4,5],
        [5,6],
        [6,7],
        [7,4],

        [0,4],
        [1,5],
        [2,6],
        [3,7],
    ]
    faces = [
        [1,0,2],
        [1,5,0],
        [1,2,5],
        [2,0,5]
    ]
    offset : list[float] = [0.0,0.0,5.0] # Postitions the object 5 away from the camera
    rotation : list[float]= [math.pi/8,0.0,0.0]

    active_touches = {}

    last_pos = False
    zoom_vel = 0.0
    pan_vel = [0.0,0.0]
    vel = [0.0,0.0]
    zooming = False

    running = True

    while running:
        delta_time = clock.tick(constants.FPS) / 1000.0

        # Handle Pygame Events
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    running = False
                # case pygame.MOUSEMOTION:
                #     rotation[0] = event.pos[1]*0.01
                #     rotation[1] = event.pos[0]*0.01
                case pygame.FINGERDOWN:
                    active_touches[event.finger_id] = (event.x, event.y)
                case pygame.FINGERUP:
                    if event.finger_id in active_touches:
                        del active_touches[event.finger_id]
                        last_pos = False
                case pygame.FINGERMOTION:
                    if event.finger_id in active_touches:
                        # Update the current position of the moving finger
                        active_touches[event.finger_id] = (event.x, event.y)
                case pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_0:
                            offset : list[float] = [0.0,0.0,5.0]
                            # rotation : list[float]= [math.pi/8,0.0,0.0]

        keys = pygame.key.get_pressed()

        zooming = (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL] or keys[pygame.K_LMETA] or keys[pygame.K_RMETA])

        panning = (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])
        

        if len(active_touches) == 2:
            finger_ids = list(active_touches.keys())
            pos1 = active_touches[finger_ids[0]]

            if last_pos:
                delta_vel = np.array(pos1) - np.array(last_pos)
                zoom_vel = 0.0
                pan_vel = [0.0,0.0]
                vel = [0.0,0.0]
                if zooming:
                    zoom_vel = delta_vel[1]
                elif panning:
                    pan_vel = [-delta_vel[0], delta_vel[1]]
                else:
                    vel = [delta_vel[0], delta_vel[1]]

            last_pos = pos1

        if zooming:
            offset[2] -= zoom_vel * 4
        elif panning:
            # up untill 2
            offset[:2] -= np.array(pan_vel) * 2
        else:
            rotation[1] -= vel[0] * 2.0
            rotation[0] += vel[1] * 2.0
            # clamp tilt
            rotation[0] = max(-math.pi/2 + 0.1, min(math.pi/2 - 0.1, rotation[0]))

        # Slow velocity each frame
        zoom_vel = utils.lerp(zoom_vel, 0.0, 2.0 * delta_time)
        pan_vel[0] = utils.lerp(pan_vel[0], 0.0, 2.0 * delta_time)
        pan_vel[1] = utils.lerp(pan_vel[1], 0.0, 2.0 * delta_time)
        vel[0] = utils.lerp(vel[0], 0.0, 2.0 * delta_time)
        vel[1] = utils.lerp(vel[1], 0.0, 2.0 * delta_time)

        draw(points, lines, faces, offset, rotation)

    pygame.quit()

def draw(points, lines, faces, offset, rotation):
    SCREEN.fill((0,0,0))

    # Rotate and transform all points to 3D space with offsets applied
    transformed_points = []
    screen_points = []
    
    # for point in points:
    #         # use this order
    #         new_point = utils.rotate_y(point, rotation[1])
    #         new_point = utils.rotate_x(new_point, rotation[0])
    #         new_point = utils.rotate_z(new_point, rotation[2])
            
    #         world_x = new_point[0] + offset[0]
    #         world_y = new_point[1] + offset[1]
    #         world_z = new_point[2] + offset[2]
    #         transformed_points.append((world_x, world_y, world_z))
            
    #         # Project to 2D screen
    #         screen_points.append(utils.plane_to_screen(utils.point_to_plane(new_point, [offset])))

    transformed_points = utils.transform_points(points, rotation, offset)

    screen_points = utils.get_screen_points(transformed_points)

    # (depth, type_string, data_tuple)
    render_queue = []

    # Calculate Vertex Depths
    for i, point in enumerate(transformed_points):
        if point[2] <= 0: continue # Skip if behind camera
        depth = utils.length(point)
        render_queue.append((depth, 'vertex', i))

    # Calculate Line Depths (using midpoint of the two vertices)
    for line in lines:
        p0 = transformed_points[line[0]]
        p1 = transformed_points[line[1]]
        
        if p0[2] <= 0 or p1[2] <= 0: continue
        
        avg_x = (p0[0] + p1[0]) / 2.0
        avg_y = (p0[1] + p1[1]) / 2.0
        avg_z = (p0[2] + p1[2]) / 2.0
        
        depth = utils.length((avg_x, avg_y, avg_z))
        render_queue.append((depth, 'line', line))

    # Calculate dace depth using center point
    for face in faces:
        p0 = transformed_points[face[0]]
        p1 = transformed_points[face[1]]
        p2 = transformed_points[face[2]]
        
        if p0[2] <= 0 or p1[2] <= 0 or p2[2] <= 0: continue
        
        avg_x = (p0[0] + p1[0] + p2[0]) / 3.0
        avg_y = (p0[1] + p1[1] + p2[1]) / 3.0
        avg_z = (p0[2] + p1[2] + p2[2]) / 3.0
        
        depth = utils.length((avg_x, avg_y, avg_z))
        render_queue.append((depth, 'face', face))

    # Sort
    render_queue.sort(key=lambda item: item[0], reverse=True)

    # Draw
    for depth, item_type, data in render_queue:
        
        if item_type == 'vertex':
            p_screen = screen_points[data]
            pygame.draw.circle(SCREEN, (200, 200, 200), p_screen, 3)
            
        elif item_type == 'line':
            pygame.draw.line(SCREEN, (255, 255, 255), screen_points[data[0]], screen_points[data[1]], 1)
            
        elif item_type == 'face':
            p0 = screen_points[data[0]]
            p1 = screen_points[data[1]]
            p2 = screen_points[data[2]]
            
            # Winding orientation color check
            winding = (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p1[1] - p0[1]) * (p2[0] - p0[0])
            if winding > 0:
                color = (50, 120, 255)  # Blue = Front
            else:
                color = (255, 70, 70)   # Red = Back

            pygame.draw.polygon(SCREEN, color, (p0, p1, p2))
            # Outlone of face
            # pygame.draw.polygon(SCREEN, (255, 255, 255), (p0, p1, p2), 1)

    d = utils.length(offset) / 2 # Half the dist from camera to prevent clipping issues

    axis_lines = [
        (( -d,  0,  0), ( d,  0,  0)), # X Axis
        ((  0, -d,  0), ( 0,  d,  0)), # Y Axis
        ((  0,  0, -d), ( 0,  0,  d))  # Z Axis
    ]

    axis_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]

    for i, line in enumerate(axis_lines):
        rotated_line = []
        behind_camera = False
        
        for point in line:
            # Rotate around object center
            new_point = utils.rotate_y(point, rotation[1])
            new_point = utils.rotate_x(new_point, rotation[0])
            new_point = utils.rotate_z(new_point, rotation[2])
            
            # Check if point is behind the camera after offset
            if new_point[2] + offset[2] <= 0:
                behind_camera = True
                break
                
            rotated_line.append(new_point)

        if not behind_camera:
            p0_screen = utils.plane_to_screen(utils.point_to_plane(rotated_line[0], offset))
            p1_screen = utils.plane_to_screen(utils.point_to_plane(rotated_line[1], offset))
            
            pygame.draw.line(SCREEN, axis_colors[i], p0_screen, p1_screen, 2)

    pygame.display.update()

if __name__ == "__main__":
    main()