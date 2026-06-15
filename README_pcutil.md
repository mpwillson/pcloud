# NAME
pcutil.py: Supports cp and rm utilities for pCloud file management.

# SYNOPSIS
```
python pcutil.py [common_options]
                 {cp [-dr] source destination | rm [-dr] file [file ...]}
```

# DESCRIPTION
`pcutil.py cp` will copy files from pCloud to local storage or vice-versa. A
pCloud-hosted file (i.e. remote) is indicated by a prefix of
`p:`. pCloud pathnames are absolute (i.e. must start with a /).

If destination is a directory, pcutil.py will create a file in that directory
with the same file name as the source file.

Directories/folders will be created as required.

`pcutil.py rm` will delete files and folders from pCloud. The `p:/`
suffix need not be specified, as it is assumed.

# OPTIONS
`pcutil.py` does not provide any addtional options to common_options,
but does support command options following the `cp` or `rm` command
token. This is intended to make their use closer to that of their UNIX
analogues.

```-r```
: For `cp`, copies a source folder/directory to the destination. If the
source path ends with a '/' character, only the contents of source are
copied, not the source folder/directory itself. Destination
folders/directories are created as required.

For `rm`, deletes specified folder(s) recursively. **Use with care.**

```-d```
: `pcutil.py` will not perform any operations, but prints what would
  be done.

# EXAMPLES
`python pcutil.py cp p:/Music/mp3/tune.mp3 .`
: Copies pCloud file to a file of the same name in the current working
  directory.

`python pcutil.py cp ~/local_file.txt p:/backups/not_local.txt`
: Copies a local file, from the home directory, to pCloud folder, backups.

`python pcutil.py cp ~/src/hello.c p:/`
: Copies a local file from ${HOME}/src to a file with the same name on
  the pCloud root directory.

`python pcutil.py cp -r p:/folder dir`
: Recursively copies pCloud folder and its contents to local directory dir.

`python pcutil.py cp -r p:/folder/ dir`
: Recursively copies the contents of pCloud folder to local directory dir.

`python pcutil.py rm tmp-file`
: Deletes the file tmp-file from the pCloud root folder.

`python pcutil.py rm -r saves/stuff`
: Recursively deletes stuff and all its contents from the pCloud saves folder.

`python pcutil.py rm old-folder`
: Deletes an empty folder, old-folder, from the pCloud root folder.


# NOTES
Under no circumstances should you use pcutil.py instead of rclone.

# BUGS
An empty local file cannot be uploaded to pCloud.

Others too many and various to mention.
