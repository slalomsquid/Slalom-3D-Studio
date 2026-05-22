import math, constants, numpy as np

"""Utility functions to keep main somewhat readable"""

def point_to_plane(point, offset):
    """tysm Tsoding, not i see why y is up in godot..., i guess it cood be flipped easily"""
    x = point[0]+offset[0]
    y = point[1]+offset[1]
    z = point[2]+offset[2]

    # prevent divide by 0
    if z == 0:
        z += 0.001

    return (x / z, y / z)

def plane_to_screen(point):
    """Projects a plane coord (-1...1, -1...1) to a screen coordinate"""
    return ((point[0] + 1)/2*constants.WIDTH,(1-(point[1] + 1)/2)*constants.HEIGHT)

def rotate_x(point, angle_rad):
    """
    Rotates a 3D point counterclockwise around the Y-axis by a given angle in radians.
    """
    x, y, z = point
    
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    
    # Calculate the new Y and Z coordinates
    new_y = y * cos_a + z * sin_a
    new_z = -y * sin_a + z * cos_a
    
    # X remains unchanged during a X-axis rotation
    return (x, new_y, new_z)

def rotate_y(point, angle_rad):
    """
    Rotates a 3D point counterclockwise around the Y-axis by a given angle in radians.
    """
    x, y, z = point
    
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    
    # Calculate the new X and Z coordinates
    new_x = x * cos_a + z * sin_a
    new_z = -x * sin_a + z * cos_a
    
    # Y remains unchanged during a Y-axis rotation
    return (new_x, y, new_z)

def rotate_z(point, angle_rad):
    """
    Rotates a 3D point counterclockwise around the Z-axis by a given angle in radians.
    """
    x, y, z = point
    
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    
    # Calculate the new X and Y coordinates
    new_x = x * cos_a - y * sin_a
    new_y = x * sin_a + y * cos_a
    
    # Z remains unchanged during a Z-axis rotation
    return (new_x, new_y, z)

def length(vect):
    return math.sqrt(vect[0]**2 + vect[1]**2 + vect[2]**2)

def set_angle(angle: float) -> float:
    return angle % (2 * math.pi)

def move_towards(current, target, max_distance_delta):
    """Moves towards a vector/value with a max step"""
    to_vector = target - current
    dist = np.linalg.norm(to_vector)
    if dist <= max_distance_delta or dist == 0:
        return target
    return current + to_vector / dist * max_distance_delta

def lerp(start, end, t):
    """Linear interpolation between 2 points with t being the proportion between them"""
    return start + t * (end - start)
