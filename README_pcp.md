# NAME
pcp.py: Copies files to and from pCloud to local storage.

# SYNOPSIS
```
python pcp.py [common_options] source destination
```

# DESCRIPTION
`pcp.py` will copy files from pCloud to local storage or vice-versa. A
pCloud-hosted file (i.e. remote) is indicated by a prefix of
`p:`. pCloud pathnames are absolute (i.e. must start with a /).

If destination is a directory, pcp.py will create a file in that directory
with the same file name as the source file.

# OPTIONS
There are no pcp.py-specific command options.

# EXAMPLES
`python pcp.py p:/Music/mp3/tune.mp3 .`
: Copies pCloud file to a file of the same name in the current working
  directory.

`python pcp.py ~/local_file.txt p:/backups/local_file.txt`
: Copies a local file, from the home directory to pCloud. Remote
  directories must already exist.

`python pcp.py ~/src/hello.c p:/`
: Copies a local file from ${HOME}/src to a file with the same name on
  the pCloud root directory.

# NOTES
Under no circumstances should you use this instead of rclone.
