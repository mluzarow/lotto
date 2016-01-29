from bs4 import BeautifulSoup # For making the soup
import urllib2 # For comms
import turtle # For drawing
import os # Dealing with the OS
import sys # Exit
import logging # Error logging
import re # Minor text parsing

#region Defines
VERSION_MAJOR = 0
VERSION_MINOR = 1
VERSION_SMALL = 0

WEB_PATH = "http://www.lottonumbers.com/%s-lotto-results-%d.asp"
YEARS = dict ()
YEARS["illinois"] = [2009, 2010, 2011, 2012, 2013, 2014, 2015]


APP_DATA_FOLDER = "Lotto Data"
APP_DATA_MASTER = "Master"
#endregion Defines

#region Public vars

#endregion Public Vars

# Print help text
def printHelp ():
    print "Lotto thing - V%d.%d.%d\n" % (VERSION_MAJOR, VERSION_MINOR, VERSION_SMALL)
    print "\nUsage: [-h] lotto.py"
    print "Arguments:"
    print "      --ds      Download more data sets."
    print "-h, --help      Show this help message."
    print "-q, --quit      Quit the program.\n\n"

# Class for storing data on a set of lotto data
class LottoSet (object):
   def __init__ (self, state=None, year=None, numbers=None):
       self.state = state
       self.year = year
       self.numbers = numbers

# Class for storing data on specific numbers draw on a day
class LottoNumber (object):
    def __init__ (self, date=None, month=None, numbers=None, extra=None):
        self.date = date
        self.month = month
        self.numbers = numbers
        self.extra = extra

def checkDatafile ():
    # Check for the directory
    if not os.path.exists (APP_DATA_FOLDER):
        # Directory is not there, this is the first or clean run; make the directory
        os.makedirs (APP_DATA_FOLDER)

    # Check in directory for master file
    if not os.path.isfile (APP_DATA_FOLDER + "/" + APP_DATA_MASTER):
        # Master file is missing; create it
        with open (APP_DATA_FOLDER + "/" + APP_DATA_MASTER, 'w') as f:
            f.write ("1234") # Future writes will overwrite this data
        f.closed
        
        return (False)
    return (True)

# Read the master file, load data into memory for useage
def readMaster ():
    flc = True
    lotto = list ()

    with open (APP_DATA_FOLDER + "/" + APP_DATA_MASTER, 'r') as f:
        set = LottoSet ()

        set.numbers = list ()

        # Read header
        line = f.readline ()

        # Check the first line of the master for fresh file trigger
        if flc:
            flc = False
            if line == "1234":
                f.closed
                return (None)

        # Read header
        line = line.split (' ')
        set.state = line[0]
        set.year = int (line[1])

        line = f.readline ()

        # Iterate through numbers
        while line is not "\n":
            num = LottoNumber ()

            # Split the line into the date | month and numbers
            line = line.split (':')

            # Slipt top in date and month
            top = line[0].split ('|')

            # Place data into struct
            num.date = int (top[0].strip (' '))
            num.month = top[1].strip (' ')

            # Split numbers into seperate numbers
            bottom = line[1].split (';')

            # Place data into struct
            num.numbers =  [int (bottom[0]), int (bottom[1]), int (bottom[2]), int (bottom[3]), int (bottom[4]), int (bottom[5])]
            num.extra = int (bottom[6])
            
            # Add current numbers to set list
            set.numbers.append (num)

            # Read next line
            line = f.readline ()

    return (lotto)

# Append new data to current master
def writeMaster (lotto):
    # Split set names by newline; content is now "state year"
    sets = data[0].split ("\n")

    with open (APP_DATA_FOLDER + "/" + APP_DATA_MASTER, 'w') as f:
        # Iterate through the lotto sets
        for set in lotto:
            # Write header for set
            f.write (set.state + " " + str (set.year) + "\n")

            # Iterate though numbers
            for num in set.numbers:
                f.write (str (num.date) + "|" + num.month + ":")

                # Iterate through a single batch of numbers
                for subnum in num.numbers:
                    f.write (str (subnum) + ";")

                # Write the extra number
                f.write (str (num.extra) + "\n")

    f.closed

def parsePageData (parsedHTML):
    try:
        # Find all sets of lotto results
        data = parsedHTML.find_all ("div", "results")
        
        # Find all lotto result headers
        header_comp = re.compile (".*\-lotto\-result\-[0-9]+\-[0-9]+\-[0-9]+.asp")
        header = parsedHTML.find_all (href=header_comp)

        # Set up data dict
        dic = dict ()

        arrM = [] # Black array of arrays
        # Go through each set of lotto results
        for set in data:
            # Make blank array of 7 values (7 numbers each)
            arr = [0, 0, 0, 0, 0, 0, 0]

            # Find each value
            set_r = set.find_all ("div", "result")

            # Go through each value, parse it, add it to array
            i = 0
            for s in set_r:
                arr[i] = int (s.string)
                i += 1

            # Add set data to dict, continue to next set
            arrM.append (arr)

        i = 0
        for head in header:
            # Split word byt spaces
            head = head.text.split (' ')

            dic[head[1] + "." + head[2] + "." + head[3]] = arrM[i]
            i += 1

        return dic
    except Exception, e:
        logging.warning (str(e.code))

def getPageData (url):
    try:
        # Follow URL
        response = urllib2.urlopen (url)
        # GET HTML page data
        html = response.read ()
        # Spruce up the soup
        parsedHTML = BeautifulSoup (html, "lxml")

        return (parsePageData (parsedHTML))

    except urllib2.HTTPError, e: # HTTP Error
        logging.warning ("HTTPError = %s" % str(e.code))
        return (None)
    except urllib2.URLError, e: # URL Error
        logging.waring ("URLError = %s" % str(e.code))
        return (None)
    except Exception:
        logging.warning ("Something happened :<")
        return (None)

# Initialize Turtle turtle
def initTurtle (x, y):
    # Wake the turtle
    t = turtle.Turtle ()
    # Max turtle speed
    t.speed (0)
    t.setup (x, y)
    # Create turtle playground
    t.screen.screensize (x, y)
    # Hide turtle head
    t.hideturtle ()
    # Hide turtle animations
    t.tracer ()

    return (t)

# Main entry
if __name__ == "__main__":
    printHelp ()
    __DEBUG__ = True

    if not checkDatafile ():
        print "A valid master has not been found."
        print "Master file has been created.\n"

    # Check if master has data
    print "Master file found. Checking...\n"
    # Read master file
    sets = readMaster ()

    print "Master has the following data sets:"

        # Master has no data, do nothing
    if sets == None:
        print "No data sets found.\n"
                
    # Master has data, print it
    else:
        i = 1
        for set in sets:
            print "[%d] %s" % (i, set)
            i += 1

    # Flag init
    ds = False
    dsPickName = False
    ds_Pick_Date = False

    # watchdog
    while (1):
        # Catch weird errors by printing help text
        try:
            args = raw_input (">")
            args = args.split(' ')
            # Check if arguments are too few
            if len(args) == 0:
                continue
            # check for control arguments
            for arg in args:
                # [-h] | [--help]
                if arg == "-h" or arg == "--help":
                    printHelp ()
                    continue
                # [-q] | [--quit]
                elif arg == "-q" or arg == "--quit":
                    sys.exit (0)

                # [--ds]
                if arg == "--ds":
                    ds = True
                    print "Would you like to download more data sets?\n"
                else:
                    continue

            # ds flag is set for download for sets
            if ds == True:
                for arg in args:    
                    arg = arg.upper ()

                    # Begin acquisition
                    if arg == "Y" or arg == "YES":
                        ds - False
                        data = getPageData (WEB_PATH % ("illinois", 2015))
                        writeMaster (data, "liinois")
                    elif arg == "N" or arg == "NO":
                        ds = False
                        print "Not downloadng.\n"
                    else:
                        print "Valid arguments are either \"yes\" or \"no\"."
                    
                    break

        except Exception, e:
            print e