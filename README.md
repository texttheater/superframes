Superframes
===========

Superframes is an annotation scheme for semantic roles. Like other such
schemes, it is essentially about pinning down, in a machine-readable form, “who
did what to whom”. It is different from other such schemes, such as FrameNet,
VerbNet, PropBank, VerbAtlas, or WiSER in a number of ways. It aims to avoid a
number of practical problems in annotating with those schemes. Find out more in
the [annotation
manual](https://github.com/texttheater/superframes/blob/main/doc/manual/manual.pdf).

Instructions for annotators
---------------------------

### Setup

You need a Unix-like command-line environment such as provided, e.g., by Linux,
Windows Subsystem for Linux (WSL), or Git Bash. You also need to have installed Git
and Python 3.10 or higher.

***NOTE:*** If using Git Bash, you may have to add `winpty ` in front of
commands such as `python3`, `pip3`, and `pyenv` in order for them to work
correctly.

***NOTE:*** WSL is recommended over Git Bash. 

***NOTE:*** You can always re-setup your annotation environment, e.g., for
switching from Git Bash to WSL or when something has gone wrong. Make sure you
have pushed all your annotations to GitHub, delete your `superframes`
directory, and follow these instructions again.

Step 1: clone this repository and cd into the working copy:

    git clone https://github.com/texttheater/superframes
    cd superframes

Step 2 (optional): create a dedicated Virtual Environment. For example, if you
have PyEnv set up:

    pyenv virtualenv 3.12.2 superframes
    pyenv local superframes

Step 3: install required packages.

    pip3 install -r src/python/requirements.txt

Step 4: Switch to your own branch. Replace `$NAME` with your name.

    git switch -c $NAME origin/$NAME

If you get the error message “fatal: invalid refrence origin/$NAME”, it means
that your branch does not yet exist. In this case, do this (replace `$NAME`
with your name):

    git switch -c $NAME

Step 5: Push your branch to the remote. Replace `$NAME` with your name.

    git push -u origin $NAME

### Annotation

To start an annotation session, first go back into the working copy (and
activate your virtual environment).

Step 1: Make sure you are on the correct branch.

    git switch $NAME

Step 2: Get any updates from the main branch.

    git fetch
    git merge origin main

Step 3: Open whatever you are currently annotating (something in `data/`) in
your favorite text editor and annotate away.

***NOTE:*** If using WSL, you can use this command to open the current
directory in Explorer, from where you can open them with a text editor:

    explorer.exe .

***NOTE:*** Example annotations are provided
[here](https://github.com/texttheater/superframes/blob/kilian/data/prince/prince.cusf).

Step 4: Check your annotations with the checker script and fix them if
necessary. For example:

    python3 src/python/check.py data/prince/prince.cusf

Step 5: Commit your changes and push them to GitHub. For example:

    git commit -u -m 'annotated sentences 1-10'
    git push
