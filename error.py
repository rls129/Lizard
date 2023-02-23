from typing import List

class Error:
    def __init__(self, line, col, msg):
        self.line = line
        self.col = col
        self.msg = msg

errno: List[Error] = []

def push_error(line: int, col: int, message: str):
    errno.append(Error(line, col, message))