# docx/odt parsing for Seismica

These scripts are for converting docx/odt manuscript submissions into latex, specifically a tex file that will work with the Seismica latex production template. The scripts are a bit janky and not completely tested, so if anything breaks or doesn't work, it's probably my fault, not yours.

## dependencies:
- python 3.n (preferably 3.8+)
- numpy
- [biblib](https://github.com/aclements/biblib)

A [conda](conda.io) environment is a nice way to set this up. Note that biblib is not available through conda or pip, though it can be installed in a conda env by using pip with the downloaded source code. A future version of these scripts may build in relevant parts of biblib since it's under an MIT license and that would remove the dependency on one peron's github-hosted project.

You will also need to have [pandoc](pandoc.org/) installed for the initial conversion of the .docx file.

A local installation of the anystyle gem is recommended but not required as long as the web-hosted [anystyle.io](anystyle.io) exists. On a linux machine, this can be obtained by running: `sudo apt install ruby-dev` followed by `sudo gem install anystyle=cli`

Compiling the output tex file from this set of scripts into a pdf requires the Seismica production tex template, which is available only to Seismica typesetters.


## general steps for the conversion process

- check a few things in the docx/odt file before running pandoc:
    - 2nd and 3rd language abstract headers in the format "Second language abstract: Resumen (Spanish)" 
    - title is the first line of the document
    - headers are using header styles
    - authors are all on one line and affiliations are right after authors, one affiliation per line
    - references or bibliography is the last section of the document
    - template formatting is generally intact

- convert article file to latex
    - docx: `pandoc file.docx -f docx -t latex --wrap=none -s -o file_pandoc.tex`
    - odt: `pandoc file.odt -f odt -t latex --wrap=none -s -o file_pandoc.tex`

- convert text bibliography into a .bib file by either:
    - running the anystyle gem locally: copy the text of the references into a plain text file (e.g. `refs.txt`) with one reference per line, and then run `anystyle -f bib parse refs.txt .` to generate the file `refs.bib` (filename will be the same as the input, with suffix replaced by .bib)
    - copy-pasting bibliography from docx/odt into anystyle.io, and copy-pasting the output into a new .bib file

- fix anystyle bibtex file year fields and keys, make a new .bib file
    - `fix_bibtex.py --ifile refs.bib (--ofile refs_corr.bib)`
        - filenames can be whatever you want; ofile is optional, or the script can set it for you
    - any non-ascii keys will be printed to stdout with option to correct while running script

- parse the pandoc output tex file to a better tex format
    - `parse_pandoc_file.py --bibfile refs.bib --ifile tex_in.tex (--ofile tex_out.tex)`
    - unparsed tables etc will go in `junk.tex`
    - `temp.tex` is used for intermediate stages of parsing

- run bibtex and lualatex, look at the output and figure out what needs fixing
    - `lualatex tex_out.tex` -> `tex_out.pdf`
    - `bibtex tex_out.aux`
    - `lualatex tex_out.tex`
    - `lualatex tex_out.tex`
        - running at least twice gives inline references a chance to sort themselves out

- manually set options (breakmath, fast reports, proof) as necessary
- manually link figure files at the right sizes, adjust placement of automated \includegraphics as needed
    - pandoc does not extract image files from word so they will need to be uploaded separately
- manually adjust for any citations that we couldn't parse (should be in red)
- add extra hyphenation rules for words latex doesn't know if columns are overfull
- manually add header metadata eg. volume, doi, editor, dates
- look at junk file and manually reformat/place tables in text where they belong

## TODO: 
- make sure catch for supplemental figures/tables works for in-text references
- figure out longtable/table parsing?
- check YYYYa/YYYYb citations
- make a docker instance so it's easier for people to run this whole thing
- (incorporate relevant parts of biblib)
