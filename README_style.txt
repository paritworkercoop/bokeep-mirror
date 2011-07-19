PEP 8 is the "official" style guide for BoKeep, though you'll find plenty of
code that violates it, some on the "A Foolish Consistency is the Hobgoblin of
Little Minds" basis, and others of the basis of ignorance or laziness.
After all, we got to commit 920 prior to this being added!
http://www.python.org/dev/peps/pep-0008/

PEP 257 is our official docstring guide.
http://www.python.org/dev/peps/pep-0257/
You'll find plenty of module, class, and function summaries that are more
than one line though -- my brevity is hard.

README docs like this one are to be written in plaintext with two newlines
between paragraphs and 80 character hard wrap justification.

Long form manual and tutorial documentation should be written using docutils,
see:
http://docutils.sourceforge.net/
http://docutils.sourceforge.net/docs/
http://www.python.org/dev/peps/pep-0216/
http://www.python.org/dev/peps/pep-0256/
http://www.python.org/dev/peps/pep-0258/
http://www.python.org/dev/peps/pep-0287/

An eventual long term goal is to include enough high quality docutils documents,
docstrings and docutils text in the source that we can do:
$ ./setup.py book
and get a full html, pdf, etc book with the entire source code, manuals,
and tutorials presented in a sane order in the spirit of literate programming.

That is, the BoKeep book, generated entirely from the source tree! Some
consistent style in code and docstrings will lay the foundation for this
ambitious long term project.
