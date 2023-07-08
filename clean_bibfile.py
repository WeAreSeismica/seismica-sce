import biblib.bib as bbl
from argparse import ArgumentParser
from collections import OrderedDict
import os, re

####
# check a bibtex file against a tex file and clean out any unused references in the bib file
# writes out 2 files: clean bib file (*_clean.bib) and a file with the unused entries (junk.bib or name provided)

# usage:
    # python3 clean_bibfile.py -b best_bibfile.bib -t copyedited_texfile.tex [-n excess_entries.bib]
####

parser = ArgumentParser()
parser.add_argument('--bibfile','-b',type=str,help='path to bib file')
parser.add_argument('--texfile','-t',type=str,help='path to tex file')
parser.add_argument('--nahfile','-n',type=str,help='path to file for unused entries',default='junk.bib')
args = parser.parse_args()

# make sure there are inputs, warn for overwrite
in_bib = args.bibfile
assert in_bib is not None, 'input bibfile needed (-b)'
in_tex = args.texfile
assert in_tex is not None, 'input texfile needed (-b)'
o_clean = in_bib.rstrip('.bib') + '_clean.bib'
print('output will be in %s (good entries) and %s (unused entries)' % (o_clean,args.nahfile))
if os.path.isfile(args.nahfile):
    input('%s already exists and will be overwritten [hit enter to continue]' % args.nahfile)
if os.path.isfile(o_clean):
    input('%s already exists and will be overwritten [hit enter to continue]' % o_clean)

# parse the bibtex file for entries
parser = bbl.Parser()
parsed = parser.parse(open(in_bib, 'r'))
bib_init = parsed.get_entries()  # initial bibtex
bib_used = OrderedDict()    # for the entries that *should* be in the file
bib_rogue = OrderedDict()   # for the entries that are not referenced in the tex

# read the tex file as one long string
with open(in_tex,'r') as file:
    all_tex_text = file.read()

cks = ','.join(re.findall(r'cite.{(.*?)}',all_tex_text)).split(',')  # join and split for individual keys
cks2 = ','.join(re.findall(r'cite.\[.*?\]{(.*?)}',all_tex_text)).split(',')  # for cite* with pre and/or post text
cks.extend(cks2)
cks = [e.lstrip().rstrip() for e in cks]

for key in bib_init.keys():
    entry = bib_init[key]
    if key in cks:
        bib_used[key] = entry
    else:
        bib_rogue[key] = entry

# write things out
# first write out the *unused* entries in a separate file in case we need them later
with open(args.nahfile, 'w') as f:
    for key in bib_rogue.keys():
        f.write(bib_rogue[key].to_bib())
        f.write('\n')

# then write a new clean bib file with only the entries that are actually used
with open(o_clean, 'w') as f:
    for key in bib_used.keys():
        f.write(bib_used[key].to_bib())
        f.write('\n')