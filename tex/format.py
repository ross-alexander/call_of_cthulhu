#!/usr/bin/python3

# ----------------------------------------------------------------------
#
# 2025-12-15: Format YAML file to PDF via jinja template and lualatex
#
# ----------------------------------------------------------------------

import os
import sys
import math
import argparse
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
import jinja2
import random
from collections import Counter

# ----------------------------------------------------------------------
#
# yaml_file_read
#
# Open and decode YAML file
#
# ----------------------------------------------------------------------

def yaml_file_read(path):

    with open(path, encoding='utf-8') as stream:
        data = load(stream, Loader=Loader)
    return data

# ----------------------------------------------------------------------
#
# eval_stat
#
# ----------------------------------------------------------------------

def eval_stat(stattable, expr):
    EDU = stattable['EDU']
    DEX = stattable['DEX']
    return int (eval(expr))


# ----------------------------------------------------------------------
#
# M A I N
#
# ----------------------------------------------------------------------

parser = argparse.ArgumentParser(description='Format character JSON file to LuaLaTeX')
parser.add_argument("-t", "--template", action='store', type=str, required=True, help="Input file", dest="template")
parser.add_argument("-i", "--in", action='store', type=str, required=True, help="Input file", dest="inpath")
parser.add_argument("-o", "--out", action='store', type=str, required=True, help="Output file", dest="outpath")
args = parser.parse_args()

opts = {}

opts['template'] = args.template
opts['inpath'] = args.inpath
opts['outpath'] = args.outpath

yaml = yaml_file_read(opts['inpath'])

if not 'game' in yaml:
    print("Missing 'game' key from YAML file", file=sys.stderr)
    exit(1)

if not 'name' in yaml['game']:
    print("Missing 'name' key from 'game'", file=sys.stderr)
    exit(1)

if not (yaml['game']['name'] == 'Call of Cthulhu 7th Ed'):
    print("Game name must be 'Call of Cthulhu 7th Ed'", file=sys.stdrr)
    exit(1)

if not 'character' in yaml['game']:
    print("'character' key missing from 'game'", file=sys.stderr)
    exit(1)

character = yaml['game']['character']

tbl = {
    'base': {}
}

# ----------------------------------------------------------------------
#
# base
#
# ----------------------------------------------------------------------

base_keys = ['name', 'occupation', 'residence', 'birthplace', 'age', 'gender']
for base in base_keys:
    if not base in character:
        print("key '%s' missing from 'character'" % base, file=sys.stderr)
        exit(1)
    tbl['base'][base] = character[base]
    print("%s: %s" % (base, tbl['base'][base]))

# ----------------------------------------------------------------------
#
# stats
#
# ----------------------------------------------------------------------

if not 'stats' in character:
    print("Key 'stats' missing from 'character'", file=sys.stderr)
    exit(1)

stats = character['stats']
tbl['stats'] = {}
stat_values = []
stat_keys = ['SIZ', 'STR', 'CON', 'DEX', 'APP', 'EDU', 'INT', 'POW']
for stat in stat_keys:
    if not stat in stats:
        print("Stat %s missing from stats" % stat, file=sys.stderr)
        exit(1)
    value = stats[stat]
    stat_values.append(value)
    value_50 = int(value * 0.50)
    value_20 = int(value * 0.20)
    print("%s: %d %d %d" % (stat, value, value_50, value_20))
    tbl['stats'][stat] = {
        'value': value,
        'value_50': value_50,
        'value_20': value_20
        }

# --------------------
# allowed values
# --------------------

stat_allowed = [40, 50, 50, 50, 60, 60, 70, 80]
cnt_allowed = Counter()
cnt_diff = Counter()
for i in stat_allowed:
    cnt_allowed[i] += 1
    cnt_diff[i] += 1
cnt_values = Counter()
for i in stat_values:
    cnt_values[i] += 1

cnt_diff.subtract(cnt_values)
if +cnt_diff:
    print("Stats don't match allowed values: %s (%s vs %s)" % (cnt_diff, cnt_allowed, cnt_values))
    exit(1)


# --------------------
# Luck
# --------------------

if not 'LUCK' in stats:
    print("Stat 'LUCK' missing from stats", file=sys.stdout)
    luck = (random.randint(1,6) + random.randint(1,6) + random.randint(1,6)) * 5
    stats['LUCK'] = luck
tbl['stats']['LUCK'] = stats['LUCK']
print("LUCK: %d" % stats['LUCK'])

# --------------------
# Sanity
# --------------------

if not 'SAN' in stats:
    print("Stat 'SAN' missing from stats", file=sys.stdout)
    stats['SAN'] = {
        'CUR': stats['POW'],
        'MAX': stats['POW'],
    }

san = stats['SAN']
if not 'CUR' in san:
    print("Value 'CUR' missing from 'SAN'", file=sys.stderr)
    exit(1)

if not 'MAX' in san:
    print("Value 'MAX' missing from 'SAN'", file=sys.stderr)
    exit(1)

tbl['stats']['SAN'] = {
    'CUR': san['CUR'],
    'MAX': san['MAX'],
    }
print("SAN: %d/%d" % (san['CUR'],san['MAX']))


# --------------------
# Hit Points
# --------------------

if not 'HP' in stats:
    print("Stat 'HP' missing from stats", file=sys.stdout)
    stats['HP'] = {
        'CUR': int((stats['CON'] + stats['SIZ'])/10.0),
        'MAX': int((stats['CON'] + stats['SIZ'])/10.0),
    }

hp = stats['HP']
if not 'CUR' in hp:
    print("Value 'CUR' missing from 'HP'", file=sys.stderr)
    exit(1)

if not 'MAX' in hp:
    print("Value 'MAX' missing from 'HP'", file=sys.stderr)
    exit(1)

tbl['stats']['HP'] = {
    'CUR': hp['CUR'],
    'MAX': hp['MAX'],
    }
print("HP: %d/%d" % (hp['CUR'],hp['MAX']))

# --------------------
# Magic Points
# --------------------

if not 'MP' in stats:
    print("Stat 'MP' missing from stats", file=sys.stdout)
    stats['MP'] = {
        'CUR': '-',
        'MAX': int((stats['POW'] * 0.20)),
    }

mp = stats['MP']
if not 'CUR' in mp:
    print("Value 'CUR' missing from 'MP'", file=sys.stderr)
    exit(1)

if not 'MAX' in mp:
    print("Value 'MAX' missing from 'MP'", file=sys.stderr)
    exit(1)

tbl['stats']['MP'] = {
    'CUR': mp['CUR'],
    'MAX': mp['MAX'],
    }
print("MP: %s/%s" % (mp['CUR'],mp['MAX']))


# ----------------------------------------------------------------------
#
# Skills
#
# ----------------------------------------------------------------------

skill_table = {
    'Accounting': { 'base': 5},
    'Anthropology': { 'base': 1},
    'Appraise': { 'base': 5},
    'Archaeology': { 'base': 1},
    'Charm': { 'base': 5},
    'Climb': { 'base': 20},
    'Credit Rating': { 'base': 0},
    'Cthulhu Mythos': { 'base': 0},
    'Disguise': { 'base': 5},
    'Dodge': { 'eval': 'DEX/2'},
    'Drive Auto': { 'base': 20},
    'Elec. Repair': { 'base': 10},
    'Fast Talk': { 'base': 5},
    'Brawl': { 'category': 'Fighting', 'base': 25},
    'Handgun': { 'category': 'Firearms', 'base': 20},
    'Rifle/Shotgun': { 'category': 'Firearms', 'base': 25},
    'First Aid': { 'base': 30},
    'History': { 'base': 5},
    'Intimidate': { 'base': 15},
    'Jump': { 'base': 20},
    'Language (Own)': { 'category': 'Language', 'eval': 'EDU'},
    'Law': { 'base': 5},
    'Library Use': { 'base': 20},
    'Listen': { 'base': 20},
    'Locksmith': { 'base': 1},
    'Mech. Repair': { 'base': 10},
    'Medicine': { 'base': 1},
    'Natual World': { 'base': 10},
    'Navigate': { 'base': 10},
    'Occult': { 'base': 5},
    'Op. Heavy Machinary': {'base': 1},
    'Persuade': { 'base': 10},
    'Psychoanalysis': { 'base': 1},
    'Psychology': { 'base': 10},
    'Ride': { 'base': 5},
    'Sleight of Hand': { 'base': 10},
    'Spot Hidden': { 'base': 25},
    'Stealth': { 'base': 20},
    'Swim': { 'base': 20},
    'Throw': { 'base': 20},
    'Track': { 'base': 10},
}

category_table = {
    'Arts/Craft': True,
    'Firearms': True,
    'Fighting': True,
    'Language': True,
    'Pilot': True,
    'Science': True
}

# --------------------
# Check skills from character sheet
# --------------------

if 'skills' in character:
    skills_char = character['skills']
    for name in skills_char.keys():
        value = skills_char[name]
        if not isinstance(value, dict):
            value = {'cur': value}
            skills_char[name] = value
        if not (name in skill_table):
            if 'category' in value:
                category = value['category']
                if not category in category_table:
                    print("%s: Category %s unknown" % (name, category))
            else:
                print("%s: not in table" % (name))
                exit(1)
        if 'category' in value:
            print("%s (%s): %s" % (name, value['category'], value['cur']))
        else:
            print("%s: %s" % (name, value['cur']))
else:
    skills_char = {}

# --------------------
# Sort by category
# --------------------

skill_keys = sorted(skill_table.keys())
for name in skill_keys:
    if not name in skills_char:
        s = skill_table[name]
        if 'category' in s:
            print("%s (%s): added" % (name, s['category']))
        else:
            print("%s: added" % (name))
        skills_char[name] = dict(s)

skills_by_cat = {}
for name in skills_char.keys():
    s = skills_char[name]
    category = s['category'] if 'category' in s else '_base_'
    if not category in skills_by_cat:
        skills_by_cat[category] = {}
    skills_by_cat[category][name] = s

# --------------------
# Check allocation (to be completed)
# --------------------

skills_allowed = [70, 60, 60, 50, 50, 50, 40, 40, 40]

for c in sorted(skills_by_cat.keys()):
    print("%s: %d" % (c, len(skills_by_cat[c])))

# --------------------
# Evaluate all skills
# --------------------

for name,value in skills_char.items():
    if not 'cur' in value:
        if 'base' in value:
            value['cur'] = value['base']
        elif 'eval' in value:
            value['cur'] = eval_stat(stats, value['eval'])
        else:
            print("Skill %s incorrect value" % (skill_key))
            exit(1)
    

# --------------------
# Split base skills over two columns
# --------------------

skills = [
    [],
    [],
    []
]

base = skills_by_cat['_base_']
skill_keys = sorted(base.keys())
skill_count = len(base)
skill_table_size = math.ceil(skill_count/2)
skill_table_index = 0
for index in range(0, skill_count):
    table_num = int(index / skill_table_size)
    table_index = index - (table_num * skill_table_size)
    skill_key = skill_keys[index]
    value = base[skill_key]['cur']
    skills[table_num].append({
        'skill': skill_key,
        'value': value,
    })

categories = [ i for i in skills_by_cat.keys() if i != '_base_' ]
index = 1
for c in categories:
    skills[2].append({
        'skill': c,
        'index': index,
    })
    index += 1
    for name in sorted(skills_by_cat[c].keys()):
        skills[2].append({
            'skill': name,
            'value': skills_by_cat[c][name]['cur']
        })
        index += 1

tbl['skills'] = skills

# --------------------
# Jinja
# --------------------
        
latex_jinja_env = jinja2.Environment(
    block_start_string = '\\BLOCK{',
    block_end_string = '}',
    variable_start_string = '\\VAR{',
    variable_end_string = '}',
    comment_start_string = '\\#{',
    comment_end_string = '}',
    line_statement_prefix = '%%',
    line_comment_prefix = '%#',
    trim_blocks = True,
    autoescape = False,
    loader = jinja2.FileSystemLoader(os.path.abspath('.'))
)

template_path = opts['template']
if not (os.path.exists(template_path) and os.path.isfile(template_path)):
    print("Template %s either does not exist or is not a file" % template_path, file=sys.stderr)
    exit(1)

template = latex_jinja_env.get_template(template_path)
res = template.render(character = tbl)
with open(opts['outpath'], 'w', encoding='utf-8') as stream:
    print(res, file=stream)
