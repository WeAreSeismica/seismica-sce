import numpy as np
import biblib.bib as bbl
import dateutil.parser as dp
from habanero import Crossref
from argparse import ArgumentParser
from collections import OrderedDict
from urllib.request import Request, urlopen, HTTPError
import os, sys, re, random, string

####
# clean up bibtex file produced by anystyle
    # try to find dois where they are missing
    # get nice citations from crossref when we do have dois
    # neaten up bibtex entries, with clean keys for docx/odt parsing
# TODO un-tex/html-escape special characters from crossref search? like &lt; and {\'{e}} or whatever
####

parser = ArgumentParser()
parser.add_argument('--ifile','-i',type=str,help='path to input file')
parser.add_argument('--ofile','-o',type=str,help='path to output file')
parser.add_argument('--keepkeys','-k',action='store_true')  # set this flag to keep input keys
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

cr = Crossref(mailto="tech@seismica.org")  # connection for querying

parser = bbl.Parser()  # parser for bibtex
parsed = parser.parse(open(in_bib,'r'))  # parse the input file with biblib

# get entries
bib_OD = parsed.get_entries()  # returns collections.OrderedDict
bib_new = OrderedDict()

for key in bib_OD:  # loop entry keys
    entry = bib_OD[key]
    # TODO if url us a key and doi is not, check if url is actually a doi
    doi = None   # to start
    if 'doi' in entry.keys(): # get provided doi, check to make sure it will work
        if entry['doi'][-1] == '.':  # check if doi ends with . and if it does, get rid of the .
            entry['doi'] = entry['doi'][:-1]
        doi = entry['doi']
        if '. ' in doi:
            ourl = "https://dx.doi.org/"+doi[0:doi.find('. ')]
        else:
            ourl = "https://dx.doi.org/"+doi
        req = Request(ourl, headers=dict(Accept='application/x-bibtex'))
        try:
            bibtext = urlopen(req).read().decode('utf-8')
        except HTTPError:
            doi = None  # authors were wrong or anystyle messed up; try a search

    if not doi:  # try querying crossref for this
        q = cr.works(query=entry['title'],query_author=entry['author'],limit=1,select='DOI,title,author')
        print('\nqueried for:\ntitle: %s\nby: %s\n' % (entry['title'],entry['author']))
        # TODO print first author nicer; need to catch 'name' case as well as 'given' 'family'
        print('received:\ntitle: %s\n1st auth: %s\ndoi: %s\n' % (q['message']['items'][0]['title'][0],\
                q['message']['items'][0]['author'][0],\
                q['message']['items'][0]['DOI']))
        iok = input('accept entry [Y]/n: ') or 'Y'
        if iok.lower() == 'y':
            doi = q['message']['items'][0]['DOI']
        else:
            doi = None

    if doi:  # if doi not none, use to query for a clean citation
        if '. ' in doi:
            ourl = "https://dx.doi.org/"+doi[0:doi.find('. ')]
        else:
            ourl = "https://dx.doi.org/"+doi
        req = Request(ourl, headers=dict(Accept='application/x-bibtex'))
        try:
            bibtext = urlopen(req).read().decode('utf-8')
            # get whatever the key is that comes from crossref
            pieces = bibtext.split('\n')
            key0 = pieces[0].split('{')[1].rstrip(',')
            # parse to an Entry and check to make sure all the pieces are there
            parser = bbl.Parser()
            parsed = parser.parse(bibtext)
            entry_new = parsed.get_entries()[key0]
            rereparse = False
            if 'author' not in entry_new.keys() and 'author' in entry.keys():  # avoid losing info
                entry_new['author'] = entry['author']
                rereparse = True
            if 'title' not in entry_new.keys() and 'title' in entry.keys():
                entry_new['title'] = entry['title']
                rereparse = True
            if rereparse:  # info has been added, re-parse to reset field_pos
                parser = bbl.Parser()
                parsed = parser.parse(entry_new.to_bib())
                entry_new = parsed.get_entries()[key0]
        except HTTPError:  # shouldn't hit this bc crossref dois should work, but who knows
            entry_new = entry  # keep whatever the initial entry was
                        
    else:  # no doi, from authors or from crossref
        entry_new = entry  # keep whatever the initial entry was

    entry_new.key = key         # keep the input key for now
    bib_new[key] = entry_new    # as that should be unique, even from anystyle

# now go through the new OrderedDict with "cleaner" entries and fix up as needed

# open final outfile for writing
fout = open(out_bib,'w')  # will overwrite if file exists

newkey_list = []  # for tracking keys used in case we need 'a' and 'b'
n_with_doi = 0
n_without_doi = 0
for key in bib_new:  # loop entry keys
    entry = bib_new[key]
    # for each, if 'date' is a key, make 'year' based on 'date'
    if 'date' in entry.keys():
        if len(entry['date']) == 4: # assume this means it's a year, which is probably true
            entry['year'] = entry['date']
        else: # some other format, try to parse
            try_year = dp.parse(entry['date']).year
            print('date is %s, year set to %s' % (entry['date'],try_year))
            iy = input('enter corrected year if needed: ') or None
            if iy != None:
                entry['year'] = iy
    if 'url' in entry.keys():
        if re.search(r"doi\.org",entry['url']):  # check if url is just a doi link
            _ = entry.pop('url')  # if it is, we should have used it earlier and can clean now

    # TODO decide if pages should ever be kept
    # tends to be a messy field; sometimes an id#, sometimes page range, sometimes number of pages
#    if 'pages' in entry.keys():  
#        _ = entry.pop('pages')

    if 'pages' in entry.keys():
        entry['pages'] = entry['pages'].rstrip(',')  # at least get rid of any trailing commas
        if "n/a" in entry['pages']:  # sometimes get "n/a -- n/a" or similar from crossref
            _ = entry.pop('pages')

    if 'note' in entry.keys():
        entry['note'] = re.sub(r'Available at','',entry['note'])
        if len(entry['note']) <= 3:  # if we've only got 3 characters left or less, probably nothing
            _ = entry.pop('note')  # should take care of case with : at the end

    if entry['title'].endswith("'"):
        entry['title'] = entry['title'][:-1]  # remove trailing apostrophe if present

    if not args.keepkeys:  # if we want to make new entry keys (docx/odt input file)
        if 'author' not in entry.keys():
            entry['author'] = entry['editor']  # TODO catch other cases??
            parser = bbl.Parser()  # need to re-parse to get field_pos right in Entry
            parsed = parser.parse(entry.to_bib())
            entry = parsed.get_entries()[key]

        # clean up first author name: no {}, no spaces
        auth0 = re.sub(r'[ ]',r'',entry.authors()[0].last.lstrip('{').rstrip('}'))

        # for each, reformat key to be what we'd look for in inline citations
        # first, count authors: if >2, key is firstauthorEAYYYY, if 2 or less is author(author)YYYY
        if len(entry.authors()) > 2:
            newkey = auth0 + 'EA' + entry['year']
        elif len(entry.authors()) == 2:
            auth1 = re.sub(r'[ ]',r'',entry.authors()[1].last.lstrip('{').rstrip('}'))
            newkey = auth0 + auth1 + entry['year']
        elif len(entry.authors()) == 1:
            newkey = auth0 + entry['year']
        newkey = newkey.replace(" ","")  # get rid of spaces if there are any (like van Keken or something)
        newkey = newkey.replace("-","")  # get rid of hyphens, which tex2jats doesn't like
        nextletter = 'a'
        if newkey + nextletter in newkey_list:  # already have 'a', try the next letter
            thisauthor = [e for e in newkey_list if e.startswith(newkey)]
            alphabet = [e[-1] for e in thisauthor]
            nextletter = chr(ord(alphabet[-1]) + 1)
        newkey = newkey + nextletter  # this is what we'll use for bibtex

        newkey_list.append(newkey)
        entry.key = newkey

    # check if doi field is present
    if 'doi' in entry.keys() or 'DOI' in entry.keys():
        n_with_doi += 1
    else:
        n_without_doi += 1

    # write entry to new bib file
    fout.write(entry.to_bib())
    fout.write('\n')

fout.close()

print('%i items have doi, %i do not have doi' % (n_with_doi, n_without_doi))
print('%.2f percent lack doi' % (100*n_without_doi/(n_with_doi + n_without_doi)))
#print('if many dois are missing, try searching the plain text reference list with %s' % ("https://apps.crossref.org/SimpleTextQuery"))
