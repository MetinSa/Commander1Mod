import curses
import math
import sys
import os
import subprocess
import time
import datetime
from curses.textpad import Textbox, rectangle
from resources.ConfigureParameterFile import ConfigureParameterFile
from resources.Menu import Menu

class Interface(object):

    def __init__(self, stdscr):
        self.stdscr = stdscr
        curses.curs_set(0)
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

        self.savefile = 'param.txt'
        self.tempfile = 'param_temp.txt'

        def check_operative_system():
            if sys.platform.startswith('freebsd'):
                raise SystemError('Commander1 Module only works on linux or OS operative systems.')
            elif sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
                pass
        check_operative_system()

        def get_dir():
            self.run_path = os.getcwd()
            self.dir_path = os.path.dirname(os.path.realpath(__file__))
            os.chdir(self.dir_path)
        get_dir()

        def get_window_size():
            xmin = 99
            ymin = 29
            ymax, xmax = self.stdscr.getmaxyx()
            if ymax < ymin:
                raise curses.error('Window size to small to display UI. '
                                   'Please increase y length')
            elif xmax < xmin:
                raise curses.error('Window size to small to display UI. '
                                   'Please increase x length')
            self.ymax = ymax
            self.xmax = xmax
            self.y_center = ymax//2
            self.x_center = xmax//2
        get_window_size()

        def initialize_windows():
            self.header_win = self.stdscr.subwin(1, 0)
            self.loc_win = self.stdscr.subwin(3, 0)
            self.menu_win = self.stdscr.subwin(7, 0)
            self.info_win = self.stdscr.subwin(self.ymax-2, 0)
        initialize_windows()

        def header():
            title = '--------- COMMANDER1 MODULE ---------'
            self.header_win.addstr(0, self.center_str(title), title)
            self.header_win.refresh()
        header()

        def load_parameterfile():
            parameterfiles = []
            for file in os.listdir(self.run_path):
                if file.endswith('.txt') and 'param' in file:
                    parameterfiles.append(file)
            if not parameterfiles:
                raise NameError('No parameter files found in current work directory')

            menu_title = 'Load Parameterfile'
            menu_instructions = ['Select parameterfile:', 'ENTER: select highlighted option']
            menu = Menu(menu_title, parameterfiles, menu_instructions)
            paramfile = self.display_menu(menu)

            return f'{self.run_path}/{paramfile}'

        paramfile = load_parameterfile()
        self.config = ConfigureParameterFile(paramfile)

    def center_str(self, string):
        return self.x_center - len(string)//2

    def save(self, filename):
        self.config.write_to_file(filename)

    def get_user_input(self, menu, title, instructions):
        try:
            self.loc_win.addstr(1,self.center_str(menu.parent.format_menu_name),
                                menu.parent.format_menu_name)
            self.loc_win.addstr(2,self.center_str(menu.format_menu_name),
                                menu.format_menu_name)
        except AttributeError:
            self.loc_win.addstr(1,self.center_str(menu.format_menu_name),
                                menu.format_menu_name)
        max_str_len = 35
        box_start = self.x_center - max_str_len//2
        self.loc_win.refresh()
        self.menu_win.clear()
        self.display_module_info()
        rectangle(self.menu_win, 0, box_start - 2, 4+len(instructions), box_start + max_str_len + 2)
        self.menu_win.addstr(0, self.center_str(title), title)
        for i, instruction in enumerate(instructions):
            self.menu_win.addstr(i+4, box_start, instruction)
        self.menu_win.refresh()
        rectangle(self.menu_win, 1, box_start - 1, 3, box_start + max_str_len + 1)
        curses.echo()
        user_input = self.menu_win.getstr(2, box_start, max_str_len).decode(encoding="utf-8")
        return user_input

    def display_module_info(self):
        scriptpath = os.path.realpath(__file__)
        last_modified = f'Last modified: {time.ctime(os.path.getmtime(scriptpath))}'
        author_name = 'Written by Metin San'
        self.info_win.addstr(0,self.center_str(author_name), author_name)
        self.info_win.addstr(1,self.center_str(last_modified), last_modified)
        self.info_win.refresh()

    def display_menu(self, menu):
        self.menu_win.clear()
        self.loc_win.clear()

        items_per_col = 12
        menu_len = len(menu.items)
        items = menu.items
        longest_item = max(items, key=len)
        n_cols = math.ceil(menu_len/items_per_col)

        try:
            self.loc_win.addstr(1,self.center_str(menu.parent.format_menu_name),
                                menu.parent.format_menu_name)
            self.loc_win.addstr(2,self.center_str(menu.format_menu_name),
                                menu.format_menu_name)
        except AttributeError:
            self.loc_win.addstr(1,self.center_str(menu.format_menu_name),
                                menu.format_menu_name)
        self.loc_win.refresh()

        x_space = len(longest_item) + 1
        if n_cols == 1:
            x_init = self.x_center - 18
        else:
            x_init = self.xmax//2 - (x_space*n_cols)//2

        for item in menu.items:
            if item.startswith('*'):
                if menu_len > items_per_col:
                    box_len = items_per_col + 2
                else:
                    box_len = menu_len + 2
            else:
                if menu_len > items_per_col:
                    box_len = items_per_col + 1
                else:
                    box_len = menu_len + 1

        if self.xmax % 2 == 0:
            increment_box_edge = 0
        else:
            increment_box_edge = 0
        rectangle(self.menu_win, 0, x_init-1, box_len + len(menu.instructions)+2,
                  self.xmax - x_init +1)
        rectangle(self.menu_win,1, x_init, box_len + 1, self.xmax - x_init
                  - increment_box_edge)

        if menu.instructions:
            for i, instructions in enumerate(menu.instructions):
                if i == 0:
                    self.menu_win.addstr(i,self.center_str(instructions),
                                         instructions)
                else:
                    self.menu_win.addstr(box_len + 2 + (i-1), x_init+1,
                                         instructions)

        self.display_module_info()
        current_i = 0
        while 1:
            for i, item in enumerate(items):
                if menu_len > items_per_col:
                    x = x_init +  int(x_space*(i//items_per_col)) + 1
                    y = i  - int((items_per_col)*((i)//items_per_col)) + 2
                else:
                    if item.startswith('*'):
                        y = i + 3
                    else:
                        y = i + 2
                    x = self.center_str(longest_item) - 1

                item = item.strip("'")
                if menu.numbered:
                    item = f'{i+1}. {item}'

                if i == current_i:
                    self.menu_win.attron(curses.color_pair(1))
                    self.menu_win.addstr(y, x, item.replace('*',''))
                    self.menu_win.attroff(curses.color_pair(1))
                else:
                    self.menu_win.addstr(y, x, item.replace('*',''))
            self.menu_win.refresh()

            key = self.stdscr.getch()
            if key == curses.KEY_UP:
                if menu_len < items_per_col and current_i == 0:
                    current_i = menu_len - 1
                elif current_i != 0:
                    current_i -= 1

            elif key == curses.KEY_DOWN:
                if menu_len < items_per_col and current_i == menu_len - 1:
                    current_i = 0
                elif current_i != menu_len - 1:
                    current_i += 1

            elif key == curses.KEY_RIGHT and current_i < menu_len - items_per_col:
                current_i += items_per_col

            elif key == curses.KEY_LEFT and current_i > items_per_col:
                current_i -= items_per_col

            elif key == curses.KEY_ENTER or key in [10, 13]:
                self.menu_win.clear()
                if "Return" in items[current_i]:
                    return menu.parent

                elif isinstance(menu.menues.get(items[current_i]), Menu):
                    return menu.menues.get(items[current_i])
                else:
                    return items[current_i]

            elif key == curses.KEY_BACKSPACE or key in [8, 127]:
                if menu.name not in ['Main Menu','Load Parameterfile']:
                    return menu.parent

            elif key == ord('\t') and 'TAB/SPACE: view/edit parameterfile' in menu.instructions:
                self.config.write_to_file(self.tempfile)
                curses.endwin()
                subprocess.run(['less', '-S', self.tempfile])
                curses.doupdate()

            elif key == ord(' ') and 'TAB/SPACE: view/edit parameterfile' in menu.instructions:
                self.config.write_to_file(self.tempfile)
                curses.endwin()
                subprocess.run(['emacs', '-nw', self.tempfile])
                curses.doupdate()


if __name__ == "__main__":

    def run(stdscr):
        UI = Interface(stdscr)
    curses.wrapper(run)
