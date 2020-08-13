# Adding Leaderboards
This section is subject to change, it's based on how I would expect things to
develop.

## How it Works
The leaderboard system is similar to the archive system. It runs as a root user
with access to both the shared volume and the assignment configuration volume.
The leaderboard system listens for encrypted JSON messages, which are sent from
the submit system. They can be arbitrary so must be configured from the
assignment configuration side to send the right message and the leaderboard
system to understand it.

The leaderboard is intended to maintain two files.
1. A file which is only read/writeable by root. Which is used internally as the
  state, stored on the shared volume.
2. A second file, which is readable by any JupyterHub users, that can be
  rendered into a leaderboard by a local user.

The leaderboard is intended to have the following features:
 - Updates at a specific rate, perhaps every 24 hours
 - Allow anonymity
 - Optional Submission
