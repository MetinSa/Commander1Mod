import os
import re

dir_path = os.getcwd()
home = os.path.expanduser('~')
bashrc = os.path.abspath(f'{home}/.bashrc')

alias = f'alias c1="{dir_path}/Commander1Mod"'
pattern = re.compile(alias)

def append_to_bashrc():
    with open(bashrc, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if pattern.match(line):
                print('Alias already exists.')
                return
    with open(bashrc, 'a') as f:
        f.write(f'\n{alias}')
        print('Installation complete. Execute Commander1Mod from any directory '
              'which contains parameterfiles by typing "c1".')

if __name__ == '__main__':
    append_to_bashrc()
