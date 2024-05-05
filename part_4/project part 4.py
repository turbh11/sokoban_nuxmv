import subprocess
import os
import threading
from datetime import timedelta
import re
import time
import shutil
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle
import concurrent.futures

base_folder = r'C:\Users\user\OneDrive - Bar-Ilan University - Students\תואר שני\סמסטר א\אימות פורמלי וסינטזה\תרגילים\תרגילים של השנה\project\part_4'
nuxmv_dir = r"C:\Users\user\OneDrive - Bar-Ilan University - Students\Desktop\nuXmv-2.0.0-win64\nuXmv-2.0.0-win64\bin"

class Sokoban:
    '''
    Name: Sokoban
    Input: xsb_file (str): Path to the xsb file
    Output: None
    Operation: Initializes the Sokoban class with the given xsb file
    '''
    def __init__(self, xsb_file):
        # Read the xsb file and store the board
        
        self.board = self.read_xsb(xsb_file)
        self.length = self.board.__len__()
        self.width = self.board[0].__len__()
        self.processed_board = []
        self.goal_location = []
        self.num_of_boxes = 0
        self.iteration_counts = []
        self.iteration_steps = 0
        self.iteration_results = []
        self.box_priority = self.calculate_target_counts()
        self.max_priority_box =sum(sum(row) for row in self.box_priority)
        

    def validate_board(self):
        # Check if all rows have the same length
        if not all(len(row) == self.width for row in self.board):
            return False

        # Check if the first and last row are all '#'
        if not all(cell == '#' for cell in self.board[0]) or not all(cell == '#' for cell in self.board[-1]):
            return False

        # Check if the first and last cell in each row are '#'
        if not all(row[0] == '#' and row[-1] == '#' for row in self.board):
            return False

        return True
    
    
    def calculate_target_counts(self):
        counts_tb = [[0]*self.width for _ in range(self.length)]
        counts_bt = [[0]*self.width for _ in range(self.length)]
        counts_lr = [[0]*self.width for _ in range(self.length)]
        counts_rl = [[0]*self.width for _ in range(self.length)]
        # top to bottom
        for i in range(self.length):
            for j in range(self.width):
                if self.board[i][j] == '#':
                    
                    k = i + 1
                    while k < self.length and self.board[k][j] in ['.', '+', '*']:

                        for r2 in range(k, self.length):
                            if self.board[r2][j] in ['.', '+', '*']:
                                counts_tb[k][j] += 1
                            else:
                                break
                        k += 1
                    #while k < self.length and self.board[k][j] in ['.','+','*']:
                    #    counts_tb[m][j] += counts_tb[k-1][j] + 1 if k > 0 else 1
                    #    k += 1

        for i in range(self.length-1, -1, -1):
            for j in range(self.width):
                if self.board[i][j] == '#':
                    k = i - 1
                    while k >= 0 and self.board[k][j] in ['.', '+', '*']:
                        for r2 in range(k, -1, -1):
                            if self.board[r2][j] in ['.', '+', '*']:
                                counts_bt[k][j] += 1
                            else:
                                break
                        k -= 1

        for i in range(self.length):
            for j in range(self.width):
                if self.board[i][j] == '#':
                    k = j + 1
                    while k < self.width and self.board[i][k] in ['.', '+', '*']:
                        for c2 in range(k, self.width):
                            if self.board[i][c2] in ['.', '+', '*']:
                                counts_lr[i][k] += 1
                            else:
                                break
                        k += 1

        for i in range(self.length):
            for j in range(self.width-1, -1, -1):
                if self.board[i][j] == '#':
                    k = j - 1
                    while k >= 0 and self.board[i][k] in ['.', '+', '*']:
                        for c2 in range(k, -1, -1):
                            if self.board[i][c2] in ['.', '+', '*']:
                                counts_rl[i][k] += 1
                            else:
                                break
                        k -= 1

        counts = [[max(counts_tb[i][j], counts_bt[i][j], counts_lr[i][j], counts_rl[i][j]) for j in range(self.width)] for i in range(self.length)]

        return counts

    '''
    Name: read_xsb
    Input: xsb_file (str): Path to the xsb file
    Output: board (list): A list of lists representing the board
    Operation: Reads the xsb file and returns a list of lists representing the board
    '''
    # Static method to read the xsb file
    @staticmethod
    def read_xsb(xsb_file):
        with open(xsb_file, 'r') as file:
            board = [list(line.strip()) for line in file]
        return board

    '''
    Name: process_board
    Input: None
    Output: None
    Operation: Processes the board and stores the result in self.processed_board
    '''
    
    '''
        Symbol Definition
    @ warehouse keeper
    + warehouse keeper on goal
    $ box
    ∗ box on goal
    # wall
    . goal
    - floor
    '''
    def init_board(self, row ,col):
        cell = self.board[row][col]
        match cell:
            case '@':
                return "warehouse_keeper"
            case '+':
                return "warehouse_keeper_on_goal"
            case '$':
                return "box"
            case '*':
                return "box_on_goal"
            case '#':
                return "wall"
            case '.':
                return "goal"
            case '-':
                return "floor"
            
    def process_board(self):
        processed_wall = ["\n\n-- Define the wall\n\n"]
        processed_floor_box_wk = ["\n\n-- Define the floor, box and warehouse keeper\n\n"]
        procrssed_goal = ["\n\n-- Define the goal\n\n"]
        for row in range(self.length):
            for col in range(self.width):
                cell=self.board[row][col]
                if cell == '@':
                    processed_floor_box_wk.append(self.floor_box_warrkeeper(row,col))
                elif cell == '+':
                    self.goal_location.append("["+str(row)+"]["+str(col)+"]")
                    procrssed_goal.append(self.goal(row,col))
                elif cell == '$':
                    processed_floor_box_wk.append(self.floor_box_warrkeeper(row,col))
                elif cell == '*':
                    self.goal_location.append("["+str(row)+"]["+str(col)+"]")
                    self.num_of_boxes += self.box_priority[row][col]
                    procrssed_goal.append(self.goal(row,col))
                elif cell == '#':
                    processed_wall.append(self.wall(row,col))
                elif cell == '.':
                    self.goal_location.append("["+str(row)+"]["+str(col)+"]")
                    procrssed_goal.append(self.goal(row,col))
                elif cell == '-':
                    processed_floor_box_wk.append(self.floor_box_warrkeeper(row,col))
                else:
                    print("Invalid cell in the board")
                    return False
        
        self.processed_board.append(processed_wall)
        self.processed_board.append(processed_floor_box_wk)
        self.processed_board.append(procrssed_goal)
        return True
    
    def wall(self,row,col):
        return "next (board["+ str(row)+"]["+str(col)+"]) := (board["+ str(row)+"]["+str(col)+"]);\n"
    
    def goal(self,row,col):
        ro = "next (board["+ str(row)+"]["+str(col)+"]) := case\n"
        # up
        if (self.board[row+1][col] != '#'):
            ro += '    U_able['+ str(row+1)+']['+str(col)+'] & next (shift) = "U" & ' 
            if (self.board[row+1][col] in ['-', '$', '@']):    
                ro += 'board['+ str(row+1)+']['+str(col)+'] = "warehouse_keeper"  : {"warehouse_keeper_on_goal"};\n'
            else:    
                ro += 'board['+ str(row+1)+']['+str(col)+'] = "warehouse_keeper_on_goal"  : {"warehouse_keeper_on_goal"};\n'
            ro +=  '    D_able['+ str(row)+']['+str(col)+'] & next (shift) = "D" & board['+ str(row)+']['+str(col)+'] = "warehouse_keeper_on_goal"  : {"goal"};\n'
            if(row+2<self.length and self.board[row+2][col] != '#' ):
                ro += '    U_able['+ str(row+2)+']['+str(col)+'] & next (shift) = "U" & '
                if (self.board[row+2][col] in ['-', '$', '@']):    
                    ro += 'board['+ str(row+2)+']['+str(col)+'] = "warehouse_keeper"'
                else:    
                    ro += 'board['+ str(row+2)+']['+str(col)+'] = "warehouse_keeper_on_goal"'
                if (self.board[row+1][col] in ['-', '$', '@']):    
                    ro += ' & board['+ str(row+1)+']['+str(col)+'] = "box"  : {"box_on_goal"};\n'
                else:    
                    ro += ' & board['+ str(row+1)+']['+str(col)+'] = "box_on_goal"  : {"box_on_goal"};\n'


        # Down
        if (self.board[row-1][col] != '#'):
            ro += '    D_able['+ str(row-1)+']['+str(col)+'] & next (shift) = "D" & ' 
            if (self.board[row-1][col] in ['-', '$', '@']):	
                ro += 'board['+ str(row-1)+']['+str(col)+'] = "warehouse_keeper"  : {"warehouse_keeper_on_goal"};\n'
            else:	
                ro += 'board['+ str(row-1)+']['+str(col)+'] = "warehouse_keeper_on_goal"  : {"warehouse_keeper_on_goal"};\n'
            ro +=  '    U_able['+ str(row)+']['+str(col)+'] & next (shift) = "U" & board['+ str(row)+']['+str(col)+'] = "warehouse_keeper_on_goal"  : {"goal"};\n'
            if(row-2 >0 and self.board[row-2][col] != '#' ):
                ro +='    D_able['+ str(row-2)+']['+str(col)+'] & next (shift) = "D" & '
                if (self.board[row-2][col] in ['-', '$', '@']):	
                    ro += 'board['+ str(row-2)+']['+str(col)+'] = "warehouse_keeper"'
                else:	
                    ro += 'board['+ str(row-2)+']['+str(col)+'] = "warehouse_keeper_on_goal"'
                if (self.board[row-1][col] in ['-', '$', '@']):	
                    ro += ' & board['+ str(row-1)+']['+str(col)+'] = "box"  : {"box_on_goal"};\n'
                else:	
                    ro += ' & board['+ str(row-1)+']['+str(col)+'] = "box_on_goal"  : {"box_on_goal"};\n'

        # left
        if (self.board[row][col+1] != '#'):
            ro += '    L_able['+ str(row)+']['+str(col+1)+'] & next (shift) = "L" & ' 
            if (self.board[row][col+1] in ['-', '$', '@']):	
                ro += 'board['+ str(row)+']['+str(col+1)+'] = "warehouse_keeper"  : {"warehouse_keeper_on_goal"};\n'
            else:	
                ro += 'board['+ str(row)+']['+str(col+1)+'] = "warehouse_keeper_on_goal"  : {"warehouse_keeper_on_goal"};\n'
            ro +=  '    R_able['+ str(row)+']['+str(col)+'] & next (shift) = "R" & board['+ str(row)+']['+str(col)+'] = "warehouse_keeper_on_goal"  : {"goal"};\n'
            if(col+2<self.width and self.board[row][col+2] != '#' ):
                ro +='    L_able['+ str(row)+']['+str(col+2)+'] & next (shift) = "L" & '
                if (self.board[row][col+2] in ['-', '$', '@']):	
                    ro += 'board['+ str(row)+']['+str(col+2)+'] = "warehouse_keeper"'
                else:	
                    ro += 'board['+ str(row)+']['+str(col+2)+'] = "warehouse_keeper_on_goal"'
                if (self.board[row][col+1] in ['-', '$', '@']):	
                    ro += ' & board['+ str(row)+']['+str(col+1)+'] = "box"  : {"box_on_goal"};\n'
                else:	
                    ro += ' & board['+ str(row)+']['+str(col+1)+'] = "box_on_goal"  : {"box_on_goal"};\n'


        # right
        if (self.board[row][col-1] != '#'):
            ro += '    R_able['+ str(row)+']['+str(col-1)+'] & next (shift) = "R" & ' 
            if (self.board[row][col-1] in ['-', '$', '@']):    
                ro += 'board['+ str(row)+']['+str(col-1)+'] = "warehouse_keeper"  : {"warehouse_keeper_on_goal"};\n'
            else:    
                ro += 'board['+ str(row)+']['+str(col-1)+'] = "warehouse_keeper_on_goal"  : {"warehouse_keeper_on_goal"};\n'
            ro +=  '    L_able['+ str(row)+']['+str(col)+'] & next (shift) = "L" & board['+ str(row)+']['+str(col)+'] = "warehouse_keeper_on_goal"  : {"goal"};\n'
            if(col-2>0 and self.board[row][col-2] != '#' ):
                ro +='    R_able['+ str(row)+']['+str(col-2)+'] & next (shift) = "R" & '
                if (self.board[row][col-2] in ['-', '$', '@']):    
                    ro += 'board['+ str(row)+']['+str(col-2)+'] = "warehouse_keeper"'
                else:    
                    ro += 'board['+ str(row)+']['+str(col-2)+'] = "warehouse_keeper_on_goal"'
                if (self.board[row][col-1] in ['-', '$', '@']):    
                    ro += ' & board['+ str(row)+']['+str(col-1)+'] = "box"  : {"box_on_goal"};\n'
                else:    
                    ro += ' & board['+ str(row)+']['+str(col-1)+'] = "box_on_goal"  : {"box_on_goal"};\n'
        ro += 'TRUE : board['+ str(row)+']['+str(col)+'];\n'
        ro += 'esac;\n\n'
        return ro
    
    
    
    def floor_box_warrkeeper(self,row,col):
        ro = "next (board["+ str(row)+"]["+str(col)+"]) := case\n"

        # up
        if (self.board[row+1][col] != '#'):
            ro += '    U_able['+ str(row+1)+']['+str(col)+'] & next (shift) = "U" & ' 
            if (self.board[row+1][col] in ['-', '$', '@']):    
                ro += 'board['+ str(row+1)+']['+str(col)+'] = "warehouse_keeper"  : {"warehouse_keeper"};\n'
            else:    
                ro += 'board['+ str(row+1)+']['+str(col)+'] = "warehouse_keeper_on_goal"  : {"warehouse_keeper"};\n'
            ro +=  '    D_able['+ str(row)+']['+str(col)+'] & next (shift) = "D" & board['+ str(row)+']['+str(col)+'] = "warehouse_keeper"  : {"floor"};\n'
            if(row+2<self.length and self.board[row+2][col] != '#' ):
                ro +='    U_able['+ str(row+2)+']['+str(col)+'] & next (shift) = "U" & '
                if (self.board[row+2][col] in ['-', '$', '@']):    
                    ro += 'board['+ str(row+2)+']['+str(col)+'] = "warehouse_keeper"'
                else:    
                    ro += 'board['+ str(row+2)+']['+str(col)+'] = "warehouse_keeper_on_goal"'
                if (self.board[row+1][col] in ['-', '$', '@']):    
                    ro += ' & board['+ str(row+1)+']['+str(col)+'] = "box"  : {"box"};\n'
                else:    
                    ro += ' & board['+ str(row+1)+']['+str(col)+'] = "box_on_goal"  : {"box"};\n'
  # Down
        if (self.board[row-1][col] != '#'):
            ro += '    D_able['+ str(row-1)+']['+str(col)+'] & next (shift) = "D" & ' 
            if (self.board[row-1][col] in ['-', '$', '@']):    
                ro += 'board['+ str(row-1)+']['+str(col)+'] = "warehouse_keeper"  : {"warehouse_keeper"};\n'
            else:    
                ro += 'board['+ str(row-1)+']['+str(col)+'] = "warehouse_keeper_on_goal"  : {"warehouse_keeper"};\n'
            ro +=  '    U_able['+ str(row)+']['+str(col)+'] & next (shift) = "U" & board['+ str(row)+']['+str(col)+'] = "warehouse_keeper"  : {"floor"};\n'
            if(row-2 >0 and self.board[row-2][col] != '#' ):
                ro +='    D_able['+ str(row-2)+']['+str(col)+'] & next (shift) = "D" & '
                if (self.board[row-2][col] in ['-', '$', '@']):    
                    ro += 'board['+ str(row-2)+']['+str(col)+'] = "warehouse_keeper"'
                else:    
                    ro += 'board['+ str(row-2)+']['+str(col)+'] = "warehouse_keeper_on_goal"'
                if (self.board[row-1][col] in ['-', '$', '@']):    
                    ro += ' & board['+ str(row-1)+']['+str(col)+'] = "box"  : {"box"};\n'
                else:    
                    ro += ' & board['+ str(row-1)+']['+str(col)+'] = "box_on_goal"  : {"box"};\n'

        # left
        if (self.board[row][col+1] != '#'):
            ro += '    L_able['+ str(row)+']['+str(col+1)+'] & next (shift) = "L" & ' 
            if (self.board[row][col+1] in ['-', '$', '@']):    
                ro += 'board['+ str(row)+']['+str(col+1)+'] = "warehouse_keeper"  : {"warehouse_keeper"};\n'
            else:    
                ro += 'board['+ str(row)+']['+str(col+1)+'] = "warehouse_keeper_on_goal"  : {"warehouse_keeper"};\n'
            ro +=  '    R_able['+ str(row)+']['+str(col)+'] & next (shift) = "R" & board['+ str(row)+']['+str(col)+'] = "warehouse_keeper"  : {"floor"};\n'
            if(col+2<self.width and self.board[row][col+2] != '#' ):
                ro +='    L_able['+ str(row)+']['+str(col+2)+'] & next (shift) = "L" & '
                if (self.board[row][col+2] in ['-', '$', '@']):    
                    ro += 'board['+ str(row)+']['+str(col+2)+'] = "warehouse_keeper"'
                else:    
                    ro += 'board['+ str(row)+']['+str(col+2)+'] = "warehouse_keeper_on_goal"'
                if (self.board[row][col+1] in ['-', '$', '@']):    
                    ro += ' & board['+ str(row)+']['+str(col+1)+'] = "box"  : {"box"};\n'
                else:    
                    ro += ' & board['+ str(row)+']['+str(col+1)+'] = "box_on_goal"  : {"box"};\n'


        # right
        if (self.board[row][col-1] != '#'):
            ro += '    R_able['+ str(row)+']['+str(col-1)+'] & next (shift) = "R" & ' 
            if (self.board[row][col-1] in ['-', '$', '@']):    
                ro += 'board['+ str(row)+']['+str(col-1)+'] = "warehouse_keeper"  : {"warehouse_keeper"};\n'
            else:	
                ro += 'board['+ str(row)+']['+str(col-1)+'] = "warehouse_keeper_on_goal"  : {"warehouse_keeper"};\n'
            ro +=  '    L_able['+ str(row)+']['+str(col)+'] & next (shift) = "L" & board['+ str(row)+']['+str(col)+'] = "warehouse_keeper"  : {"floor"};\n'
            if(col-2>0 and self.board[row][col-2] != '#' ):
                ro +='    R_able['+ str(row)+']['+str(col-2)+'] & next (shift) = "R" & '
                if (self.board[row][col-2] in ['-', '$', '@']):	
                    ro += 'board['+ str(row)+']['+str(col-2)+'] = "warehouse_keeper"'
                else:	
                    ro += 'board['+ str(row)+']['+str(col-2)+'] = "warehouse_keeper_on_goal"'
                if (self.board[row][col-1] in ['-', '$', '@']):	
                    ro += ' & board['+ str(row)+']['+str(col-1)+'] = "box"  : {"box"};\n'
                else:	
                    ro += ' & board['+ str(row)+']['+str(col-1)+'] = "box_on_goal"  : {"box"};\n'

        ro += 'TRUE : board['+ str(row)+']['+str(col)+'];\n'
        ro += 'esac;\n\n'
        return ro
    
    
    def write_define(self):
        ro = ""
        for row in range(1,self.length-1):
                for col in range(1,self.width-1):
                    if (self.board[row][col] != '#'):
                        
                        #upable
                        if(self.board[row-1][col] != '#'):
                            able2=row>2 and (self.board[row-2][col] != '#')
                            able1_floor = self.board[row-1][col] in  ['-', '$', '@']
                            able2_floor = row>2 and self.board[row-2][col] in  ['-', '$', '@']
                            match (able2,able1_floor,able2_floor):
                                case (False, True, _):
                                    ro += '    U_able['+str(row) +'][' + str(col) + '] := board['+ str(row-1)+']['+str(col)+'] = "floor";\n' 
                                case (False, False, _):
                                    ro += '    U_able['+str(row) +'][' + str(col) + '] := board['+ str(row-1)+']['+str(col)+'] = "goal";\n' 
                                case (True, True, True):
                                    ro += '    U_able['+str(row) +'][' + str(col) + '] := (board['+ str(row-1)+']['+str(col)+'] = "floor" ) | ((board['+ str(row-1)+']['+str(col)+'] = "box" ) &  (board['+ str(row-2)+']['+str(col)+'] = "floor"));\n'  
                                case (True, True, False):
                                    ro += '    U_able['+str(row) +'][' + str(col) + '] := (board['+ str(row-1)+']['+str(col)+'] = "floor" ) | ((board['+ str(row-1)+']['+str(col)+'] = "box" ) &  (board['+ str(row-2)+']['+str(col)+'] = "goal"));\n'  
                                case (True, False,True):
                                    ro += '    U_able['+str(row) +'][' + str(col) + '] := (board['+ str(row-1)+']['+str(col)+'] = "goal" ) | ((board['+ str(row-1)+']['+str(col)+'] = "box_on_goal" ) &  (board['+ str(row-2)+']['+str(col)+'] = "floor"));\n'  
                                case (True, False, False):
                                    ro += '    U_able['+str(row) +'][' + str(col) + '] := (board['+ str(row-1)+']['+str(col)+'] = "goal" ) | ((board['+ str(row-1)+']['+str(col)+'] = "box_on_goal" ) &  (board['+ str(row-2)+']['+str(col)+'] = "goal"));\n'  
                        
                        #down_able
                        if(self.board[row+1][col] != '#'):
                            able2= row<self.width-2 and (self.board[row+2][col] != '#')
                            able1_floor = self.board[row+1][col] in  ['-', '$', '@']
                            able2_floor = row<self.width-2 and self.board[row+2][col] in  ['-', '$', '@']
                            match (able2,able1_floor,able2_floor):
                                case (False, True, _):
                                    ro += '    D_able['+str(row) +'][' + str(col) + '] := board['+ str(row+1)+']['+str(col)+'] = "floor";\n'  
                                case (False, False, _):
                                    ro += '    D_able['+str(row) +'][' + str(col) + '] := board['+ str(row+1)+']['+str(col)+'] = "goal";\n'  
                                case (True, True,True):
                                    ro += '    D_able['+str(row) +'][' + str(col) + '] := (board['+ str(row+1)+']['+str(col)+'] = "floor" ) | ((board['+ str(row+1)+']['+str(col)+'] = "box" ) &  (board['+ str(row+2)+']['+str(col)+'] = "floor"));\n'  
                                case (True, True, False):
                                    ro += '    D_able['+str(row) +'][' + str(col) + '] := (board['+ str(row+1)+']['+str(col)+'] = "floor" ) | ((board['+ str(row+1)+']['+str(col)+'] = "box" ) &  (board['+ str(row+2)+']['+str(col)+'] = "goal"));\n'  
                                case (True, False,True):
                                    ro += '    D_able['+str(row) +'][' + str(col) + '] := (board['+ str(row+1)+']['+str(col)+'] = "goal" ) | ((board['+ str(row+1)+']['+str(col)+'] = "box_on_goal" ) &  (board['+ str(row+2)+']['+str(col)+'] = "floor"));\n'  
                                case (True, False, False):
                                    ro += '    D_able['+str(row) +'][' + str(col) + '] := (board['+ str(row+1)+']['+str(col)+'] = "goal" ) | ((board['+ str(row+1)+']['+str(col)+'] = "box_on_goal" ) &  (board['+ str(row+2)+']['+str(col)+'] = "goal"));\n'  
                        
                        #right_able
                        if(self.board[row][col+1] != '#'):
                            able2= (col<self.width-2) and (self.board[row][col+2] != '#')
                            able1_floor = self.board[row][col+1] in  ['-', '$', '@']
                            # if not all of this sign so it is a goal
                            able2_floor = (col<self.width-2 )and( self.board[row][col+2] in  ['-', '$', '@'])
                            match (able2,able1_floor,able2_floor):
                                case (False, True, _):
                                    ro += '    R_able['+str(row) +'][' + str(col) + '] := board['+ str(row)+']['+str(col+1)+'] = "floor";\n' 
                                case (False, False, _):
                                    ro += '    R_able['+str(row) +'][' + str(col) + '] := board['+ str(row)+']['+str(col+1)+'] = "goal";\n'
                                case (True, True,True):
                                    ro += '    R_able['+str(row) +'][' + str(col) + '] := (board['+ str(row)+']['+str(col+1)+'] = "floor" ) | ((board['+ str(row)+']['+str(col+1)+'] = "box" ) &  (board['+ str(row)+']['+str(col+2)+'] = "floor"));\n'  
                                case (True, True, False):
                                    ro += '    R_able['+str(row) +'][' + str(col) + '] := (board['+ str(row)+']['+str(col+1)+'] = "floor" ) | ((board['+ str(row)+']['+str(col+1)+'] = "box" ) &  (board['+ str(row)+']['+str(col+2)+'] = "goal"));\n' 
                                case (True, False,True):
                                    ro += '    R_able['+str(row) +'][' + str(col) + '] := (board['+ str(row)+']['+str(col+1)+'] = "goal" ) | ((board['+ str(row)+']['+str(col+1)+'] = "box_on_goal" ) &  (board['+ str(row)+']['+str(col+2)+'] = "floor"));\n'  
                                case (True, False, False):
                                    ro += '    R_able['+str(row) +'][' + str(col) + '] := (board['+ str(row)+']['+str(col+1)+'] = "goal" ) | ((board['+ str(row)+']['+str(col+1)+'] = "box_on_goal" ) &  (board['+ str(row)+']['+str(col+2)+'] = "goal"));\n'  
                        
                        #left_able
                        if(self.board[row][col-1] != '#'):
                            able2= col>2 and (self.board[row][col-2] != '#')
                            able1_floor = self.board[row][col-1] in  ['-', '$', '@']
                            able2_floor =  col>2 and self.board[row][col-2] in  ['-', '$', '@']
                            match (able2,able1_floor,able2_floor):
                                case (False, True, _):
                                    ro += '    L_able['+str(row) +'][' + str(col) + '] := board['+ str(row)+']['+str(col-1)+'] = "floor";\n' 
                                case (False, False, _):
                                    ro += '    L_able['+str(row) +'][' + str(col) + '] := board['+ str(row)+']['+str(col-1)+'] = "goal";\n'
                                case (True, True,True):
                                    ro += '    L_able['+str(row) +'][' + str(col) + '] := (board['+ str(row)+']['+str(col-1)+'] = "floor" ) | ((board['+ str(row)+']['+str(col-1)+'] = "box" ) &  (board['+ str(row)+']['+str(col-2)+'] = "floor"));\n'
                                case (True, True, False):
                                    ro += '    L_able['+str(row) +'][' + str(col) + '] := (board['+ str(row)+']['+str(col-1)+'] = "floor" ) | ((board['+ str(row)+']['+str(col-1)+'] = "box" ) &  (board['+ str(row)+']['+str(col-2)+'] = "goal"));\n'
                                case (True, False,True):
                                    ro += '    L_able['+str(row) +'][' + str(col) + '] := (board['+ str(row)+']['+str(col-1)+'] = "goal" ) | ((board['+ str(row)+']['+str(col-1)+'] = "box_on_goal" ) &  (board['+ str(row)+']['+str(col-2)+'] = "floor"));\n'  
                                case (True, False, False):
                                    ro += '    L_able['+str(row) +'][' + str(col) + '] := (board['+ str(row)+']['+str(col-1)+'] = "goal" ) | ((board['+ str(row)+']['+str(col-1)+'] = "box_on_goal" ) &  (board['+ str(row)+']['+str(col-2)+'] = "goal"));\n'  
        return ro
    
    '''
    Name: write_smv
    Input: smv_file (str): Path to the smv file
    Output: None
    Operation: Writes the SMV model to the given smv file
    '''
    def write_smv(self, smv_file):
        with open(smv_file, 'w') as file:
            file.write('MODULE main\n')
            
            # Define the variables
            file.write('VAR\n')
            file.write('    board: array 0..' + str(self.length - 1) + ' of array 0..' + str(self.width - 1) + ' of {"warehouse_keeper","warehouse_keeper_on_goal", "box", "box_on_goal", "wall", "goal", "floor"};\n')
            file.write('    shift: {"L" , "R" , "U" , "D" , 0};\n')
            file.write('    count_of_box_on_goals: 0..' + str(self.max_priority_box) + ';\n')
            
            # Define the initial state
            file.write('\n\nASSIGN\n')
            for row in range(self.length):
                for col in range(self.width):
                    file.write('    init(board['+str(row) +'][' + str(col) + ']) := "' +self.init_board(row,col)+'";\n')  
            file.write('    init(shift):= 0;\n')
            file.write('    init(count_of_box_on_goals) := ' +str(self.num_of_boxes) +';\n')
            # Define the U_able, D_able, R_able and L_able variables            
            file.write('\n\nDEFINE\n')
            file.write(self.write_define())
            
	### to be add###

            goal_statements = []
            for i in range(len(self.goal_location)):
                goal_name = f'goal{i+1}'
                file.write(f'    {goal_name} := case  -- for each goal/box on goal in init.\n')
                match = re.match(r'\[(\d+)\]\[(\d+)\]', self.goal_location[i])
                if match:
                    x, y = map(int, match.groups())
                    file.write(f'       board{self.goal_location[i]} = "box_on_goal" : {self.box_priority[x][y]};\n')
                file.write('       TRUE: 0;\n')
                file.write('    esac;\n')
                goal_statements.append(goal_name)
            if self.num_of_boxes == self.max_priority_box:
                file.write(f'    solve := ({" + ".join(goal_statements)}) = '+str(self.num_of_boxes) +';\n')
            else:
                file.write(f'    solve := ({" + ".join(goal_statements)}) > '+str(self.num_of_boxes) +';\n')
            # Write the next state function
            file.write('\n\nASSIGN\n')
            file.write('next (shift) := { "U" , "D" , "L" , "R" };\n')
                        
            
            # Iterate over the processed board
            for row in self.processed_board:
                for cell in row:
                # Write each cell to the smv file
                    file.write(cell)

            # Write the justice part
            file.write(self.justice())
            
            #LTLSPEC
            file.write('LTLSPEC ! F solve\n')        
    
        
     
    '''
    Name: justice
    Input: None
    Output: justice (str): The justice part of the SMV model
    Operation: Returns the justice part of the SMV model
    '''
    def justice(self):
        justice = 'JUSTICE\n'
        justice += self.add_justice()
        justice += '\n'
        return justice

    '''
    Name: add_justice
    Input: None
    Output: justice_string (str): The justice part of the SMV model
    Operation: Adds the justice part of the SMV model
    '''
    def add_justice(self):
        # Iterate over the board and if goal locations not do anything 
        # if it isn't a goal location add the line to the justice part 
        # as !(board[row][col] = "box") |
        # until finish
        justice_single = []
        justice_floor = []
        justice_duo = []
        for row in range(1, self.length-1):  # Start from 1 and end at length-1 to avoid index out of range
            for col in range(1, self.width-1):  # Start from 1 and end at width-1 to avoid index out of range
                cell_location = f"[{row}][{col}]"
                # Check if cell is a corner (has walls on two adjacent sides)
                if self.board[row][col] not in ['#', '.', '*', '+'] and \
                ((self.board[row-1][col] == '#' and self.board[row][col-1] == '#') or \
                    (self.board[row-1][col] == '#' and self.board[row][col+1] == '#') or \
                    (self.board[row+1][col] == '#' and self.board[row][col-1] == '#') or \
                    (self.board[row+1][col] == '#' and self.board[row][col+1] == '#')):
                        justice_single.append(f'!(board{cell_location} = "box")')
                        
                if self.board[row][col] not in ['#', '.', '*', '+']:
                # check if all the column or row is wall
                    #left    
                    if all(self.board[i][col-1] == '#' for i in range(self.length)):
                        # . or + becuase if it is a goal so the box can go inside
                        if('.' not in [self.board[i][col] for i in range(self.length)] and '+' not in [self.board[i][col] for i in range(self.length)]):
                            justice_floor.append(f'!(board{cell_location} = "box")')
                    #right
                    if all(self.board[i][col+1] == '#' for i in range(self.length)):
                        if('.' not in [self.board[i][col] for i in range(self.length)] and '+' not in [self.board[i][col] for i in range(self.length)]):
                            justice_floor.append(f'!(board{cell_location} = "box")')
                    #up
                    if all(self.board[row-1][i] == '#' for i in range(self.width)):
                        if('.' not in [self.board[row][i] for i in range(self.width)] and '+' not in [self.board[row][i] for i in range(self.width)]):
                            justice_floor.append(f'!(board{cell_location} = "box")')
                    #down
                    if all(self.board[row+1][i] == '#' for i in range(self.width)):
                        if('.' not in [self.board[row][i] for i in range(self.width)] and '+' not in [self.board[row][i] for i in range(self.width)]):
                            justice_floor.append(f'!(board{cell_location} = "box")')

                # Check for walls in all directions
                    #up right
                    if self.board[row-1][col] == '#' and self.board[row-1][col+1] == '#':
                        if self.board[row][col+1] != '#':
                            justice_duo.append(f'!(board{cell_location} = "box" & board[{row}][{col+1}] = "box")')
                    #up left
                    if self.board[row-1][col] == '#' and self.board[row-1][col-1] == '#':
                        if self.board[row][col-1] != '#':
                            justice_duo.append(f'!(board[{row}][{col-1}] = "box" & board{cell_location} = "box")')
                    #down right
                    if self.board[row+1][col] == '#' and self.board[row+1][col+1] == '#':
                        if self.board[row][col+1] != '#':
                            justice_duo.append(f'!(board{cell_location} = "box" & board[{row}][{col+1}] = "box")')
                    #down left
                    if self.board[row+1][col] == '#' and self.board[row+1][col-1] == '#':
                        if self.board[row][col-1] != '#':
                            justice_duo.append(f'!(board[{row}][{col-1}] = "box" & board{cell_location} = "box")')
                    #left up
                    if self.board[row][col-1] == '#' and self.board[row+1][col-1] == '#':
                        if self.board[row+1][col] != '#':
                            justice_duo.append(f'!(board{cell_location} = "box" & board[{row+1}][{col}] = "box")')
                    #left down
                    if self.board[row][col-1] == '#' and self.board[row-1][col-1] == '#': 
                        if self.board[row-1][col] != '#':
                            justice_duo.append(f'!(board[{row-1}][{col}] = "box" & board{cell_location} = "box")')
                    #right up
                    if self.board[row][col+1] == '#' and self.board[row+1][col+1] == '#':
                        if self.board[row+1][col] != '#':
                            justice_duo.append(f'!(board{cell_location} = "box" & board[{row+1}][{col}] = "box")')
                    #right down
                    if self.board[row][col+1] == '#' and self.board[row-1][col+1] == '#':
                        if self.board[row-1][col] != '#':
                            justice_duo.append(f'!(board[{row-1}][{col}] = "box" & board{cell_location} = "box")')
        justice = justice_single + justice_floor + justice_duo
        # to remove duplicates
        justice = list(dict.fromkeys(justice)) 
        justice_string = ' &\n '.join(justice[:-1])  # Join all but the last with '|'
        if justice:  # If there are any conditions, add the last one without '|'
            justice_string += ' &\n' + justice[-1] + ';\n'
        return justice_string
    
        

    def run_engine(self, engine, smv_file):
        nuxmv_path = os.path.join(nuxmv_dir, "nuXmv.exe")
        run_com = "nuXmv.exe "
        print(f"Running nuXmv with {engine} engine")
        if engine == 'SAT':
            args = [nuxmv_path, "-bmc", "-bmc_length", "80", smv_file]
            run_com += "-bmc -bmc_length 80 "
        elif engine == 'BDD':
            args = [nuxmv_path, smv_file]
        else:
            print("Invalid engine. Please choose either 'SAT' or 'BDD'")
            return None

        start_time = time.time()
        nuxmv_process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
        term_pros = ""
        def terminate_process():
            nonlocal term_pros
            nuxmv_process.terminate()
            term_pros = " Process terminated after 6 hours "
            print("Process terminated after 6 hours")

        timer = threading.Timer(6 * 60 * 60 , terminate_process)
        timer.start()

        stdout, _ = nuxmv_process.communicate()
        timer.cancel()  # If process ends before 2 hours, cancel the timer

        end_time = time.time()
        execution_time = end_time - start_time  # Time it took for the process to run

        return stdout, execution_time, run_com, term_pros

    '''
    Name: run_smv
    Input: smv_file (str): Path to the smv file
    Output: None
    Operation: Runs the SMV model and prints the result
    '''
    def parallel_run_smv(self, smv_file):
        executor = concurrent.futures.ThreadPoolExecutor()
        try:
            future_to_engine = {executor.submit(self.run_engine, engine, smv_file): engine for engine in ['SAT', 'BDD']}
            futures = list(future_to_engine.keys())
            for future in concurrent.futures.as_completed(future_to_engine):
                engine = future_to_engine[future]
                try:
                    stdout, execution_time, run_com, term_pros = future.result()
                except Exception as exc:
                    print('%r generated an exception: %s' % (engine, exc))
                else:
                    print('%r engine returned %r' % (engine, run_com))
                    # If one engine finishes, cancel the other
                    for other_future in futures:
                        if other_future != future:
                            other_future.cancel()
                    return stdout, execution_time, run_com, term_pros
        finally:
            executor.shutdown(wait=False)
    def run_smv(self, smv_file, engine='SAT'):
        '''
        start_time = time.time()
        nuxmv_path = "C:\\Users\\user\\OneDrive - Bar-Ilan University - Students\\Desktop\\nuXmv-2.0.0-win64\\nuXmv-2.0.0-win64\\bin\\nuXmv.exe"
        result = subprocess.run([nuxmv_path, smv_file], stdout=subprocess.PIPE)
        end_time = time.time()
        print(f'Time taken: {end_time - start_time} seconds')
        print(result.stdout.decode())
        '''
        
        stdout, execution_time, run_com, term_pros = self.parallel_run_smv(smv_file)
        formatted_time = str(timedelta(seconds=execution_time))

        print(f"Execution time: {formatted_time}")
        print(f"Execution time: {execution_time} seconds")
        
        # move on the stdout to find the result
        # Process the output
        #search_string = "-- specification !( F solve)  is false"
        search_string = "State"
        solution_string = "the solution steps are: "
        not_solve_string = "this board cannot be solve"
        solve_print = ""
        counter = 0
        if solution_string in stdout:
            print(f"Output has already been processed")
        elif not_solve_string in stdout:
            print(f"Output cannot be solved")
        elif search_string not in stdout:
            solve_print = "this board cannot be solve"
        else:
            start_index = stdout.find("State: 1.2")
            end_index = stdout.find("solve = TRUE", start_index) + len("solve = TRUE")
            end_index = stdout.find("State:", end_index)
            relevant_content = stdout[start_index:end_index]
            shifts = []
            last_shift = None
            
            for state in relevant_content.split('State:')[1:]:
                for line in state.split('\n'):
                    if "shift" in line:
                        last_shift = line.split('=')[-1].strip().replace('"', '')
                shifts.append(last_shift)
                counter += 1
            self.iteration_results.append(shifts)
            solve_print = solution_string + ' '.join(shifts) + f" ({counter} steps)"
            # if not win from the first time we run so we need to add to the box number one becuase in her we found a solution
            #if len(self.goal_location) != self.num_of_boxes:
            #    self.num_of_boxes +=1
        
        
        with open(smv_file, 'r') as f:
            nuxmv_content = f.read()
        # Find the state changes
        state_changes = re.findall(r'(State:.*?)(?=State:|$)', relevant_content, re.DOTALL)
        # Apply the state changes to the nuxmv file
        for state_change in state_changes:
            board_changes = re.findall(r'(board\[\d+\]\[\d+\]) = "(.*?)"', state_change)
            for board_change in board_changes:
                nuxmv_content = re.sub(r'(init\(' + re.escape(board_change[0]) + r'\) := ).*?;', r'\1"' + board_change[1] + '";', nuxmv_content)
        
        init_statements = re.findall(r'init\((board\[\d+\]\[\d+\])\) := "(.*?)"', nuxmv_content)
        sum_priorities = 0
        for init_statement in init_statements:
            if init_statement[1] == "box_on_goal":
                match = re.match(r'board\[(\d+)\]\[(\d+)\]', init_statement[0])
                if match:
                    x, y = map(int, match.groups())
                    sum_priorities += self.box_priority[x][y]
        
        self.num_of_boxes = sum_priorities
        
        self.iteration_counts.append(execution_time)
        self.iteration_steps += counter
        # Save output to file
        if self.max_priority_box == self.num_of_boxes:
            engine_folder  = 'outputs'
        else:   
            engine_folder  = 'mid_outputs'
        base_name = os.path.basename(smv_file)  # Get the base name of the file
        name_without_ext = os.path.splitext(base_name)[0]  # Remove the extension
        #script_dir = os.path.dirname(os.path.realpath(__file__))  # Get the directory of the current script
        #output_folder = os.path.join(script_dir, engine_folder)  # Create a separate folder for each engine in the script directory
        output_folder = os.path.join(base_folder, engine_folder)  # Create a separate folder for each engine in the script directory
        os.makedirs(output_folder, exist_ok=True)  # Create the folder if it doesn't exist
        output_filename = os.path.join(output_folder, f"Solution_{name_without_ext}.out")  # Append the engine to the filename
        run_com += base_name
        with open(output_filename, "w") as f:
            f.write(f"#####################\n")
            f.write(f"#### nuxmv command: {run_com} ####\n")
            f.write(f"#### {term_pros}Execution time: {execution_time} seconds = {formatted_time} ######\n")
            f.write(f"#### {solve_print} ####\n")
            if engine_folder == 'outputs':
                f.write("#################\n")
                f.write(f"The total solution took {len(self.iteration_counts)} iterations\n")
                for i, (count, steps) in enumerate(zip(self.iteration_counts, self.iteration_results), start=1):
                    f.write(f"Iteration {i} took {count} \n")
                    f.write(f"The steps for iteration {i} are: {steps}\n")
                total_steps = ' '.join([' '.join(sublist) for sublist in self.iteration_results])                
                f.write("#################\n")
                f.write("#####Summary####\n")   
                f.write(f"The total time for all iterations is: {sum(self.iteration_counts)} seconds = "+str(timedelta(seconds=sum(self.iteration_counts)))+"\n")
                f.write(f"The total steps for all iterations are: {total_steps}  ({self.iteration_steps}) steps\n")
            f.write("#################\n\n\n")
            f.write(stdout)
        print(f"Output saved to {output_filename}")
        return output_filename, execution_time
    
    def draw(self,name):
        # Define the color mapping
        # Define the color mapping
        color_mapping = {
            '#': 'black',  # wall
            '@': 'blue',  # warehouse keeper
            '+': 'blue',  # warehouse keeper on goal
            '$': 'yellow',  # box
            '*': 'green',  # box on goal
            ' ': 'white',  # empty
            '.': 'red',  # goal
            '-': 'white',  # floor
        }

        # Convert the board string to a 2D list
        # Convert the characters to colors
        color_board = [[color_mapping[char] for char in row] for row in self.board]

        # Create a figure and a set of subplots
        fig, ax = plt.subplots()

        # Create a colormap from the color board
        cmap = ListedColormap(list(color_mapping.values()))

        # Convert the color board to integers for plotting
        # Create a list of keys in the same order as the colors in the colormap
        keys = ['#', '@', '+', '$', '*', ' ', '.', '-']

        # Convert the color board to integers for plotting
        int_board = [[keys.index(char) for char in row] for row in self.board]
        # The rest of your code remains the same

        # The rest of your code remains the same


        # Create the plot
        ax.imshow(int_board, cmap=cmap)

        # Set the minor ticks to the middle of the cells
        ax.set_xticks(np.arange(-.5, len(self.board[0]), 1), minor=True)
        ax.set_yticks(np.arange(-.5, len(self.board), 1), minor=True)

        # Add grid lines at the minor ticks
        ax.grid(which='minor', color='k', linestyle='-', linewidth=2)
        # Add text and create a separate scatter plot for the goals
        for i in range(len(self.board)):
            for j in range(len(self.board[0])):
                if self.board[i][j] == '.':
                    #ax.scatter(j, i, s=500, c='white', marker='s')
                    ax.scatter(j, i, s=300, c='green', marker='o')
                    ax.scatter(j, i, s=100, c='white', marker='o')
                elif self.board[i][j] in ['$', '*']:
                    ax.text(j, i, 'B', ha='center', va='center', color='r')
                elif self.board[i][j] in ['@', '+']:
                    ax.text(j, i, 'W', ha='center', va='center', color='r')
                # Add a rectangle for each cell
                rect = Rectangle((j-0.5, i-0.5), 1, 1, edgecolor='k', facecolor='none')
                ax.add_patch(rect)

        # Hide the axes
        ax.axis('off')
        destination_folder = os.path.join(base_folder, 'board_images')
        dest_file = os.path.join(destination_folder, name + '.png')
        os.makedirs(destination_folder, exist_ok=True)  # Create the folder if it doesn't exist
        plt.savefig(dest_file)
    
    def update_and_draw(self, state_changes, name):
        # Apply the state changes to the nuxmv file
        for state_change in state_changes:
            board_changes = re.findall(r'(board\[\d+\]\[\d+\]) = "(.*?)"', state_change)
            for board_change in board_changes:
                # Extract the board position and new value
                position = re.findall(r'\[(\d+)\]\[(\d+)\]', board_change[0])[0]
                new_value = board_change[1]

                # Update the board
                self.board[int(position[0])][int(position[1])] = self.get_char_from_string(new_value)

        # Draw the updated board
        self.draw(name)
        
    def get_char_from_string(self, string):
        match string:
            case "warehouse_keeper":
                return '@'
            case "warehouse_keeper_on_goal":
                return '+'
            case "box":
                return '$'
            case "box_on_goal":
                return '*'
            case "wall":
                return '#'
            case "goal":
                return '.'
            case "floor":
                return '-'    
        


# Create a Sokoban object, process the board and write the SMV model
#sokoban = Sokoban(r'C:\Users\user\OneDrive - Bar-Ilan University - Students\תואר שני\סמסטר א\אימות פורמלי וסינטזה\תרגילים\תרגילים של השנה\פרוייקט\xsb_file.txt')
#sokoban.process_board()
#sokoban.write_smv('C:\\Users\\user\\OneDrive - Bar-Ilan University - Students\\Desktop\\nuXmv-2.0.0-win64\\nuXmv-2.0.0-win64\\bin\\soko_file.smv')
#output = sokoban.run_smv(r'C:\Users\user\OneDrive - Bar-Ilan University - Students\Desktop\nuXmv-2.0.0-win64\nuXmv-2.0.0-win64\bin\soko_file.smv')

def process_xsb_files():
    xsb_folder = os.path.join(base_folder, 'maps')
    for filename in os.listdir(xsb_folder):
        if filename.endswith('.txt'):
            xsb_file = os.path.join(xsb_folder, filename)
            base_filename = os.path.splitext(filename)[0]
            smv_file = os.path.join(nuxmv_dir,  base_filename + '_0.smv')

            sokoban = Sokoban(xsb_file)
            print(f"Processing board {filename}")
            if not sokoban.validate_board():
                print(f"The board {filename} is not legal by length or by border.")
                continue  # Skip the current iteration if the board is not valid
            if not sokoban.process_board():
                print(f"The board {filename} is not legal by cell. There is not right cell in it.")
                continue        
            sokoban.write_smv(smv_file)
            # New code to copy the file
            destination_folder = os.path.join(base_folder, 'SMV')
            os.makedirs(destination_folder, exist_ok=True)  # Create the folder if it doesn't exist
            destination_file = os.path.join(destination_folder, os.path.basename(smv_file))
            shutil.copy(smv_file, destination_file)
            sokoban.draw(base_filename+'_0')
            output_sat, time_sat = sokoban.run_smv(smv_file, 'SAT')
            continue_process_files(base_filename,sokoban)

    
        
        
def continue_process_files(base_filename,sokoban):
    # Iterate over the solution files    
    #solution_dir = os.path.join(base_folder, "outputs")
    j = -1
    while(True):
        if sokoban.max_priority_box == sokoban.num_of_boxes:
            output_folder = 'outputs'
        else:
            output_folder = 'mid_outputs'
        solution_dir = os.path.join(base_folder, output_folder)
        
        j += 1
        solution_filename = f"Solution_{base_filename}_{j}.out"
        nuxmv_filename = f"{base_filename}_{j}.smv"
        new_nuxmv_filename = f"{base_filename}_{j+1}.smv"
        print(f"Processing board {new_nuxmv_filename}")

        # Read the solution file
        with open(os.path.join(solution_dir, solution_filename), 'r') as f:
            solution_content = f.read()
        # Check if the solution file contains the string "specification !( F solve)  is true"
        if "specification !( F solve)  is true" in solution_content:
            break  # Exit the loop
        if not "State" in solution_content: # if the solution is not found
            break  # Exit the loop
        start_index = solution_content.find("State: 1.2")
        end_index = solution_content.find("solve = TRUE", start_index) + len("solve = TRUE")
        if end_index == -1:  # "solve = TRUE" not found
            break  # Skip to the next iteration of the loop
        end_index = solution_content.find("State:", end_index)
        relevant_content = solution_content[start_index:end_index]
        # Find the state changes
        state_changes = re.findall(r'(State:.*?)(?=State:|$)', relevant_content, re.DOTALL)
        # Read the nuxmv file
        with open(os.path.join(nuxmv_dir, nuxmv_filename), 'r') as f:
            nuxmv_content = f.read()
        
        # Apply the state changes to the nuxmv file
        for state_change in state_changes:
            board_changes = re.findall(r'(board\[\d+\]\[\d+\]) = "(.*?)"', state_change)
            for board_change in board_changes:
                nuxmv_content = re.sub(r'(init\(' + re.escape(board_change[0]) + r'\) := ).*?;', r'\1"' + board_change[1] + '";', nuxmv_content)
        
        sokoban.update_and_draw(state_changes, base_filename + f'_{j+1}')
        # Calculate the sum of priorities for boxes on goals
        init_statements = re.findall(r'init\((board\[\d+\]\[\d+\])\) := "(.*?)"', nuxmv_content)
        sum_priorities = 0
        for init_statement in init_statements:
            if init_statement[1] == "box_on_goal":
                match = re.match(r'board\[(\d+)\]\[(\d+)\]', init_statement[0])
                if match:
                    x, y = map(int, match.groups())
                    sum_priorities += sokoban.box_priority[x][y]
        
        num_of_goals_pattern = r'(count_of_box_on_goals: 0..)(\d+);'
        num_of_goals = re.search(num_of_goals_pattern, nuxmv_content)
        count_of_box_on_goals_pattern = r'(init\(count_of_box_on_goals\) := )(\d+);'
        match = re.search(count_of_box_on_goals_pattern, nuxmv_content)
        
        solve_line_pattern = r'(solve := \(.+\) (?:=|>) )(\d+)(;)'
        match_solve = re.search(solve_line_pattern, nuxmv_content)

        # Update new_value and new_line
        if match:
            new_value = sum_priorities
            if new_value == int(num_of_goals.group(2)):
                break
            else:
                new_line = match_solve.group(1) + str(new_value) + match_solve.group(3)
                nuxmv_content = nuxmv_content.replace(match_solve.group(0), new_line)
                #add the priority number to the box on goal counter
                nuxmv_content = re.sub(count_of_box_on_goals_pattern, r'\g<1>' + str(new_value) + ';', nuxmv_content)
        
        
        # Locate the line and increment the number
            # Write the updated content to a new nuxmv file
        new_nuxmv_filename = os.path.join(nuxmv_dir, new_nuxmv_filename)
        with open(new_nuxmv_filename, 'w') as f:
            f.write(nuxmv_content)
        destination_folder = os.path.join(base_folder, 'SMV')
        os.makedirs(destination_folder, exist_ok=True)  # Create the folder if it doesn't exist
        destination_file = os.path.join(destination_folder, os.path.basename(new_nuxmv_filename))
        shutil.copy(new_nuxmv_filename, destination_file)
        # Run the updated nuxmv file
        output_sat, time_sat = sokoban.run_smv(os.path.join(nuxmv_dir, new_nuxmv_filename), 'SAT')

def main():
    process_xsb_files()

if __name__ == "__main__":
    main()