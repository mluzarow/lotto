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

STATES = list ()

WEB_PATH = "http://www.lottonumbers.com/%s-results-%d.asp"
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

class LottoSource (object):
    def __init__ (self, state, code, years):
        self.State = state
        self.Code = code
        self.Years = years

# Class for storing data on a set of lotto data
class LottoSet (object):
   def __init__ (self, state=None, year=None, numbers=None):
       self.state = state
       self.year = year
       self.numbers = numbers

   def listNumberbyFrequency (self):
        pass
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
        while line != '\n':
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
            
            # If there is no extra shot
            if num.numbers.count < 7:
                num.extra = None
            else:
                num.extra = int (bottom[6])
            
            # Add current numbers to set list
            set.numbers.append (num)

            # Read next line
            line = f.readline ()

        lotto.append (set)
    return (lotto)

# Append new data to current master
def writeMaster (lotto):
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
            f.write ('\n')
    f.closed

def parsePageData (parsedHTML, lotto, lottoSet):
    try:
        # Find all sets of lotto results
        data = parsedHTML.find_all ("div", "results")
        
        # Find all lotto result headers
        header_comp = re.compile (".*\-lotto\-result\-[0-9]+\-[0-9]+\-[0-9]+.asp")
        header = parsedHTML.find_all (href=header_comp)

        # Make a list for stroing all the lotto numbers
        lottoNumberList = list ()
        lottoSet.numbers = list ()

        # Go through each set of lotto results
        for set in data:
            num = LottoNumber ()
            num.numbers = list ()

            # Find each value
            set_r = set.find_all ("div", "result")

            # Go through each value, parse it, add it to list
            for s in set_r:
                num.numbers.append (int (s.string))

            # Move extra shot to extra slot and remove from numbers
            num.extra = num.numbers[6]
            num.numbers.remove (num.numbers[6])

            lottoNumberList.append (num)

        i = 0
        for head in header:
            # Split word byt spaces
            head = head.text.split (' ')

            # Iterate through all possible numeric superscripts and remove them
            for s in ["st", "nd", "rd", "th"]:
                head[1] = head[1].replace (s, "")

            # Add date to numbers
            lottoNumberList[i].date = int (head[1])
            # Add month to numbers
            lottoNumberList[i].month = head[2]

            # Add numbers to set
            lottoSet.numbers.append (lottoNumberList[i])

            i += 1
        
        # Add data set tp lotteSet
        lotto.append (lottoSet)

        return lotto
    except Exception, e:
        logging.warning (str(e.code))

def getPageData (url, lotto, set):
    try:
        # Follow URL
        response = urllib2.urlopen (url)
        # GET HTML page data
        html = response.read ()
        # Spruce up the soup
        parsedHTML = BeautifulSoup (html, "lxml")

        return (parsePageData (parsedHTML, lotto, set))

    except urllib2.HTTPError, e: # HTTP Error
        logging.warning ("HTTPError = %s" % str(e.code))
        return (None)
    except urllib2.URLError, e: # URL Error
        logging.waring ("URLError = %s" % str(e.code))
        return (None)
    except Exception, e:
        logging.warning ("Something happened: %s" % e)
        return (None)

#region Console Control
#region DS
def dsGetYear (ls, lotto):
    numYears = len (ls.Years)
    print "The following arae all the valid years with lotta data for the state [%s]. Select a year from the list by entering the number to the left of the entry.  You can also select %d in order to download all available data.\n" % (ls.State, numYears)

    i = 0
    for year in ls.Years:
        print "[%d %d" % (i, year)
        i += 1

    print "[%d] Download all\n" % numYears

    while (1):
        arg = getInput ()

        # If input is not a digit, try again
        if not arg.isdigit ():
            continue

        # If input is "download all"
        if arg == str (numYears):
            #download evertthing loop
            pass

        # Check if input is out of bounds
        if int (arg) >= numYears or int (arg) < 0:
            continue

        lotto = getPageData (WEB_PATH % (ls.Code, ls.Years[int (arg)]), lotto, LottoSet (ls.State, ls.Years[int (arg)]))

def dsGetState (lotto):
    numStates = len (STATES)
    print "The following are all the valid states with lotto data.  Select a state from the list by entering the number to the left of the entry.  You can also select %d in order to download all available data.\n" % numStates

    i = 0
    for state in STATES:
        print "[%d] %s" % (i, state.State)
        i += 1

    print "[%d] Download all\n" % i

    while (1):
        arg = getInput ()

        # If input is not a digit, try again
        if not arg.isdigit ():
            continue

        # If input is "download all"
        if arg == str (numStates):
            #download evertthing loop
            pass

        # Check if input is out of bounds
        if int (arg) >= numStates or int (arg) < 0:
            continue

        dsGetYear (STATES[int (arg)], lotto)

def dsGetDownloadInfo (lotto):
    print "\nDownload additional data sets? [y/n]"

    while (1):
        arg = getInput (True)

        # Check for Y or N
        if arg == "Y" or arg == "YES":
            dsGetState (lotto)
        elif arg == "N" or arg == "NO":
            print "Not downloading...\n"
            return
        else:
            continue
#endregion DE

def getInput (upperize = False):
    # Get user input and split it by ' '
    args = raw_input (">")
    args = args.split(' ')

    # If the args list is empty, return Mone
    if len(args) == 0:
        return (None)

    # [-h] | [--help]
    if args[0] == "-h" or args[0] == "--help":
        printHelp ()
        return (None)
    # [-q] | [--quit]
    elif args[0] == "-q" or args[0] == "quit":
        sys.exit (0)

    if upperize:
        args[0] = args[0].upper ()

    # Return the first phrase and throw out the rest
    return (args[0])
#endregion Console Control

#region Initialization
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

def initStates ():
    STATES.append (LottoSource ("Illinois", "illinois-lotto", [2015, 2014, 2013, 2012, 2011, 2010, 2009]))
    STATES.append (LottoSource ("New York", "new-york-lotto", [2015, 2014, 2013, 2012, 2011, 2010, 2009, 2008, 2007, 2006, 2005,
                                                         2004, 2003, 2002, 2001, 2000, 1999, 1998, 1997, 1996, 1995, 1994,
                                                         1993, 1992, 1991, 1990, 1989, 1988, 1987, 1986, 1985, 1984, 1983,
                                                         1982, 1981, 1980, 1979, 1978]))
    STATES.append (LottoSource ("Texas", "lotto-texas", [2015, 2014, 2013, 2012, 2011, 2010, 2009, 2008, 2007, 2006, 2005, 
                                                      2004, 2003, 2002, 2001, 2000, 1999, 1998, 1997, 1996, 1995, 1994, 
                                                      1993, 1992]))
    STATES.append (LottoSource ("Florida", "florida-lotto", [2015, 2014, 2013, 2012, 2011, 2010, 2009, 2008, 2007, 2006, 2005,
                                                        2004, 2003, 2002, 2001, 2000, 1999, 1998, 1997, 1996, 1995, 1994,
                                                        1993, 1992, 1991, 1990, 1989, 1988]))

def initLotto ():
    # Check that the data file exists
    if not checkDatafile ():
        print "A valid master has not been found."
        print "Master file has been created.\n"

    # Check if master has data
    print "Master file found. Checking...\n"

    # Read master file
    lotto = readMaster ()

    print "Master has the following data sets:"

    # Master has no data, do nothing
    if lotto == None:
        lotto = list ()
        print "No data sets found.\n"
    # Master has data, print it
    else:
        i = 1
        for set in lotto:
            print "[%d] %s %d" % (i, set.state, set.year)
            i += 1
#endregion Initialization

# Main entry
if __name__ == "__main__":
    printHelp ()
    initStates ()
    # Read the saved data into memory and show user what exists
    lotto = initLotto ()

    # Flag init
    ds = False
    dsPickName = False
    ds_Pick_Date = False
    ds_Choose = False

    # watchdog
    while (1):
        # Catch weird errors by printing help text
        try:
            # Get the user's input
            arg = getInput ()

            # Check which flag the user has entered.
            # [-h] | [--help]
            if arg == "-h" or arg == "--help":
                printHelp ()
                continue
            # [-q] | [--quit]
            elif arg == "-q" or arg == "quit":
                sys.exit (0)
            # [--ds]
            elif arg == "--ds":
                dsGetDownloadInfo (lotto)
            else:
                continue

            # ds flag is set for download for sets
            if ds == True:
                for arg in args:    
                    arg = arg.upper ()

                    # Begin acquisition
                    if arg == "Y" or arg == "YES":
                        ds == False
                        ds_Choose = True

                        # List all available states
                        i = 0
                        for state in STATES:
                            print "[%d] %s" % (i, state.State)
                            i += 1

                        # Add option to download all states
                        print "[%d] Download all\n" % i

                        # Choose the state
                        state = dsChooseState (args[0])
                       # ds_Choose = True
                        #lotto = getPageData (WEB_PATH % ("illinois", 2012), lotto, LottoSet ("IL", 2012))
                        #writeMaster (lotto)
                    elif arg == "N" or arg == "NO":
                        ds = False
                        print "Not downloadng.\n"
                    
                    break
            # Flag is set for Choose download state (or download all)
            if ds_Choose == True:
                for arg in args:
                    arg = arg.upper ()
                    
                    i = 0
                    for state in STATES:
                        print "[%d] %s" % (i, state.State)
                        i += 1

                    print "[%d] Download All" % i

                    if arg == "1":
                        ds_Choose_Year = True
                        ds_Choose = False
                    elif arg == "2" or "NY":
                        ds_Choose_Year = True
                        ds_Choose = False
                    else:
                        print "Valid arguments are either item number."

        except Exception, e:
            print e