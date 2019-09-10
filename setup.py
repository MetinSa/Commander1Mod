import sys
import os
import re

if len(sys.argv) == 1:
    print('Please pass on the path to commander1 as an argument. '
          '\nRun as following: python setup.py [path_to_commander1]')
    sys.exit()
elif len(sys.argv) == 2:
    commander1path = sys.argv[1]

dir_path = os.getcwd()
home = os.path.expanduser('~')
bashrc = os.path.abspath(f'{home}/.bashrc')

alias = f'alias c1="{dir_path}/Commander1Mod"'
evn_path = f'export COMMANDER1PATH="{commander1path}"'
pattern_alias = re.compile(alias)
pattern_env_path = re.compile(evn_path)

alias_exists = False
env_path_exists = False

with open(bashrc, 'r') as f:
    lines = f.readlines()
    for line in lines:
        if pattern_alias.match(line):
            alias_exists = True
        if pattern_env_path.match(line):
            env_path_exists = True
if not any([alias_exists, env_path_exists]):
    with open(bashrc, 'a') as f:
        if not alias_exists:
            f.write(f'\n{alias}')
            print('Alias c1 appended to bashrc.')
        if not env_path_exists:
            f.write(f'\n{evn_path}')
            print('Commander1 path appended to bashrc as enviornment variable.')

    print("Installation complete. Run Commander1Mod from any directory by typing 'c1'.")
else:
    print("Alias and Commander1 path already exists.")
