#!/usr/bin/env python
# -*- coding: utf-8 -*-
#used to strip out powershell scripts from memory and get stored variable values
import re
import itertools
import operator
import pdb
import collections
import os
import time
import sys
import linecache
import subprocess as sp
import ast 

powerdump = [
  '''==============================
 |  __ \                      
 | |__) |____      _____ _ __ 
 |  ___/ _ \ \ /\ / / _ \ '__|
 | |  | (_) \ V  V /  __/ |   
 |_|   \___/ \_/\_/ \___|_|   ''',
 ''' \x1b[0m\x1b[93m__                       __
 \x1b[0m\x1b[93m\ \        \x1b[0m\x1b[95m \x1b[0m\x1b[92m(   )    \x1b[0m\x1b[93m   / /
  \x1b[0m\x1b[93m\ \_    \x1b[0m\x1b[95m\x1b[0m\x1b[92m(   ) (   \x1b[0m\x1b[93m   _/ /
   \x1b[0m\x1b[93m\__\   \x1b[0m\x1b[95m \x1b[0m\x1b[92m) \x1b[0m\x1b[95m_   \x1b[0m\x1b[92m)   \x1b[0m\x1b[93m /__/
    \x1b[0m\x1b[93m  \\\\   \x1b[0m\x1b[95m ( \_   \x1b[0m\x1b[93m  //
      \x1b[0m\x1b[93m `\ \x1b[0m\x1b[95m_(_\ \)__ \x1b[0m\x1b[93m/'
        \x1b[0m\x1b[95m (____\___)) ''',
 ''' __                       __
 \ \         (   )       / /
  \ \_    (   ) (      _/ /
   \__\    ) _   )    /__/
      \\\\    ( \_     //
       `\ _(_\ \)__ /'
         (____\___)) ''',
   '''  _____  _    _ __  __ _____  
 |  __ \| |  | |  \/  |  __ \ 
 | |  | | |  | | \  / | |__) |
 | |  | | |  | | |\/| |  ___/ 
 | |__| | |__| | |  | | |     
 |_____/ \____/|_|  |_|_|   
Dumps PowerShell From Memory
=============================='''
]


conv_mem_bin_int = lambda bin_val: 0 if bool(bin_val) and bin_val[0] == "\x00" and bin_val == len(bin_val) * bin_val[0] else int(bin_val.rstrip('\x00')[::-1].encode("hex-codec"), 16)

def clear():
  global clear_var
  sp.call(clear_var,shell=True)

def scroll_down():
  print('\n'*5)

class color:
  green = '\x1b[92m'
  red = '\x1b[91m'
  white = '\x1b[97m'
  yellow = '\x1b[93m'
  blue = '\x1b[34m'
  bgblack = '\x1b[40m'
  bgred = '\x1b[101m'
  bgwhite = '\x1b[107m'
  bggreen = '\x1b[102m'
  default = '\x1b[39m'
  termreset = '\x1b[0m'
  brown = '\x1b[95m'

def colorize(fgin, bgin=''):
  def newprint(printdata):
    print(bgin + fgin + printdata + color.termreset)
  return newprint

def newprint(data):
  print(data)

if os.name != 'nt':
  red = colorize(color.red, color.bgblack)
  green = colorize(color.green, color.bgblack)
  white = colorize(color.white, color.bgblack)
  yellow = colorize(color.yellow, color.bgblack)
  blue = colorize(color.blue, color.bgblack)
  alert = colorize(color.white, color.bgred)
  brown = colorize(color.brown, color.bgblack)
  clear_var = 'clear'
else:
  red = newprint
  green = newprint
  white = newprint
  yellow = newprint
  alert = newprint
  blue = newprint
  brown = newprint
  powerdump[1] = powerdump[2]
  clear_var = 'cls'

def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    alert('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))

def take_dump(big_dump):
  menu = [
    '\n============ Load Dump Menu ================',
    'COMMAND |     ARGUMENT       | Explanation  ',
    '========|====================|==============',
    'ld      | /path/to/file.name | load mem dump',
    'ls      | ../directory/path  | list files   ',
    'B       |                    | back to menu  ',
    '============= Loaded File: =================',
    
  ]
  cmd = ''
  while True:
    scroll_down()
    print('\n'.join(menu))
    green(big_dump['mem_dump']['path']+" "+str(big_dump['mem_dump']['length']))
    cmd_arg = re.findall(r'^((?:ld|ls|b|e|back|exit))\s*?([^\s].*)?$', raw_input('============================================\n: ').strip(), re.IGNORECASE)
    if len(cmd_arg) and len(cmd_arg[0]) == 2 and len(cmd_arg[0][1]):
      cmd, arg = cmd_arg[0]
    elif len(cmd_arg) and cmd_arg[0][0].upper() in ['B','E','EXIT','BACK']:
      return False
    elif len(cmd_arg) and cmd_arg[0][0].upper() == "LS":
      cmd = cmd_arg[0][0]
      arg = './'
    else:
      no_option('')
      continue
    if cmd.upper() == "LD" and os.path.isfile(arg):
      try:
        mem_dump = open('wannacookie_mem_1.dmp','rb').read()
        big_dump['mem_dump']['data'] = mem_dump
        big_dump['mem_dump']['length'] = len(mem_dump)
        big_dump['mem_dump']['path'] = arg
        big_dump['mem_data'] = {'variables':[],'script_blocks':[],'stored_variable_values':[],'processed':False}
      except:
        PrintException()
    elif cmd.upper() == "LS" and  os.path.isdir(arg):
      for root, dirs, files in os.walk(arg):
        if not root.endswith('/'):
          root = root+ '/'
        green("\n============= Listing of "+root+" =================")
        if len(dirs):
          green('Dir  - ' + '\nDir  - '.join(list(dirs)))
        tmp_files = [x+' '+str(os.path.getsize(root+x)) for x in files if os.path.isfile(root+x)]
        if len(tmp_files):
          green('File - ' +  '\nFile - '.join(list(tmp_files)))
        raw_input('Enter to Continue...')
        break
    else:
      no_option(cmd)
        
def no_option(selection):
  red('[-] {0} is an invalid option!'.format(selection))
  time.sleep(1)

def find_var_matches(mem_dump, var_names):
  matches = []
  for i in var_names:
    key_val = re.findall(r'(\$\w+?)\s+?\=\s+?(.*?)(?:\r\n|\r|\n|\;)',i)
    for item in key_val:
      for ident,length in re.findall(r'(.{6})..(.{4})'+(item[0][1].encode('UTF-16LE')), mem_dump):
        if length != "\x00\x00\x00\x00" and bool(ident.rstrip('\x00')) and conv_mem_bin_int(length) == len(item[0][1]):
          matches.append(ident)
      if len(matches) > 100:
        return matches

def dump_vars_from_mem(match, mem_dump):
  alldata = []
  for length,data in re.findall(r''+match+'..(....)((?:(?:\x00)?[\x01-\x7F])+)',mem_dump):
    if length != "\x00\x00\x00\x00":
      dec_len = conv_mem_bin_int(length)
      utf8_data = data.replace('\x00','')
      if dec_len == len(utf8_data) and bool(re.search(r'^[\x01-\x7F]+$',utf8_data)) and utf8_data not in alldata:
        alldata.append(utf8_data)
  return alldata


def digest_it(big_dump):
  if big_dump['mem_data']['processed']:
    red('[-] Your memory dump is already processed!')
    time.sleep(1)
    return False
  if not bool(big_dump['mem_dump']['length']):
    red('[-] No Memory Dump Loaded!')
    time.sleep(1)
    return False
  yellow("[i] Please wait, processing memory dump...")
  mem_dump = big_dump['mem_dump']['data']
  script_blocks = [x for x in re.findall(r'(?:(?:\x00)?[\x01-\x7F]){500,}', mem_dump, re.DOTALL) if set(["$"," ","e","t"]).issubset([y[0] for y in collections.Counter(x).most_common(10)]) ]
  if not bool(len(script_blocks)):
    red('[-] No Powershell Scripts Found in Memory')
    return False
  green("[+] Found "+str(len(script_blocks))+" script blocks!")
  var_names = list(set([x.replace('\x00','') for x in re.findall(r'\$(?:(?:\x00)?\w)+?(?:(?:\x00)?\s)+?(?:\x00)?\=(?:(?:\x00)?\s)+?(?:\x00)?.+?(?:\r\n|\r|\n|\;)', ';'.join(script_blocks), re.DOTALL)]))
  if not bool(len(script_blocks)):
    red('[-] No Powershell Variables Found!')
    return False
  green("[+] Found some Powershell variable names to work with...")
  matches = find_var_matches(mem_dump, var_names)
  try:
    match = ''
    match = collections.Counter(matches).most_common(1)[0][0]
  except:
    pass
  if not bool(len(match)):
    red('[-] No Powershell Variables Found!')
    return False
  stored_ascii_powershell_variables = dump_vars_from_mem(match, mem_dump)
  green("[+] Found "+str(len(stored_ascii_powershell_variables))+" ascii variables stored in memory")
  big_dump['mem_data']['variables'] = var_names
  big_dump['mem_data']['script_blocks'] = script_blocks
  big_dump['mem_data']['stored_variable_values'] = stored_ascii_powershell_variables
  big_dump['mem_data']['processed'] = True
  time.sleep(0.5)
  green('\nSuccessfully Processed Memory Dump!\n')
  raw_input('Press Enter to Continue...')
  return False

def sift_the_dump_for_loads(big_dump):
  if not big_dump['mem_data']['processed']:
    red('[-] Memory dump not loaded or not processed!')
    time.sleep(1)
    return False
  menu = [
    '============== Search/Dump PS Script Blocks ===================================',
    'COMMAND        |     ARGUMENT                | Explanation                     ',
    '===============|=============================|=================================',
    'print          | print [all|num]             | print specific or all scripts   ',
    'dump           | dump [all|num] [dest_file]  | dump specific or all scripts    ',
    'contains       | contains [ascii_string]     | script block must contain string',
    'matches        | matches ["python_regex"]    | match python regex inside quotes',
    'len            | len [><=] [byte_size]       | script length >,<,=,>=,<= size  ',
    'clear          | clear [all|num]             | clear all or specific filter num',
    '===============================================================================\n: ',
  ]
  while True:
    for_loop = ["[x for x in big_dump['mem_data']['script_blocks'] ", " ]"]
    search_filters = []
    if len(search_filters):
      filtered_script_blocks = eval(for_loop[0] + ' if ' + ' and '.join(search_filters) + for_loop[-1])
    else:
      filtered_script_blocks = big_dump['mem_data']['script_blocks']
    if len(search_filters):
      print('\n================ Filters ================')
      for filt in search_filters:
        if 'bool(' in filt:
          tmp = 'MATCHES '
        elif ' in ' in filt:
          tmp = "CONTAINS "
        else:
          tmp = "LENGTH "
        green(tmp + filt)
    blue('\n'+str(len(filtered_script_blocks)) + ' powershell script blocks found!')
    selection = raw_input('\n'.join(menu)).strip()
    if selection.upper().startswith('CONTAINS ') and len([x for x in selection.split(' ') if x != '']) > 1:
      sel = selection[9:].strip()
      search_filters.append(sel+' in x ')
    elif selection.upper.startswith('PRINT ') and bool(re.search(r'^print\s+?(:all|\d+)\s+?$', selection, re.IGNORECASE)):
      if 'all' in selection:
        count = 1
        for script in filtered_script_blocks:
          blue(script)
          if bool(raw_input('Script block #'+str(count)+' above.\nType any key to go back and just Enter to Continue...')):
            break
          count += 1
      else:
        sel = int(selection[6:].strip())
        if sel >= 1 and sel <= len(filtered_script_blocks):
          blue(filtered_script_blocks[sel-1])
          raw_input('Press Enter to Continue...')
    elif selection.upper.startswith('DUMP ') and bool(re.search(r'^dump\s+?(?:all|\d+)\s+?([\w\.]+?)$', selection, re.IGNORECASE)):
      opt,
      if 'all' in selection:
        for script in filtered_script_blocks:
          #something here
      else:
        dig,
        if sel >= 1 and sel <= len(filtered_script_blocks):
          #something here
    elif selection.upper().startswith('MATCHES ') and bool(re.search(r'^matches\s+?\".+\"$', selection, re.IGNORECASE)):
      regex = re.findall(r'^matches\s+?\"(.+)\"$',selection)[0]
      search_filters.append(' bool(re.search(r"'+regex+'",x)) ')
    elif selection.upper().startswith('LEN ') and len(selection.split(' ')) > 3 and bool(re.search(r'^len\s+?(?:\>|\<|\>\=|\<\=)\s+?\d+$',selection, re.IGNORECASE)):
      op, dig = re.findall(r'^len\s+?((?:\>|\<|\>\=|\<\=))\s+?(\d+)$',selection)[0]
      if op == ">":
        search_filters.append(' x > '+dig)
      elif op == "<":
        search_filters.append(' x < '+dig)
      elif op == "<=":
        search_filters.append(' x <= '+dig)
      elif op == ">=":
        search_filters.append(' x >= '+dig)
    elif selection.upper().startswith('CLEAR ') and bool(re.search(r'^clear\s+?(?:\d+|all)$',selection, re.IGNORECASE)):
      if bool(re.search(r'^clear\s+?\d+$',selection, re.IGNORECASE)):
        num = int([x for x in selection.split(' ') if x != ""][1])
        if num <= len(search_filters) and num >=1:
          del search_filters[num-1]
      elif 'all' in selection.lower():
        search_filters = []
    elif selection.upper().startswith('B'):
      return False
    else:
      no_option(selection)
  

def main():
  power_dump_functions = {
    '1':take_dump,
    '2':digest_it,
    '3':sift_the_dump_for_loads,
    '4':sift_the_dump_for_loads,
    'E':lambda x:True
  }
  EXIT = False
  menu = [
    '=======================================',
    '1. Load PowerShell Memory Dump File',
    '2. Process PowerShell Memory Dump',
    '3. Search/Dump Powershell Scripts',
    '4. Search/Dump Stored String Variables',
    'e. Exit\n: '
  ]
  big_dump = {
    'mem_dump':{'data':'','length':'','path':''},
    'mem_data':{'variables':[],'script_blocks':[],'stored_variable_values':[],'processed':False}
  }
  while not EXIT:
    if bool(big_dump['mem_dump']['length']):
      print('\n\n\n============ Main Menu ================')
      green('Memory Dump: '+big_dump['mem_dump']['path'])
      green('Loaded     : True')
      if big_dump['mem_data']['processed']:
        green('Processed  : True')
      else:
        red('Processed  : False')
    selection = raw_input('\n'.join(menu)).strip().upper()
    if selection in power_dump_functions.keys():
      EXIT = power_dump_functions[selection](big_dump)
    else:
      no_option(selection)


if __name__ == "__main__":
  blue(powerdump[0])
  brown(powerdump[1])
  blue(powerdump[3])
  main()