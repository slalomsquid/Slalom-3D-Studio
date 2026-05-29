import pygame, math, utils, constants, os, numpy as np, classes

# Force SDL to send raw touch events instead of converting to mouse events
os.environ["SDL_MOUSE_TOUCH_EVENTS"] = "1"

pygame.init()

SCREEN = pygame.display.set_mode((constants.WIDTH, constants.HEIGHT))
pygame.display.set_caption("Slalom 3D Studio")

def main():
    clock = pygame.time.Clock()
    history = classes.HistoryManager(max_undo=50)

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

        [0,5],
        [1,6],
        [2,7],
        [3,4],

        [0,2],
        [4,6]
    ]
    faces = [
        # [1,0,2],
        # [1,5,0],
        # [1,2,5],
        # [2,0,5],
        [5, 6, 4], 
        [6, 7, 4], 
        [4, 7, 3], 
        [2, 3, 7], 
        [6, 2, 7], 
        [6, 5, 1], 
        [1, 2, 6], 
        [5, 4, 0], 
        [0, 1, 5], 
        [4, 3, 0], 
        [2, 0, 3], 
        [0, 2, 1]
    ]
    colors = [
        [0,0,0],
        [255,0,0],
        [0,255,0],
        [0,0,255]
    ]

    offset : list[float] = [0.0,0.0,5.0] # Moves the object 5 away from the camera
    rotation : list[float]= [math.pi/8,0.0,0.0]

    active_touches = {}

    last_pos = False
    zoom_vel = 0.0
    pan_vel = [0.0,0.0]
    vel = [0.0,0.0]
    zooming = False
    moving = False
    scaling = False
    scale_centre = (0.0,0.0)
    initial_poses = []
    axis_lock = [False, False, False]
    show_grid = True
    show_axes = True
    cull_backfaces = False
    wireframe = False

    selection = 0
    """0: points, 1: lines, 2: faces just like blender :)"""
    selected = {0:[], 1:[], 2:[]}

    timer = 0.0
    running = True

    while running:
        delta_time = clock.tick(constants.FPS) / 1000.0

        timer += delta_time
        if timer >= 2:
            timer = 0.0
            print(clock.get_fps())

        transformed_points = utils.transform_points(points, rotation, offset)

        screen_points = utils.get_screen_points(transformed_points)

        keys = pygame.key.get_pressed()

        # Handle Pygame Events
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    running = False
                case pygame.MOUSEMOTION:
                    if moving:
                        for selected_idx in selected[0]:
                            if not axis_lock[1]:
                                points[selected_idx][0] += event.rel[0] * 0.01
                            if not axis_lock[0]:
                                points[selected_idx][1] -= event.rel[1] * 0.01
                    if scaling:
                        for selected_idx in selected[0]:  
                            points[selected_idx] = utils.scale_points_around_point(points[selected_idx], 1 + (event.rel[0] + event.rel[1]) * 0.01, scale_centre)
                            # if not z_lock:
                            #     points[selected_idx][2] += event.rel[1] * 0.01
                    # rotation[0] = event.pos[1]*0.01
                    # rotation[1] = event.pos[0]*0.01
                case pygame.FINGERDOWN:
                    # active_touches[event.finger_id] = (event.x, event.y)
                    is_ghost = False
                    for touch in active_touches.values():
                        dist = utils.length(np.array((event.x, event.y)) - np.array(touch))
                        if dist < constants.DIST_THRESHOLD:
                            is_ghost = True
                            break
                    if not is_ghost:
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
                        case pygame.K_1:
                            if moving:
                                axis_lock[0] = not axis_lock[0]
                                for point_index in selected[0]:
                                    # reset postition
                                    points[point_index] = initial_poses[selected[0].index(point_index)]
                            selection = 0
                            selected[0] += utils.line_idxs_to_points(selected[1], lines)
                            selected[0] += utils.face_idxs_to_point_idxs(selected[2], faces)
                            selected[1] = []
                            selected[2] = []
                        case pygame.K_2:
                            selection = 1
                            if moving:
                                axis_lock[1] = not axis_lock[1]
                                for point_index in selected[0]:
                                    points[point_index] = initial_poses[selected[0].index(point_index)]
                            selected[1] += utils.point_idxs_to_line_idxs(selected[0], selected[1], lines)
                            selected[1] += utils.point_idxs_to_line_idxs(utils.face_idxs_to_point_idxs(selected[2], faces), selected[1], lines)
                            selected[0] = []
                            selected[2] = []
                        case pygame.K_3:
                            if moving:
                                axis_lock[0] = not axis_lock[0]
                                for point_index in selected[0]:
                                    points[point_index] = initial_poses[selected[0].index(point_index)]
                            selection = 2
                            selected[2] += utils.point_idxs_to_face_idxs(selected[0], selected[2], faces)
                            selected[2] += utils.point_idxs_to_face_idxs(utils.line_idxs_to_points(selected[1], lines), selected[2], faces)
                            selected[0] = []
                            selected[1] = []
                        case pygame.K_4:
                            show_grid = not show_grid
                        case pygame.K_5:
                            show_axes = not show_axes
                        case pygame.K_6:
                            cull_backfaces = not cull_backfaces
                        case pygame.K_TAB:
                            wireframe = not wireframe
                        case pygame.K_z:
                            if (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL] or keys[pygame.K_LMETA] or keys[pygame.K_RMETA]):
                                prev_state = history.undo(points, lines, faces)
                                if prev_state:
                                    # Slice assignment [:] updates the lists in-place 
                                    # so other references don't break
                                    points[:], lines[:], faces[:] = prev_state
                                    selected = [[], [], []] # Clear selection on undo
                                    print("Undo performed")
                        case pygame.K_y:
                            if (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL] or keys[pygame.K_LMETA] or keys[pygame.K_RMETA]):
                                next_state = history.redo(points, lines, faces)
                                if next_state:
                                    points[:], lines[:], faces[:] = next_state
                                    selected = [[], [], []] # Clear selection on redo
                                    print("Redo performed")
                        case pygame.K_f:
                            pts = []
                            for idx in selected[0]:
                                if idx not in pts:
                                    pts.append(points[idx])
                            for idx in selected[1]:
                                if idx not in pts:
                                    pts.append(points[idx])
                            for idx in selected[2]:
                                if idx not in pts:
                                    pts.append(points[idx])
                            if len(pts) == 2:
                                new_line = [selected[0][0], selected[0][1]]
                                if new_line not in lines:
                                    lines.append(new_line)
                            if len(pts) == 3:
                                new_face = [selected[0][0], selected[0][1], selected[0][2]]
                                if new_face not in faces:
                                    faces.append(new_face)

                                    transformed_points = utils.transform_points(points, rotation, offset)
                                    screen_points = utils.get_screen_points(transformed_points)

                                    p0 = screen_points[new_face[0]]
                                    p1 = screen_points[new_face[1]]
                                    p2 = screen_points[new_face[2]]

                                    # check winding
                                    winding = (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p1[1] - p0[1]) * (p2[0] - p0[0])

                                    if winding < 0:
                                        faces[-1] = utils.flip_face(new_face)

                        case pygame.K_x:
                            if moving:
                                axis_lock[0] = not axis_lock[0]
                                for point_index in selected[0]:
                                    points[point_index] = [points[point_index][0], initial_poses[selected[0].index(point_index)][1], initial_poses[selected[0].index(point_index)][2]]
                            else:
                                history.save_state(points, lines, faces)
                                if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                                    # Convert the indices into sets
                                    points_to_remove = set(selected[0])
                                    lines_to_remove = set(selected[1])
                                    faces_to_remove = set(selected[2])

                                    # Delete attatched points
                                    for line_idx in lines_to_remove:
                                        if line_idx < len(lines):
                                            points_to_remove.update(lines[line_idx])
                                            
                                    for face_idx in faces_to_remove:
                                        if face_idx < len(faces):
                                            points_to_remove.update(faces[face_idx])

                                    # Identify attatched verts
                                    for idx, line in enumerate(lines):
                                        if any(pt in points_to_remove for pt in line):
                                            lines_to_remove.add(idx)

                                    for idx, face in enumerate(faces):
                                        if any(pt in points_to_remove for pt in face):
                                            faces_to_remove.add(idx)

                                    # Rebuild the lists by keeping only what isn't marked for deletion
                                    new_points = []
                                    point_index_map = {}
                                    for old_idx, pt in enumerate(points):
                                        if old_idx not in points_to_remove:
                                            point_index_map[old_idx] = len(new_points)
                                            new_points.append(pt)

                                    # Rebuild lines with updated point indices
                                    new_lines = [
                                        [point_index_map[pt] for pt in line]
                                        for idx, line in enumerate(lines)
                                        if idx not in lines_to_remove
                                    ]

                                    # Rebuild faces with updated point indices
                                    new_faces = [
                                        [point_index_map[pt] for pt in face]
                                        for idx, face in enumerate(faces)
                                        if idx not in faces_to_remove
                                    ]

                                    # Overwrite original lists with the cleaned data
                                    points[:] = new_points
                                    lines[:] = new_lines
                                    faces[:] = new_faces

                                    # Clear selection
                                    selected = [[], [], []]
                                else:
                                    # Convert selected indices to sets for fast lookup
                                    points_to_remove = set(selected[0])
                                    lines_to_remove = set(selected[1])
                                    faces_to_remove = set(selected[2])

                                    # Identify lines and faces to deleted due to attatched verts 
                                    for idx, line in enumerate(lines):
                                        if any(pt in points_to_remove for pt in line):
                                            lines_to_remove.add(idx)

                                    for idx, face in enumerate(faces):
                                        if any(pt in points_to_remove for pt in face):
                                            faces_to_remove.add(idx)

                                    # Rebuild lines and faces filtering out deleted
                                    filtered_lines = [line for idx, line in enumerate(lines) if idx not in lines_to_remove]
                                    filtered_faces = [face for idx, face in enumerate(faces) if idx not in faces_to_remove]

                                    # Rebuild the points list and update indices if vertices were deleted
                                    if points_to_remove:
                                        new_points = []
                                        point_index_map = {}
                                        
                                        for old_idx, pt in enumerate(points):
                                            if old_idx not in points_to_remove:
                                                point_index_map[old_idx] = len(new_points)
                                                new_points.append(pt)
                                        
                                        # Update original points list
                                        points[:] = new_points
                                        
                                        # Shift the vert indices inside the remaining lines and faces
                                        lines[:] = [[point_index_map[pt] for pt in line] for line in filtered_lines]
                                        faces[:] = [[point_index_map[pt] for pt in face] for face in filtered_faces]
                                    else:
                                        # If no verts were deleted then no shift
                                        lines[:] = filtered_lines
                                        faces[:] = filtered_faces

                                    # Clear selection
                                    selected = [[], [], []]
                        case pygame.K_e:
                            if selection == 0:
                                if not selected[0]:
                                    break # Stop if none selected
                                    
                                moving = True
                                start_idx = len(points)
                                
                                # dupe pts
                                for point_idx in selected[0]:
                                    points.append(points[point_idx][:])
                                    
                                new_idxs = list(range(start_idx, len(points)))
                                
                                # store initial pos of new pts 
                                for new_idx in new_idxs:
                                    initial_poses.append(points[new_idx][:])
                                
                                for point_idx in new_idxs:
                                    lines.append([point_idx, selected[0][new_idxs.index(point_idx)]]) # Connect the new point to the original with a line

                                # update active selection
                                selected[0] = new_idxs
                        case pygame.K_g:
                            history.save_state(points, lines, faces)
                            moving = True
                            for point_idx in selected[0]:
                                initial_poses.append(points[point_idx][:]) # Store initial pos
                        case pygame.K_ESCAPE:
                            if moving or scaling:
                                for pos_idx in selected[0]:
                                    points[pos_idx] = initial_poses[selected[0].index(pos_idx)] # Reset to initial position
                                moving = False
                                scaling = False
                                initial_poses = []
                        case pygame.K_s:
                            history.save_state(points, lines, faces)
                            if len(selected[0]) > 1:
                                scaling = True
                                for point_idx in selected[0]:
                                    initial_poses.append(points[point_idx][:]) # Store initial pos
                                scale_centre = utils.get_centre(initial_poses)
                        case pygame.K_p:
                            print(faces)
                        case pygame.K_n:
                            if selection == 2:
                                for face in selected[2]:
                                    # faces[face] = [faces[face][1], faces[face][0], faces[face][2]]
                                    faces[face] = utils.flip_face(faces[face])
                case pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if moving or scaling:
                            history.save_state(points, lines, faces)
                            moving = False
                            scaling = False
                            initial_poses = []
                        else:
                            match selection:
                                case 0:
                                    if not (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]):
                                        selected[0] = []
                                    for point in screen_points:
                                        if utils.length(np.array(point) - np.array(event.pos)) < constants.VERT_DIST:
                                            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                                                if screen_points.index(point) in selected[0]:
                                                    selected[0].remove(screen_points.index(point))
                                                else:
                                                    selected[0].append(screen_points.index(point))
                                            else:
                                                selected[0] = [screen_points.index(point)]
                                                axis_lock[0] = False
                                                axis_lock[1] = False
                                                axis_lock[2] = False
                                            break
                                case 1:
                                    for line in lines:
                                        p0 = screen_points[line[0]]
                                        p1 = screen_points[line[1]]
                                        line_vec = np.array(p1) - np.array(p0)
                                        point_vec = np.array(event.pos) - np.array(p0)
                                        line_len = utils.length(line_vec)
                                        if line_len == 0: continue
                                        line_unitvec = line_vec / line_len
                                        proj_length = np.dot(point_vec, line_unitvec)
                                        if 0 <= proj_length <= line_len:
                                            closest_point = np.array(p0) + line_unitvec * proj_length
                                            if utils.length(closest_point - np.array(event.pos)) < 5:
                                                if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                                                    if lines.index(line) in selected[1]:
                                                        selected[1].remove(lines.index(line))
                                                    else:
                                                        selected[1].append(lines.index(line))
                                                else:
                                                    selected[1] = [lines.index(line)]
                                                    axis_lock[0] = False
                                                    axis_lock[1] = False
                                                    axis_lock[2] = False
                                                break
                                case 2:

                                    transformed_points = utils.transform_points(points, rotation, offset)

                                    face_list = []

                                    for face in faces:
                                        avg_z = utils.get_avg_z_of_points((transformed_points[point] for point in face))
                                        face_list.append((avg_z, face))

                                    face_list.sort(key=lambda item: item[0])

                                    for avg_z, face in face_list:
                                        if utils.is_in_triangle((screen_points[face[0]], screen_points[face[1]], screen_points[face[2]]), event.pos):
                                            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                                                if faces.index(face) in selected[2]:
                                                    selected[2].remove(faces.index(face))
                                                else:
                                                    selected[2].append(faces.index(face))
                                            else:
                                                selected[2] = [faces.index(face)]
                                                axis_lock[0] = False
                                                axis_lock[1] = False
                                                axis_lock[2] = False
                                            break

        zooming = (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL] or keys[pygame.K_LMETA] or keys[pygame.K_RMETA])

        panning = (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])
        
        holding = (keys[pygame.K_LALT] or keys[pygame.K_RALT])

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

        if holding:
            pass
        elif zooming:
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

        draw(points, lines, faces, offset, rotation, selected, moving, axis_lock, selection, show_grid, show_axes, cull_backfaces, wireframe)

    pygame.quit()

# def draw(points, lines, faces, offset, rotation, selected, moving=False, x_lock=False, y_lock=False, z_lock=False, selection=0):
#     SCREEN.fill((0,0,0))

#     # Rotate and transform all points to 3D space with offsets applied
#     transformed_points = []
#     screen_points = []
    
#     # for point in points:
#     #     # use this order
#     #     new_point = utils.rotate_y(point, rotation[1])
#     #     new_point = utils.rotate_x(new_point, rotation[0])
#     #     new_point = utils.rotate_z(new_point, rotation[2])
        
#     #     world_x = new_point[0] + offset[0]
#     #     world_y = new_point[1] + offset[1]
#     #     world_z = new_point[2] + offset[2]
#     #     transformed_points.append((world_x, world_y, world_z))
        
#     #     # Project to 2D screen
#     #     screen_points.append(utils.plane_to_screen(utils.point_to_plane(new_point, offset)))

#     transformed_points = utils.transform_points(points, rotation, offset)

#     screen_points = utils.get_screen_points(transformed_points)

#     # (depth, type_string, data_tuple)
#     render_queue = []

#     # Calculate Vertex Depths
#     for i, point in enumerate(transformed_points):
#         if point[2] <= 0: continue # Skip if behind camera
#         depth = utils.length(point)
#         render_queue.append((depth, 'vertex', i))

#     # Calculate Line Depths (using midpoint of the two vertices)
#     for line in lines:
#         p0 = transformed_points[line[0]]
#         p1 = transformed_points[line[1]]
        
#         if p0[2] <= 0 or p1[2] <= 0: continue
        
#         avg_x = (p0[0] + p1[0]) / 2.0
#         avg_y = (p0[1] + p1[1]) / 2.0
#         avg_z = (p0[2] + p1[2]) / 2.0
        
#         depth = utils.length((avg_x, avg_y, avg_z))
#         render_queue.append((depth, 'line', line))

#     # Calculate dace depth using center point
#     for face in faces:
#         p0 = transformed_points[face[0]]
#         p1 = transformed_points[face[1]]
#         p2 = transformed_points[face[2]]
        
#         if p0[2] <= 0 or p1[2] <= 0 or p2[2] <= 0: continue
        
#         avg_x = (p0[0] + p1[0] + p2[0]) / 3.0
#         avg_y = (p0[1] + p1[1] + p2[1]) / 3.0
#         avg_z = (p0[2] + p1[2] + p2[2]) / 3.0
        
#         depth = utils.length((avg_x, avg_y, avg_z))
#         render_queue.append((depth, 'face', face))

#     # Sort
#     render_queue.sort(key=lambda item: item[0], reverse=True)

#     # Draw
#     for depth, item_type, data in render_queue:
        
#         if item_type == 'vertex':
#             p_screen = screen_points[data]
#             pygame.draw.circle(SCREEN, (200, 200, 200), p_screen, 3)
            
#         elif item_type == 'line':
#             pygame.draw.line(SCREEN, (255, 255, 255), screen_points[data[0]], screen_points[data[1]], 1)
            
#         elif item_type == 'face':
#             p0 = screen_points[data[0]]
#             p1 = screen_points[data[1]]
#             p2 = screen_points[data[2]]
            
#             # Winding orientation color check
#             winding = (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p1[1] - p0[1]) * (p2[0] - p0[0])
#             if winding > 0:
#                 color = (50, 120, 255)  # Blue = Front
#             else:
#                 color = (255, 70, 70)   # Red = Back

#             pygame.draw.polygon(SCREEN, color, (p0, p1, p2))
#             # Outline of face
#             pygame.draw.polygon(SCREEN, (100, 100, 100), (p0, p1, p2), 1)

#     d = utils.length(offset) / 2 # Half the dist from camera to prevent clipping issues

#     axis_lines = [
#         (( -d,  0,  0), ( d,  0,  0)), # X Axis
#         ((  0, -d,  0), ( 0,  d,  0)), # Y Axis
#         ((  0,  0, -d), ( 0,  0,  d))  # Z Axis
#     ]

#     axis_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]

#     dmod = 2

#     for num in range(-int(d)-dmod,int(d)+dmod+1):
#         axis_lines.append(((num, 0, -d-dmod), (num, 0, d+dmod)))
#         axis_lines.append(((-d-dmod, 0, num), (d+dmod, 0, num)))
#         axis_colors += list(constants.LIGHT_GREY) + list(constants.LIGHT_GREY) + list(constants.LIGHT_GREY)

#     if moving:
#         for point_index in selected[0]:
#             point_pos = transformed_points[point_index]
#             axis_lines = []
#             if x_lock:
#                 axis_lines.append(((point_pos[0]-d,point_pos[1],point_pos[2]), (point_pos[0]+d,point_pos[1], point_pos[2])))
#                 axis_colors += list(constants.RED)
#             if y_lock:
#                 axis_lines.append(((point_pos[0], point_pos[1]-d, point_pos[2]), (point_pos[0], point_pos[1]+d, point_pos[2])))
#                 axis_colors += list(constants.GREEN)
#             if z_lock:
#                 axis_lines.append(((point_pos[0], point_pos[1], point_pos[2]-d), (point_pos[0], point_pos[1], point_pos[2]+d)))
#                 axis_colors += list(constants.BLUE)

#     for i, line in enumerate(axis_lines):
#         rotated_line = []
#         behind_camera = False
        
#         for point in line:
#             # Rotate around object center
#             new_point = utils.rotate_y(point, rotation[1])
#             new_point = utils.rotate_x(new_point, rotation[0])
#             new_point = utils.rotate_z(new_point, rotation[2])
            
#             # Check if point is behind the camera after offset
#             if new_point[2] + offset[2] <= 0:
#                 behind_camera = True
#                 break
                
#             rotated_line.append(new_point)

#         if not behind_camera:
#             p0_screen = utils.plane_to_screen(utils.point_to_plane(rotated_line[0], offset))
#             p1_screen = utils.plane_to_screen(utils.point_to_plane(rotated_line[1], offset))
            
#             pygame.draw.line(SCREEN, axis_colors[i], p0_screen, p1_screen, 2)


#     # Highlight selected
#     for point_index in selected[0]:
#         if point_index < len(screen_points):
#             pygame.draw.circle(SCREEN, (255, 255, 0), screen_points[point_index], 6, 2)
#     for line_index in selected[1]:
#         if line_index < len(lines):
#             line = lines[line_index]
#             pygame.draw.line(SCREEN, (255, 255, 0), screen_points[line[0]], screen_points[line[1]], 3)
#     for face_index in selected[2]:
#         if face_index < len(faces):
#             face = faces[face_index]
#             p0 = screen_points[face[0]]
#             p1 = screen_points[face[1]]
#             p2 = screen_points[face[2]]
#             pygame.draw.polygon(SCREEN, (255, 255, 0), (p0, p1, p2), 3)

#     ### HUD ###
#     pygame.draw.rect(SCREEN, constants.WHITE, (10, 10, 20, 20))
#     pygame.draw.circle(SCREEN, constants.BLACK, (20, 20), 4)
#     pygame.draw.rect(SCREEN, constants.WHITE, (40, 10, 20, 20))
#     pygame.draw.line(SCREEN, constants.BLACK, (50, 12), (50, 28), 4)
#     pygame.draw.rect(SCREEN, constants.WHITE, (70, 10, 20, 20))
#     pygame.draw.rect(SCREEN, constants.BLACK, (72, 12, 16, 16))

#     pygame.draw.rect(SCREEN, constants.SKY_BLUE, (30*(selection+1)-27, 3, 34, 34), 4)

#     pygame.display.update()

def draw(points, lines, faces, offset, rotation, selected, moving=False, axis_lock = [False, False, False], selection=0, show_grid = True, show_axes = True, cull_backfaces = False, wireframe = False):
    SCREEN.fill((0, 0, 0))

    # Transform points to 3D camera space
    transformed_points = utils.transform_points(points, rotation, offset)
    screen_points = utils.get_screen_points(transformed_points)

    render_queue = []
    """Depth, type, point"""

    # Calculate vert z height
    for i, point in enumerate(transformed_points):
        if point[2] <= 0: continue # Skip if behind camera
        render_queue.append((point[2], 'vertex', i))

    # Calculate line z height
    for line in lines:
        p0 = transformed_points[line[0]]
        p1 = transformed_points[line[1]]
        
        if p0[2] <= 0 or p1[2] <= 0: continue
        
        avg_z = (p0[2] + p1[2]) / 2.0
        render_queue.append((avg_z, 'line', line))

    # Calculate face z height
    for face in faces:
        # p0 = transformed_points[face[0]]
        # p1 = transformed_points[face[1]]
        # p2 = transformed_points[face[2]]
        
        # if p0[2] <= 0 or p1[2] <= 0 or p2[2] <= 0: continue
        
        # avg_z = (p0[2] + p1[2] + p2[2]) / 3.0
        # render_queue.append((avg_z, 'face', face))

        avg_z = utils.get_avg_z_of_points((transformed_points[point] for point in face))
        render_queue.append((avg_z, 'face', face))

    # sort z height
    render_queue.sort(key=lambda item: item[0], reverse=True)

    # draw mesh
    for depth, item_type, data in render_queue:
        if item_type == 'vertex' and wireframe:
            pygame.draw.circle(SCREEN, (200, 200, 200), screen_points[data], 3)

        elif item_type == 'line' and wireframe:
            pygame.draw.line(SCREEN, (255, 255, 255), screen_points[data[0]], screen_points[data[1]], 2)
            
        elif item_type == 'face':
            p0 = screen_points[data[0]]
            p1 = screen_points[data[1]]
            p2 = screen_points[data[2]]
            
            # Winding orientation color check
            winding = (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p1[1] - p0[1]) * (p2[0] - p0[0])
            color = (50, 120, 255) if winding > 0 else (255, 70, 70)

            # Hide backfaces
            if cull_backfaces or not wireframe:
                if winding <= 0:
                  continue 

            # color = (50, 120, 255) # Blue = Front

            pygame.draw.polygon(SCREEN, color, (p0, p1, p2))
            pygame.draw.polygon(SCREEN, constants.DARK_GREY, (p0, p1, p2), 2)

    # guidelines
    d = utils.length(offset) / 2 
    guide_lines = []
    
    if show_grid:
        guide_lines.extend(utils.get_grid_lines(d, dmod=2, color=constants.DARK_GREY, thickness=1))
    if show_axes:
        guide_lines.extend(utils.get_axis_lines(d, thickness=4))
    
    if moving:
        guide_lines.extend(utils.get_lock_lines(points, selected, axis_lock, d, thickness=4))

    for p0_local, p1_local, color, thickness in guide_lines:
        rotated_line = []
        behind_camera = False
        
        for pt in (p0_local, p1_local):
            # Rotate around object center
            new_pt = utils.rotate_y(pt, rotation[1])
            new_pt = utils.rotate_x(new_pt, rotation[0])
            new_pt = utils.rotate_z(new_pt, rotation[2])
            
            # Check if point is behind the camera
            if new_pt[2] + offset[2] <= 0:
                behind_camera = True
                break
                
            rotated_line.append(new_pt)

        if not behind_camera:
            p0_screen = utils.plane_to_screen(utils.point_to_plane(rotated_line[0], offset))
            p1_screen = utils.plane_to_screen(utils.point_to_plane(rotated_line[1], offset))
            pygame.draw.line(SCREEN, color, p0_screen, p1_screen, thickness)

    ### hilight selections ###
    for point_index in selected[0]:
        if point_index < len(screen_points):
            pygame.draw.circle(SCREEN, (255, 255, 0), screen_points[point_index], 6, 2)
            
    for line_index in selected[1]:
        if line_index < len(lines):
            line_pts = lines[line_index]
            pygame.draw.line(SCREEN, (255, 255, 0), screen_points[line_pts[0]], screen_points[line_pts[1]], 4)
            
    for face_index in selected[2]:
        if face_index < len(faces):
            face_pts = faces[face_index]
            p0, p1, p2 = screen_points[face_pts[0]], screen_points[face_pts[1]], screen_points[face_pts[2]]
            tmp_surf = pygame.Surface((constants.WIDTH, constants.HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(tmp_surf, (255, 255, 0, 100), (p0, p1, p2))
            SCREEN.blit(tmp_surf, (0,0))

    ### HUD ###
    inc_size = 20
    pygame.draw.rect(SCREEN, constants.WHITE, (10, 10, inc_size, inc_size))
    pygame.draw.circle(SCREEN, constants.BLACK, (inc_size, inc_size), 4)
    pygame.draw.rect(SCREEN, constants.WHITE, (40, 10, inc_size, inc_size))
    pygame.draw.line(SCREEN, constants.BLACK, (50, 12), (50, 28), 4)
    pygame.draw.rect(SCREEN, constants.WHITE, (70, 10, inc_size, inc_size))
    pygame.draw.rect(SCREEN, constants.BLACK, (72, 12, 16, 16))
    pygame.draw.rect(SCREEN, constants.SKY_BLUE, (30*(selection+1)-27, 3, 34, 34), 4)
    # show grid
    icn_start = (130, 10)
    pygame.draw.rect(SCREEN, constants.WHITE, (icn_start[0], icn_start[1], inc_size, inc_size))
    # vert lines
    pygame.draw.line(SCREEN, constants.BLACK, (icn_start[0]+6, icn_start[1]+2), (icn_start[0]+6, icn_start[1]+inc_size-2), 2)
    pygame.draw.line(SCREEN, constants.BLACK, (icn_start[0]+inc_size-6, icn_start[1]+2), (icn_start[0]+inc_size-6, icn_start[1]+inc_size-2), 2)
    # horiz lines
    pygame.draw.line(SCREEN, constants.BLACK, (icn_start[0]+2, icn_start[1]+6), (icn_start[0]+inc_size-2, icn_start[1]+6), 2)
    pygame.draw.line(SCREEN, constants.BLACK, (icn_start[0]+2, icn_start[1]+inc_size-6), (icn_start[0]+inc_size-2, icn_start[1]+inc_size-6), 2)
    if show_grid:
        pygame.draw.rect(SCREEN, constants.SKY_BLUE, (icn_start[0]-7, 3, 34, 34), 4)

    # show axes
    icn_start = (160, 10)
    pygame.draw.rect(SCREEN, constants.WHITE, (icn_start[0], icn_start[1], inc_size, inc_size))
    pygame.draw.line(SCREEN, constants.BLACK, (icn_start[0]+inc_size//2, icn_start[1]+2), (icn_start[0]+inc_size//2, icn_start[1]+inc_size-2), 2)
    pygame.draw.line(SCREEN, constants.BLACK, (icn_start[0]+2, icn_start[1]+inc_size//2), (icn_start[0]+inc_size-2, icn_start[1]+inc_size//2), 2)
    if show_axes:
        pygame.draw.rect(SCREEN, constants.SKY_BLUE, (icn_start[0]-7, 3, 34, 34), 4)

    # cull backfaces
    icn_start = (190, 10)
    pygame.draw.rect(SCREEN, constants.WHITE, (icn_start[0], icn_start[1], inc_size, inc_size))
    pygame.draw.rect(SCREEN, constants.BLACK, (icn_start[0]+2, icn_start[1]+2, inc_size-8, inc_size-8))
    pygame.draw.rect(SCREEN, constants.GREY, (icn_start[0]+6, icn_start[1]+6, inc_size-8, inc_size-8))
    if cull_backfaces:
        pygame.draw.rect(SCREEN, constants.SKY_BLUE, (icn_start[0]-7, 3, 34, 34), 4)

    icn_start = (250, 10)
    pygame.draw.rect(SCREEN, constants.WHITE, (icn_start[0], icn_start[1], inc_size, inc_size))
    pygame.draw.rect(SCREEN, constants.BLACK, (icn_start[0]+2, icn_start[1]+2, inc_size-4, inc_size-4), width=2)
    if not wireframe:
        pygame.draw.rect(SCREEN, constants.SKY_BLUE, (icn_start[0]-7, 3, 34, 34), 4)

    icn_start = (280, 10)
    pygame.draw.rect(SCREEN, constants.WHITE, (icn_start[0], icn_start[1], inc_size, inc_size))
    pygame.draw.rect(SCREEN, constants.BLACK, (icn_start[0]+2, icn_start[1]+2, inc_size-4, inc_size-4))
    if wireframe:
        pygame.draw.rect(SCREEN, constants.SKY_BLUE, (icn_start[0]-7, 3, 34, 34), 4)

    pygame.display.update()

if __name__ == "__main__":
    main()