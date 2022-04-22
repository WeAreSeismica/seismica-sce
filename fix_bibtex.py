import numpy as np
import biblib.bib as bbl
from argparse import ArgumentParser
import os, sys

parser = ArgumentParser()
parser.add_argument('--ifile','-i',type=str,help='path to input file')
parser.add_argument('--ofile','-o',type=str,help='path to output file')
args = parser.parse_args()

in_bib = args.ifile
if in_bib == None:
    in_bib = input('Enter path to input file: ') or 'refs.bib'
assert os.path.isfile(in_bib),'input bibfile does not exist'
out_bib = args.ofile
if out_bib == None:
    of1 = in_bib[:-4]+'_corr.bib'
    out_bib = input('Enter path to output file, or skip to use %s: ' % of1) or of1 
if os.path.isfile(out_bib):
    iq = input('warning: %s already exists. Overwrite? [y]/n: ' % out_bib) or 'y'
    if iq == 'n':
        sys.exit()

parser = bbl.Parser()  # parser for bibtex
parsed = parser.parse(open(in_bib,'r'))  # parse the input file with biblib

# get entries
bib_OD = parsed.get_entries()  # returns collections.OrderedDict

# open outfile for writing
fout = open(out_bib,'w')  # will overwrite if file exists

newkey_list = []  # for tracking keys used in case we need 'a' and 'b'
# loop entry keys
for key in bib_OD:
    entry = bib_OD[key]
    # for each, make 'year' and fill with year from 'date'
    if 'date' in entry.keys():
        if len(entry['date']) == 4: # assume this means it's a year, which is probably true
            entry['year'] = entry['date']
        else: # possibly 'month year'? or some other format, check on that
            entry['year'] = entry['date'].split(' ')[-1]
            if len(entry['year']) != 4:
                print('date is %s, year set to %s' % (entry['date'],entry['year']))
                iy = input('enter corrected year if needed: ') or None
                if iy != None:
                    entry['year'] = iy

    # for each, reformat key to be what we'd look for in inline citations
    # first, count authors: if >2, key is firstauthorEAYYYY, if 2 or less is author(author)YYYY
    if len(entry.authors()) > 2:
        newkey = entry.authors()[0].last + 'EA' + entry['year']
    elif len(entry.authors()) == 2:
        newkey = entry.authors()[0].last + entry.authors()[1].last + entry['year']
    elif len(entry.authors()) == 1:
        newkey = entry.authors()[0].last + entry['year']
    newkey = newkey.replace(" ","")  # get rid of spaces if there are any (like van Keken or something)
    nextletter = 'a'
    if newkey + nextletter in newkey_list:  # already have 'a', try the next letter
        thisauthor = [e for e in newkey_list if e.startswith(newkey)]
        alphabet = [e[-1] for e in thisauthor]
        nextletter = chr(ord(alphabet[-1]) + 1)
    newkey= newkey + nextletter  # this is what we'll use for bibtex

    if len(newkey) != len(newkey.encode()):
        print('key ascii error: ',newkey)  # non-ascii is fine within citations, just not in keys
        newkey2 = input('enter a corrected key to use for this entry: ') or newkey
        if newkey2 == newkey:
            print('not correcting key; this may cause problems later')
        newkey = newkey2

    newkey_list.append(newkey)
    entry.key = newkey

    # write entry to new bib file
    fout.write(entry.to_bib())
    fout.write('\n')

fout.close()
