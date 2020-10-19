import os
import sys
import subprocess
import json
import getopt
import shlex
import re

ffmpegPath = 'ffmpeg'
ffprobePath = 'ffprobe'
ffprobeCmd = ffprobePath + ' -loglevel quiet -print_format json -show_format -show_streams -show_error -i '
ffmpegCmd = ffmpegPath + ' -i "IN_FILE" -c:v libx264 -crf FF_QUALITY -tune FF_TUNE FF_VFILTERS -c:a copy -scodec copy MAPPINGS ATMOS "OUT_FILE"'

vidExtensions = ['mp4','mkv','mov','mxf','m4v','avi','wmv','ts']
outExtenstion = 'mkv'

files = []
commands = []

def generateCommands(files, output, directory, flatten, tune, quality, videoFilter):
    '''
    Generate full ffmpeg command to be executed. Will be run using external binary
    '''
    for file in files:
        outpath = output
        cmd = parseCommandParameters(ffmpegCmd, file, tune, quality, videoFilter)
        filename = os.path.splitext(os.path.basename(file[0]))[0]
        if (directory):
            outpath = os.path.join(output, filename)
        if (flatten == False):
            if (file[1] != ''):
                outpath = os.path.join(outpath, file[1], filename + '.' + outExtenstion)
            else:
                outpath = os.path.join(outpath, filename + '.' + outExtenstion)
        else:
            outpath = os.path.join(outpath, filename + '.' + outExtenstion)
        cmd = cmd.replace('OUT_FILE', outpath)
        commands.append(cmd)

def parseCommandParameters(cmd, file, tune, quality, videoFilter):
    metadata = getMetadata(file[0])
    if ('IN_FILE' in cmd):
        cmd = cmd.replace('IN_FILE', file[0])
    else:
        print('IN_FILE not found in ffmpegCmd')
    if ('FF_TUNE' in cmd):
        cmd = cmd.replace('FF_TUNE', tune)
    if ('FF_QUALITY' in cmd):
        cmd = cmd.replace('FF_QUALITY', quality)
    if ('FF_VFILTERS' in cmd):
        cmd = cmd.replace('FF_VFILTERS', videoFilter)
    if ('MAPPINGS' in cmd):
        cmd = cmd.replace('MAPPINGS', mappingString(metadata['format']['nb_streams']))
    if ('ATMOS' in cmd):
        for stream in metadata['streams']:
            if (stream['codec_name'] == 'truehd'):
                cmd = cmd.replace('ATMOS', '-max_muxing_queue_size 1000')
        if ('ATMOS' in cmd):
            cmd = cmd.replace('ATMOS', '')
    return cmd

def mappingString(count):
    string = ""
    for i in range(0, count):
        string += " -map 0:" + str(i)
    return string

def getMetadata(file):
    results = osCommand(ffprobeCmd + '\"' + file + '\"')
    if (sys.version_info > (3,0)):
        jsonObj = json.loads(results.decode('utf-8'))
    else:
        jsonObj = json.loads(results)
    return jsonObj

def osCommand(bashCommand):
    if (sys.platform == 'darwin'):
        process = subprocess.Popen(bashCommand, stdout=subprocess.PIPE, shell=True)
    else:
        process = subprocess.Popen(bashCommand, stdout=subprocess.PIPE) 
    output, error = process.communicate()
    return output

def getFiles(argv):
    for item in argv:
        if (item[-2:] == 'py'):
            continue
        else:
            # if file -> add
            if (os.path.isfile(item)):
                found = parseFile(item)
                files.append(found)
            # if directory -> parse
            elif (os.path.isdir(item)):
                found = parseDirectory(item)
                for file in found:
                    files.append(file)
            else:
                print("invalid input: " + item)

def parseFile(file):
    item = []
    for ext in vidExtensions:
        if (os.path.splitext(file)[1][1:] == ext):
            item.append(file)
            item.append('')
            break
    return item

def parseDirectory(directory):
    found = []
    for root, dirs, files in os.walk(directory):
        for filename in files:
            for ext in vidExtensions:
                if (os.path.splitext(filename)[1][1:] == ext):
                    item = []
                    filepath = os.path.join(root, filename)
                    subpath = getSubFolder(directory, filepath, filename)
                    item.append(filepath)
                    item.append(subpath)
                    found.append(item)
                    break
    return found

def checkExcludes(files, excludes):
    for path in excludes:
        for file in files:
            if (file[0].find(path) != -1):
                files.remove(file)

def regexMatch(files, regex):
    matched = []
    for file in files:
        filename = os.path.basename(file[0])
        result = re.search(regex, filename, re.I)
        if result:
            matched.append(file)
    return matched

def getSubFolder(dirpath, filepath, file):
    subpath = filepath
    subpath = subpath.replace(dirpath, '', 1)
    subpath = subpath[::-1].replace(file[::-1], '', 1)[::-1]
    if (len(subpath) <= 2):
        subpath = ''
    else:
        subpath = subpath[1:-1]
    return subpath

def runCommands():
    '''
    Execute all generated commands
    '''
    for command in commands:
        outpath = os.path.dirname(shlex.split(command)[-1])
        if (os.path.exists(outpath) == False):
            os.mkdir(outpath)
        osCommand(command)
        
def main(argv):
    inputs = []
    output = ""
    excludes = []
    tune = 'film'
    quality = '20'
    videoFilter = ""
    regex = ""
    directory = False
    executeCmd = True
    flatten = False

    try:
        opts, args = getopt.getopt(argv, "hdgsi:o:e:t:f:q:v:", ["help","directory","generate-only","flatten","input","output","exclude","tune","filter","quality","video-filter"])
    except getopt.GetoptError as err:
        print(str(err))
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-i", "--input"):
            inputs.append(a)
        elif o in ("-o", "--output"):
            if (os.path.isdir(a)):
                output = a
            else:
                print("Output is not a directory")
                sys.exit(2)
        elif o in ("-e", "--exclude"):
            excludes.append(a)
        elif o in ("-g", "--generate-only"):
            executeCmd = False
        elif o in ("-f", "--filter"):
            regex = a
        elif o in ("-s", "--flatten"):
            flatten = True
        elif o in ("-d", "--directory"):
            directory = True
            flatten = True
        elif o in ("-t", "--tune"):
            tune = a
        elif o in ("-q", "--quality"):
            quality = a
        elif o in ("-v", "--video-filter"):
            videoFilter = '-vf ' + a
        else:
            assert False, "unhandled option"

    if (inputs == []):
        print("No inputs found")
        usage()
        sys.exit(2)

    if (output == ""):
        print("No output path found")
        usage()
        sys.exit(2)

    if (tune == ""):
        tune == 'film'

    getFiles(inputs)
    if (len(files) == 0):
        print('No valid inputs found')
        usage()
        sys.exit(2)

    if (regex != ""):
        if (len(excludes) != 0):
            checkExcludes(files, excludes)
        matched = regexMatch(files, regex)
        del files[:]
        for i in matched:
            files.append(i)
    
    generateCommands(files, output, directory, flatten, tune, quality, videoFilter)
    
    if (executeCmd):
        runCommands()
    else:
        for command in commands:
            print(command)

def usage():
    '''
    Help parameters.
    '''
    usage = """
    -h    What you're reading

    -d    Place each file in a separate directory. Will also flatten
    -g    Generate commands only. Do not execute
    -s    Flatten found folder to single output directory
    -t    Specify x264 tuning parameter. Default = film
    -q    Specify quality to use for CRF value (0-53). Default = 20
    -v    Specify a simple video filter

    -i    Input file or folder (required)
    -o    Output folder path (required)
    -e    Exclude a folder from search
    -f    Regex select files from folder. Perl style. ie "(?:test)"
    """
    print(usage)

if __name__ == '__main__':
    main(sys.argv[1:])
