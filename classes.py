import copy
from collections import deque

class HistoryManager:
    def __init__(self, max_undo=50):
        # We store tuples of (points, lines, faces)
        self.undo_stack = deque(maxlen=max_undo)
        self.redo_stack = deque(maxlen=max_undo)

    def save_state(self, points, lines, faces):
        """Call this BEFORE making any modification (deletion, move, addition)."""
        state = copy.deepcopy((points, lines, faces))
        self.undo_stack.append(state)
        self.redo_stack.clear() # New actions remove out the redo history

    def undo(self, current_points, current_lines, current_faces):
        if not self.undo_stack:
            return None  # Nothing to undo
        
        # Save current state to redo stack before stepping back
        current_state = copy.deepcopy((current_points, current_lines, current_faces))
        self.redo_stack.append(current_state)
        
        # Pop the previous state
        return self.undo_stack.pop()

    def redo(self, current_points, current_lines, current_faces):
        if not self.redo_stack:
            return None  # Nothing to redo
        
        # Save current state to undo stack before moving forward
        current_state = copy.deepcopy((current_points, current_lines, current_faces))
        self.undo_stack.append(current_state)
        
        # Pop the next state
        return self.redo_stack.pop()