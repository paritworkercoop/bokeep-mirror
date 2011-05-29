There are four levels to the Bo-Keep version numbers:

X.Y.Z.s

The top level (X) is the super-major version number. This will only be
incremented when there is a major infrastructural change made. The
current version, 1.0.2 has a super-major version number of 1. Version
2 is currently slated to be the switch to GTK3. Version 3 is currently
slated to be the switch to python 3.

The second level (Y) is the major version number. This will be
incremented whenever a backwards incompatible change is made to the
front end or backend plugin apis, or when backwards incompatible
changes to utility apis provided for plugins are made that are
believed to effect plugins outside the bo-keep codebase. (You'll have
to let us know these exist). The current version, 1.0.2 has a major
version number of 0 (the 1.0 series). Backwards incompatible changes
have been discussed on the bo-keep task list and in some of the
comments regarding a future version 1.1.

The third level (Z) is used for enhancement and bug fix releases. The
next version (1.0.3) from current (1.0.2) will contain both bug fixes
and feature enhacements that don't introduce incompatibilities as
described above regarding major version numbers. The target features
and bugs for these releases are always discussed and tracked on a task
on the bokeep task list. Generally, we will try to keep the number of
bug fixes and feature enhacements targetted for these releases to a
minimum in order to have such releases as often as possible.

The fourth level (s) is used for stable releases that only contain bug
fixes and new features, which includes not only bugs in the breakage
sense of the word, but also updates to real-world tables such as
payroll related rates. For a given enhancement and bug fix release, we
do not gaurentee that a stable releases based on it will be
available. For example, there was never a 1.0.0.1, a 1.0.1.1, or a
1.0.2.1. The existence of stable releases will depend on the level of
interest, developer availability, and the pace of the third level
enhancement/bug releases.

The branches in the mercurial repository hosted on Savannah relate to
the versions and releases as follows:

The default branch will provide an important first impression for many
new developers, so it is important to balance keeping it bleeding edge
with qualty and stability. It should reflect the progress towards the
next ehancement and bug fix release, and all tags for finalized
releases (e.g. not release candidates, alphas, or betas), with the
exception of stable (X.Y.Z.s) should be on changesets in the default
branch.

Changesets should only be pushed to the central repository as part of
the default branch if they are ready for the impression of strangers
who will encounter the default branch and contribute to the current
concensus for bugs and tasks that need to be completed for the next
enhancement and bug fix release. (as reflected in the high level task
listed in the task tracker for such a release) As a special exception,
changesets for new plugins that are not yet ready enough to be exposed
through auto-detection, and to support libraries that only work with
such plugins may also be commited to the default branch and pushed to
the central repo.

Changesets needing review or outside the scope of the next feature and
bug fix release should end up in thier own branches.

Work on a future super-major, or major release should take place in
branches designated for that work and only be merged to the default
branch when once such work is actually completed and ready for
release.

After the merger of a super-major or major release into the default
branch, if there remains interest in additional feature and bug fix
releases in the old series, a branch for that should be established
that should contain the word "old" and the series number (e.g. 1.0) in
the branch name. The tags for releases under such a series should be
on that branch.

If a stable release series (bug fixes only) is established, it should
get its own branch, and the tags for releases should be on changesets
on that branch. (e.g. 1.0.3.1, 1.0.3.5, etc.)
