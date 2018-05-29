import os
import sys
import subprocess
import json
import getopt
import shlex

ffmpegPath = 'ffmpeg'
ffprobePath = 'ffprobe'
ffprobeCmd = ffprobePath + ' -loglevel quiet -print_format json -show_format -show_streams -show_error -i '
ffmpegCmd = ffmpegPath + ' -i "IN_FILE" -c:v libx264 -crf 20 -tune FF_TUNE -c:a copy -scodec copy MAPPINGS "OUT_FILE"'

vidExtensions = ['mp4','mkv','mov','mxf','m4v','avi','wmv']
outExtenstion = 'mkv'

files = []
commands = []

def generateCommands(files, output, directory, flatten, tune):
    '''
    Generate full ffmpeg command to be executed. Will be run using external binary
    '''
    for file in files:
        outpath = output
        cmd = ffmpegCmd
        cmd = cmd.replace('IN_FILE', file[0])
        cmd = cmd.replace('FF_TUNE', tune)
        cmd = cmd.replace('MAPPINGS', mappingString(getMetadata(file[0])))
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
    return jsonObj['format']['nb_streams']

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
        if (file[-3:] == ext):
            item.append(file)
            item.append('')
            break
    return item

def parseDirectory(directory):
    found = []
    for root, dirs, files in os.walk(directory):
        for name in files:
            for ext in vidExtensions:
                if (name[-3:] == ext):
                    item = []
                    filepath = os.path.join(root, name)
                    subpath = getSubFolder(directory, filepath, name)
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
    directory = False
    executeCmd = True
    flatten = False

    try:
        opts, args = getopt.getopt(argv, "hdgfi:o:e:t:", ["help","directory","generate-only","flatten","input","output","exclude","tune"])
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
        elif o in ("-f", "--flatten"):
            flatten = True
        elif o in ("-d", "--directory"):
            directory = True
            flatten = True
        elif o in ("-t", "--tune"):
            print('tune in:' + a + ':')
            tune = a
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

    inputCount = getFiles(inputs)
    if (inputCount == 0):
        print('No valid inputs found')
        usage()
        sys.exit(2)

    if (len(excludes) != 0):
        checkExcludes(files, excludes)
    
    generateCommands(files, output, directory, flatten, tune)
    
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
    -f    Flatten found folder to single output directory
    -t    Specify x264 tuning parameter. Default = film

    -i    Input file or folder (required)
    -o    Output folder path (required)
    -e    Exclude a folder from search
    """
    print(usage)

if __name__ == '__main__':
    main(sys.argv[1:])
