### FFmpeg Transcoding Script
-------

A simple python script to automate the generation of ffmpeg commands that preserve all associated tracks and subtitles. 

This script has been tested on Windows and macOS using both Python 2.7 and Python 3.4. If you find any errors in process, please submit a pull request.

#### Requirements
* Python >= 2.7 (also works with Python 3)
* FFmpeg binary
* FFprobe binary

No additional libraries or modules required

#### Usage
```
    -d    Place each file in a separate directory. Will also flatten
    -g    Generate commands only. Do not execute
    -f    Flatten found folder to single output directory
    -t    Specify x264 tuning parameter. Default = film

    -i    Input file or folder (required)
    -o    Output folder path (required)
    -e    Exclude a folder from search
    -r    Regex select files from folder. Perl style. Must be in ''
```
Script expects ffmpeg and ffprobe to be in $PATH. If they are not you will need to specify their location at the top of the script.

Only one output may be specified, but multiple input and excludes may be specified.

FFmpeg transcode command can also be updated as desired. IN_FILE, OUT_FILE, MAPPINGS, and FF_TUNE must remain in the command for the script to function correctly.

#### Examples
```
    python transcode_script.py -dg -i /Users/jdreinhardt/Desktop/test -o /Users/jdreinhardt/Desktop/converted
```
This will generate the ffmpeg commands using a separate subdirectory for each file on output. No conversion will be done in this case because of the `-g` flag. Removing that would then run the commmands.

```
    python transcode_script.py -dg -i /Users/jdreinhardt/Desktop/test -o /Users/jdreinhardt/Desktop/converted -r '^(?:X)'
```
This is the same as the previous example with the addition of a regular expression to filter which files are included in the conversion. In this example only files beginning with X will be included.

```
    python transcode_script.py -i /Users/jdreinhardt/Desktop/test -o /Users/jdreinhardt/Desktop/converted -e /Users/jdreinhardt/Desktop/test/skip -f
```
This will generate and run all ffmpeg commands generated for files found in the test directory, but it will not include any files found in the test/skip folder allowing for more flexibility in usage. This will flatten any heirarchy found to output all files inside the single directory.
