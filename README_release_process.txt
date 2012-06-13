A developer doing a release needs to do all of the following:
 1) Check very carefully for the possibility that you have files in your
    check-out that are not in the repository but will end up in the tarball.

 2) Set the version number in setup.py and in the about dialog if not already
    adjusted. Check out previous releases and hg tags to be sure

 3) Make sure there is an entry for the release in CHANGELOG if there isn't
    already.

 4) Make sure all packages are explicitly listed in setup.py and any other
    files that it is important to list in there. These are crucial when
    setup.py install or setup.py bdist are run. Take some cues from past
    listings.
 
 5) Make sure that any files to include in the source package that don't make
    sense to list in setup.py are listed in MANIFEST.in . Take some cues
    from past listings.

 6) Run setup.py sdist and inspect the tarball for files that setup.py and
    MANIFEST.in are supposed to ensure go in there.

 7) Do some final testing by running code direct from the tarball and by
    doing a test installation with ./setup.py install into a directory
    under your control.

 8) Commit any changes made to setup.py, CHANGELOG, and MANIFEST.in

 9) Tag the version number

 10) Remember to push changes, including the tag

 11) Sign and upload the tarball to Savannah

 12) Wait until signed and uploaded tarball is publically available

 13) Close the task related to the relase

 14) Put a release news item on to Savannah and announce to the mailing list.
     Be sure to mention if backwards compatibility was broken, which as per
     README_versions_and_branches.txt should be reflected by a major or
     super-major version number change.

     If doing a major or super major, mention intentions for continued minor
     or bug fix releases in older major series, if any. Mention if decently
     supported upgrade paths are planned.

 15) Update the Bo-Keep website hosted on Savannah

 16) Update entries on Freshmeat and Free Software Directory

 17) Promote news item on reddit and wherever... if there's
     some really, really good stuff compared to last time.
