# docx(/odt?) parsing for Seismica

## dependencies:
- python 3.n (preferably 3.8+)
- numpy
- biblib

A conda environment is a nice way to set this up.

You will also need to have pandoc (pandoc.org/) installed for the initial conversion of the .docx file.

A local installation of the anystyle gem is highly recommended. On a linux machine, this can be obtained by running: `sudo apt install ruby-dev` followed by `sudo gem install anystyle=cli`


## general steps for the conversion process
- convert .docx article file to latex
    - pandoc file.docx -f docx -t latex --wrap=none -s -o file_pandoc.tex

- convert text bibliography into a .bib file by either:
    - running the anystyle gem locally: copy the text of the references into a file (e.g. refs.txt) with one reference per line, and then run `anystyle -f bib parse refs.txt .` to generate the file refs.bib
    - copy-paste bibliography from docx into anystyle.io, copy-paste the output into a new file refs.bib

- fix anystyle bibtex file year fields and keys, make a new .bib file
    - (set input filenames manually in the script)
    - fix_bibtex.py -> file_init.bib

- manually correct any non-ascii keys in bib file, if there are any
    - (these will be printed to stdout so we know they need to be fixed, usually for non-ascii characters)
    - (feels like there should be a way around this but I don't know it)

- parse the pandoc output tex file to a better tex format
    - (set the input filenames manually in the script)
    - parse_pandoc_file.py -> file_init.tex

- run bibtex and pdflatex, look at the output and figure out what needs fixing
    - lualatex file_init.tex -> file_init.pdf
    - bibtex file_init.aux
    - lualatex ''
    - lualatex ''
    - (running at least twice gives inline references a chance to sort themselves out)

- manually link figure files at the right sizes, adjust placement of automated \includegraphics as needed
    - pandoc does not extract image files from word so they will need to be uploaded separately
- manually adjust for extra bits of inline citations (in red), in line citations for multiple papers by the same authors (hopefully in red), and year-only citations (in red)
- add extra hyphenation rules for words latex doesn't know if columns are overfull
- manually add some header metadata eg. volume, doi, editor, dates
- look at junk file and manually reformat/place tables in text where they belong (because I do not understand longtable)


## TODO: 
- make sure catch for supplemental figures/tables works for in-text references
- figure out longtable/table parsing?
- parse extra bits of citations, like 'e.g.,' wherever possible
- more user-friendly startup (ie input filenames, rather than editing scripts)
    - related: complete workflow that runs all scripts in sequence automatically
    - and maybe make this all install as a package?

