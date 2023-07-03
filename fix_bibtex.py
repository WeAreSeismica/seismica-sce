import numpy as np
import biblib.bib as bbl
from habanero import Crossref
from argparse import ArgumentParser
from collections import Counter
from urllib.request import Request, urlopen
import os, sys, re, random, string

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

cr = Crossref(mailto="hmark@whoi.edu")  # connection for querying

parser = bbl.Parser()  # parser for bibtex
parsed = parser.parse(open(in_bib,'r'))  # parse the input file with biblib

# get entries
bib_OD = parsed.get_entries()  # returns collections.OrderedDict


# open outfile for writing
fout = open('temp.bib','w')  # for doi'd entries, will overwrite if file exists

# loop entry keys
for key in bib_OD:
    entry = bib_OD[key]

    # TODO check if there's a doi, and use it to query crossref for good ref information if so
    if 'doi' not in entry.keys():  # query crossref and try to get a doi
        q = cr.works(query=entry['title'],query_author=entry['author'],limit=2,select='DOI,title,author')
        print('queried for:\n%s\nby:%s\n' % (entry['title'],entry['author']))
        print('received:\n%s\nfirst auth %s\n%s\n' % (q['message']['items'][0]['title'][0],\
                q['message']['items'][0]['author'][0],\
                q['message']['items'][0]['DOI']))
        iok = input('accept entry [Y]/n:\n') or 'Y'
        if iok.lower() == 'y':
            doi = q['message']['items'][0]['DOI']
        else:
            doi = None

    else:
        if entry['doi'][-1] == '.':  # check if doi ends with . and if it does, get rid of the .
            entry['doi'] = entry['doi'][:-1]
        doi = entry['doi']
    if doi:  # ie not None
        # since there is a DOI, use it to query for a clean citation in case authors messed up
        #if '(' in doi:
        #    pre = doi[0:doi.find('(')]
        #    suff = doi[doi.find(')')+1::]
        #    mid = doi[doi.find('(')+1:doi.find(')')]
        #    ourl = "https://dx.doi.org/"+pre+"\("+mid+"\)"+suff
        #elif '. ' in doi:
        if '. ' in doi:
            ourl = "https://dx.doi.org/"+doi[0:doi.find('. ')]
        else:
            ourl = "https://dx.doi.org/"+doi
        # now try to query crossref for it
        req = Request(ourl, headers=dict(Accept='text/bibliography; style=bibtex'))
        bibtext = urlopen(req).read().decode('utf-8')
        bibtext = bibtext.lstrip()  # clean leading space
        # try to make a unique key; we'll fix these later
        key_yr = re.findall('@[a-z]*{([0-9]{4})',bibtext)[0]
        extra_letters = ''.join(random.choices(string.ascii_letters,k=5))
        pieces = bibtext.split(key_yr)
        start = pieces[0] + extra_letters + key_yr + pieces[1]
        new_pieces = [start,]
        for p in pieces[2:]:
            new_pieces.append(p)
        bibtext_out = key_yr.join(new_pieces)
        fout.write(bibtext_out)
    else:
        fout.write(entry.to_bib())  # just write what we had to start with
        fout.write('\n')

fout.close()


# NOW we reread the temp bib file, which should have all available dois and the best possible
# citation info, and clean it up to look nicer (esp keys)

parser = bbl.Parser()  # parser for bibtex
parsed = parser.parse(open('temp.bib','r'))  # parse the input file with biblib

# get entries
bib_OD = parsed.get_entries()  # returns collections.OrderedDict

# check if all the titles end with an apostrophe; if so, probably an error and they need to 
# be removed (probably quoted titles and anystyle only removed the leading quote)
# this may not be an issue anymore since we should get clean titles from crossref mostly?
# TODO deal with this for things that are not queried
last_char = np.array([bib_OD[key]['title'][-1] for key in bib_OD])
strp_last = False
lc = Counter(last_char)
if max(lc.values()) >= len(last_char)/2:  # this is a red flag
    print('title trailing characters:')
    for i,k in enumerate(lc.keys()):
        print('[%i] %i instances of %s' % (i,lc[k],k))
    irem = int(input('enter index to remove: ') or -1)
    if irem >= 0: 
        strp_last = True  # and we'll remove the one with that index in the keys list
        char_out = list(lc.keys())[irem]

# open outfile for writing
fout = open(out_bib,'w')  # will overwrite if file exists

newkey_list = []  # for tracking keys used in case we need 'a' and 'b'
n_with_doi = 0
n_without_doi = 0
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
    if 'url' in entry.keys():
        if re.search(r"doi\.org",entry['url']):  # check if url is just a doi link
            _ = entry.pop('url')
# TODO if there is a url but no doi and the url is a doi, repurpose

#    if 'pages' in entry.keys():
#        _ = entry.pop('pages')

    if 'pages' in entry.keys():
        entry['pages'] = entry['pages'].rstrip(',')  # get rid of any trailing commas

    if 'note' in entry.keys():
        entry['note'] = re.sub(r'Available at','',entry['note'])
        if len(entry['note']) <= 3:  # if we've only got 3 characters left or less, probably nothing
            _ = entry.pop('note')  # should take care of case with : at the end

    if strp_last:
        if entry['title'].endswith(char_out):
            entry['title'] = entry['title'][:-1]  # remove trailing apostrophe (probably)

    # for each, reformat key to be what we'd look for in inline citations
    # first, count authors: if >2, key is firstauthorEAYYYY, if 2 or less is author(author)YYYY
    # TODO deal with {} in author lists if it comes up
    if len(entry.authors()) > 2:
        newkey = entry.authors()[0].last + 'EA' + entry['year']
    elif len(entry.authors()) == 2:
        newkey = entry.authors()[0].last + entry.authors()[1].last + entry['year']
    elif len(entry.authors()) == 1:
        newkey = entry.authors()[0].last + entry['year']
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
