import curses
import math
import sys
import os
import shutil
import subprocess
import time
from curses.textpad import rectangle
from resources.ConfigureParameterFile import ConfigureParameterFile
from resources.Menu import Menu

class Interface(object):
    """Text-based user interface.

    Curses based class which defines windows, menues and everything
    that is to be displayed for the user.
    """
    def __init__(self, stdscr):
        self.stdscr = stdscr
        curses.curs_set(0)
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

        self.savefile = 'param.txt'
        self.tempfile = 'param_temp.txt'

        def get_paths():
            """Gets the path to module location and file execution."""
            self.run_path = os.getcwd()
            self.dir_path = os.path.dirname(os.path.realpath(__file__))
            os.chdir(self.dir_path)
        get_paths()

        def get_window_size():
            """Gets terminal window size."""
            xmin = 100
            ymin = 32
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
            """Initializes the different interface-windows."""
            self.header_win = self.stdscr.subwin(1, 0)
            self.loc_win = self.stdscr.subwin(3, 0)
            self.menu_win = self.stdscr.subwin(7, 0)
            self.info_win = self.stdscr.subwin(self.ymax-2, 0)
        initialize_windows()

        def header():
            """Interface header."""
            title = 'COMMANDER1 MODULE'
            below_title = 37*'='
            self.header_win.addstr(0, self.center_str(below_title),
                                   below_title)
            self.header_win.addstr(0, self.center_str(f' {title} '),
                                   f' {title} ')
            self.header_win.refresh()
        header()

        def load_parameterfile():
            """Selects a parameterfile from the run directory and loads it."""
            parameterfiles = []
            for file in os.listdir(self.run_path):
                if (file.endswith('.txt') and 'param' in file and
                    not file.startswith('#')):
                    parameterfiles.append(file)
            if not parameterfiles:
                raise NameError('No parameter files found in '
                                'current work directory')
            parameterfiles.sort(key=lambda x: os.stat(os.path.join(self.run_path,
                                                                   x)).st_mtime)
            parameterfiles.reverse()
            menu_title = 'Load Parameterfile'
            menu_instructions_first = ['Select parameterfile:',
                                       'ENTER: select highlighted option',
                                       'n: next list']
            menu_instructions = ['Select parameterfile:',
                                 'ENTER: select highlighted option',
                                 'n: next list', 'b: previous list']
            menu_instructions_last = ['Select parameterfile:',
                                      'ENTER: select highlighted option',
                                      'b: previous list']

            max_params_per_menu = 36
            menu_items = [parameterfiles[i*max_params_per_menu:(i+1)*max_params_per_menu]
                          for i in range((len(parameterfiles) + max_params_per_menu-1)
                          //max_params_per_menu)]
            menues = []
            for items in menu_items:
                menu = Menu(menu_title, items, menu_instructions)
                menu.numbered = False
                menues.append(menu)
            if len(menues) == 1:
                menues[0].instructions = ['Select parameterfile:',
                                          'ENTER: select highlighted option']
            else:
                menues[0].instructions = menu_instructions_first
                menues[-1].instructions = menu_instructions_last
            i = 0
            while True:
                parameterfile = self.display_menu(menues[i])
                if parameterfile == 'n':
                    i += 1
                elif parameterfile == 'b':
                    i -= 1
                else:
                    return f'{self.run_path}/{parameterfile}'

        paramfile = load_parameterfile()
        self.config = ConfigureParameterFile(paramfile)

    def get_init_dirs(self):
        """Finds the init directories for the run script."""

        def get_data_dir():
            """Checks if data folder exists."""
            data_dir = 'data'
            for directory in os.listdir(self.run_path):
                if os.path.isdir(os.path.join(self.run_path, data_dir)):
                    return f'{self.run_path}/{data_dir}'
            else:
                raise NameError('Could not find data directory in '
                                f'{self.run_path}.')
        data_dir = get_data_dir()

        dirs = []
        for directory in os.listdir(self.run_path):
            if (os.path.isdir(os.path.join(self.run_path, directory)) and
                'chain' in directory):
                dirs.append(directory)
        if not dirs:
            raise NameError('No chain catalogue found in current work directory')

        dirs.sort(key=lambda x: os.stat(os.path.join(self.run_path, x)).st_mtime)
        dirs.reverse()
        menu_title = 'Continue From Previous Run'
        menu_instructions_first = ['Select Chain Directory:',
                                   'ENTER: select highlighted option',
                                   'n: next list']
        menu_instructions = ['Select Chain Directory:',
                             'ENTER: select highlighted option',
                             'n: next list', 'b: previous list']
        menu_instructions_last = ['Select Chain Directory:',
                                  'ENTER: select highlighted option',
                                  'b: previous list']
        max_dirs_per_menu = 36
        menu_items = [dirs[i*max_dirs_per_menu:(i+1)*max_dirs_per_menu]
                      for i in range((len(dirs) + max_dirs_per_menu-1)
                      //max_dirs_per_menu)]
        menues = []
        for items in menu_items:
            menu = Menu(menu_title, items, menu_instructions)
            menu.numbered = False
            menues.append(menu)
        if len(menues) == 1:
            menues[0].instructions = ['Select Chain Directory:',
                                      'ENTER: select highlighted option']
        else:
            menues[0].instructions = menu_instructions_first
            menues[-1].instructions = menu_instructions_last
        i = 0
        while True:
            chain_dir = self.display_menu(menues[i])
            if chain_dir == 'n':
                i += 1
            elif chain_dir == 'b':
                i -= 1
            elif chain_dir is menues[i].parent:
                return
            else:
                chain_dir = f'{self.run_path}/{chain_dir}'
                break

        instructions = ['ENTER: confirm/cancel(empty field)']
        tag = self.get_user_input(menues[0], 'Input Tag', instructions)
        if not tag:
            return
        sample = self.get_user_input(menues[0], 'Input Sample Number',
                                     instructions)
        if not sample:
            return
        try:
            int(sample)
        except Exception:
            raise ValueError('Sample must be of type <int>.')

        return chain_dir, data_dir, tag, sample

    def center_str(self, string):
        """Centers a string to terminal windows."""
        return self.x_center - len(string)//2

    def update_parameterfile_name(self, new_name):
        """Renames the savefile."""
        if not new_name:
            return
        if not new_name.endswith('.txt'):
            new_name = f'{new_name}.txt'
        self.savefile = new_name

    def save(self, filename):
        """Save the parameterfile after some configuration."""
        os.chdir(self.run_path)
        self.config.write_to_file(filename)
        os.chdir(self.dir_path)

    def user_manual(self):
        """Displayes a short user_manual."""
        self.menu_win.clear()
        title = 'Welcome to Commander1 Module'
        self.menu_win.addstr(1, self.center_str(title), title)
        n_lines = 3
        with open('user-manual.txt', 'r') as f:
            for i, line in enumerate(f):
                if i == 0:
                    x_start = self.x_center - len(line)//2
                n_lines += 1
                self.menu_win.addstr(3+i, x_start, line)
        rectangle(self.menu_win, 0, x_start-2, 2, self.xmax-x_start+2)
        rectangle(self.menu_win, 0, x_start-2, n_lines, self.xmax-x_start+2)
        self.menu_win.refresh()
        self.display_module_info()
        key = self.stdscr.getch()

    def get_user_input(self, menu, title, instructions):
        """Gets user input."""
        loc_str = 37*'_'
        try:
            self.loc_win.addstr(1,self.center_str(loc_str),
                                loc_str)
            self.loc_win.addstr(1,self.center_str(f' {menu.parent.name} '),
                                f' {menu.parent.name} ')
            self.loc_win.addstr(2,self.center_str(loc_str),
                                loc_str)
            self.loc_win.addstr(2,self.center_str(f' {menu.name} '),
                                f' {menu.name} ')
        except AttributeError:
            self.loc_win.addstr(1,self.center_str(loc_str),
                                loc_str)
            self.loc_win.addstr(1,self.center_str(f' {menu.name} '),
                                f' {menu.name} ')

        max_str_len = 35
        box_start = self.x_center - max_str_len//2
        self.loc_win.refresh()
        self.menu_win.clear()
        self.display_module_info()
        rectangle(self.menu_win, 0, box_start - 2, 4+len(instructions),
                  box_start + max_str_len + 2)
        self.menu_win.addstr(0, self.center_str(title), title)

        for i, instruction in enumerate(instructions):
            self.menu_win.addstr(i+4, box_start, instruction)
        self.menu_win.refresh()
        rectangle(self.menu_win, 1, box_start - 1, 3,
                  box_start + max_str_len + 1)
        curses.echo()
        user_input = self.menu_win.getstr(2, box_start,
                                          max_str_len).decode(encoding="utf-8")
        return user_input

    def run_commander(self):
        """Executes commander with given settings."""
        # self.config.write_to_file(self.savefile)
        chain_dir = self.config.json_data['General Settings'].get('CHAIN_DIRECTORY').strip("'")
        if not os.path.isdir(os.path.join(self.run_path, chain_dir)):
            os.mkdir(f'{self.run_path}/{chain_dir}')
        numbands = int(self.config.json_data['General Settings'].get('NUMBAND').split()[0])
        num_proc_per_band = int(self.config.json_data['General Settings'].get('NUM_PROC_PER_BAND').split()[0])
        self.config.write_to_file(f'{self.run_path}/{chain_dir}/{self.savefile}')
        n_processors = numbands*num_proc_per_band
        commander1_path = os.environ.get('COMMANDER1PATH')

        self.menu_win.clear()
        title = ' Run Commander '
        rectangle(self.menu_win, 3, (self.xmax//4)-1, 8, (3*self.xmax//4)+1)
        rectangle(self.menu_win, 1, (self.xmax//4)-2, 15, (3*self.xmax//4)+2)
        self.display_module_info()
        self.menu_win.addstr(0, self.center_str(title), title)
        chdir = 'Chain Directory:'
        parfile = 'Parameterfile:'
        nbands = 'NUMBANDS:'
        nprocs = 'NUMPROCS:'
        run_info = 'Current run settings:'
        self.menu_win.addstr(2, self.center_str(run_info),  run_info)
        self.menu_win.addstr(
            4, self.xmax//4, (f'{parfile:{30}} {self.savefile}'))
        self.menu_win.addstr(
            5, self.xmax//4, (f'{chdir:{30}} {chain_dir}'))
        self.menu_win.addstr(
            6, self.xmax//4, (f'{nbands:{30}} {numbands}'))
        self.menu_win.addstr(
            7, self.xmax//4, (f'{nprocs:{30}} {num_proc_per_band}'))

        description_info = 'Input a short description for the file:'
        instr = 'ENTER: run commander/cancel(empty field)'
        max_str_len = self.xmax//2
        self.menu_win.addstr(10, self.center_str(description_info), description_info)
        self.menu_win.addstr(14, self.xmax//4, instr)
        rectangle(self.menu_win, 11, (self.xmax//4)-1, 13, (3*self.xmax//4)+1)
        curses.echo()
        description = self.menu_win.getstr(12, self.xmax//4,
                                          max_str_len).decode(encoding="utf-8")
        self.menu_win.refresh()
        if description:
            curses.endwin()
            with open(f'{self.run_path}/{chain_dir}/commander_runs.txt', 'a') as f:
                f.write(description)
            bash_command = './runcommander.sh'
            subprocess.call(['bash', '-c', bash_command])
            # subprocess.run('export OMP_NUM_THREADS=1', shell=True)
            # subprocess.run(f'mpirun -n {n_processors} {commander1_path}/commander {self.savefile} 2>&1 | tee {chain_dir}/slurm.txt', shell=True)
            sys.exit()

    def display_module_info(self):
        """Displays author name and patch date."""
        scriptpath = os.path.realpath(__file__)
        day, month, date, clock, year = time.ctime(os.path.getmtime(scriptpath)).split()
        last_modified = f'Last Modified: {date} {month} {year}'
        author_name = 'Written by Metin San'
        self.info_win.addstr(0,self.center_str(author_name), author_name)
        self.info_win.addstr(1,self.center_str(last_modified), last_modified)
        self.info_win.refresh()

    def display_menu(self, menu):
        """Displays a menu and returns the selected option."""
        self.menu_win.clear()
        self.loc_win.clear()

        items_per_col = 12
        menu_len = len(menu.items)
        items = menu.items
        longest_item = max(items, key=len)
        n_cols = math.ceil(menu_len/items_per_col)

        loc_str = 37*'_'
        try:
            self.loc_win.addstr(1,self.center_str(loc_str),
                                loc_str)
            self.loc_win.addstr(1,self.center_str(f' {menu.parent.name} '),
                                f' {menu.parent.name} ')
            self.loc_win.addstr(2,self.center_str(loc_str),
                                loc_str)
            self.loc_win.addstr(2,self.center_str(f' {menu.name} '),
                                f' {menu.name} ')
        except AttributeError:
            self.loc_win.addstr(1,self.center_str(loc_str),
                                loc_str)
            self.loc_win.addstr(1,self.center_str(f' {menu.name} '),
                                f' {menu.name} ')
        self.loc_win.refresh()

        x_space = len(longest_item) + 3
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
        rectangle(self.menu_win, 0, x_init-1, box_len+len(menu.instructions)+1,
                  self.xmax - x_init +1)
        rectangle(self.menu_win,1, x_init, box_len + 1,
                  self.xmax-x_init-increment_box_edge)

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

            elif key == curses.KEY_RIGHT and current_i < menu_len-items_per_col:
                current_i += items_per_col

            elif key == curses.KEY_LEFT and current_i > items_per_col:
                current_i -= items_per_col

            elif key == curses.KEY_ENTER or key in [10, 13]:
                self.menu_win.clear()
                if isinstance(menu.menues.get(items[current_i]), Menu):
                    return menu.menues.get(items[current_i])
                else:
                    return items[current_i]

            elif key == curses.KEY_BACKSPACE or key in [8, 127]:
                if menu.name not in ['Main Menu','Load Parameterfile']:
                    return menu.parent

            elif (key == ord('\t') and
                  'TAB/SPACE: view/edit parameterfile' in menu.instructions):
                self.save(self.tempfile)
                os.chdir(self.run_path)
                curses.endwin()
                subprocess.run(['less', '-S', self.tempfile])
                os.chdir(self.dir_path)
                curses.doupdate()

            elif (key == ord(' ') and
                  'TAB/SPACE: view/edit parameterfile' in menu.instructions):
                self.save(self.tempfile)
                os.chdir(self.run_path)
                curses.endwin()
                subprocess.run(['emacs', '-nw', self.tempfile])
                os.chdir(self.dir_path)
                self.config = ConfigureParameterFile(f'{self.run_path}/{self.tempfile}')
                curses.doupdate()

            elif key == ord('b') and 'b: previous list' in menu.instructions:
                return 'b'
            elif key == ord('n') and 'n: next list' in menu.instructions:
                return 'n'

if __name__ == "__main__":
    def run(stdscr):
        UI = Interface(stdscr)
    curses.wrapper(run)
