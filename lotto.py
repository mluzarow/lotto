from bs4 import BeautifulSoup # For making the soup
import urllib2 # For comms
import turtle # For drawing
import os # Dealing with the OS
import sys # Exit
import logging # Error logging
import re # Minor text parsing
from colorama import init
from colorama import Fore, Back, Style

#region Defines
VERSION_MAJOR = 0
VERSION_MINOR = 1
VERSION_SMALL = 0

STATES = list ()

WEB_PATH = "http://www.lottonumbers.com/%s-results-%d.asp"

APP_DATA_FOLDER = "Lotto Data"
APP_DATA_MASTER = "Master"
#endregion Defines

# Print help text
def printHelp (): 
    print "Arguments:"
    print "      --ss      Show all Downloaded sets."
    print "      --ls      Show all data in all sets."
    print "      --ds      Download more data sets."
    print "      --ff      Find Frequency of numbers in sets."
    print "      --fa      Find average of numbers in sets."
    print "      --fw      Find coupling data about numbers in sets."
    print "-h, --help      Show this help message."
    print "-q, --quit      Quit the program.\n\n"

#region Classes
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

   def getLargestNumber (self):
        # Return None if numbers have not been filled yet
        if len (self.numbers) <= 0:
            return (None)

        bNum = 0
        for num in self.numbers:
            if num > bNum:
                bNum = num

        return (bNum)

   def getSmallestNumber (self):
        # Return None if numbers have not been filled yet
        if len (self.numbers) <= 0:
            return (None)

        sNum = 100
        for num in self.numbers:
            if num < sNum:
                sNum = num

        return (sNum)
# Class for storing data on specific numbers draw on a day
class LottoNumber (object):
    def __init__ (self, date=None, month=None, numbers=None, extra=None):
        self.date = date
        self.month = month
        self.numbers = numbers
        self.extra = extra
#endregion Classes

#region Analysis
#####################################################################################################################
## Makes a dictionary of all valid lotto numbers paired with their frequency of occurance.                         ##
##                                                                                                                 ##
## -> List lotto : The list of all LottoSet classes from the save file and from page requests this session.        ##
## -> Bool extra : Flag for including extra shot numbers in the analysis. Default False.                           ##
##                                                                                                                 ##
## <- Dict dic : Dictionary of lotto numbers and their frequency of occurance.                                     ##
#####################################################################################################################
def findNumberFrequency (lotto, extra=False):
    dic = dict ()

    for set in lotto:
        for nums in set.numbers:
            for num in nums.numbers:
                if dic.has_key (num):
                    dic[num] += 1
                else:
                    dic[num] = 1

    return (dic)

#####################################################################################################################
## Prints number frequencies in a small horizontal list.                                                           ##
##                                                                                                                 ##
## -> Dict dic : Dictionary of lotto numbers and their frequency of occurance.                                     ##
##                                                                                                                 ##
## <- None                                                                                                         ##
#####################################################################################################################
def printNumberFrequency (dic):
    print "Displaying frequency of numbers in the current data sets.\n"
    l = list ()
    i = 0
    t = list ()

    for (key, value) in dic.iteritems (): 
        t.append ("[%2.d : %2.d]" % (key, value))
        i += 1

        if i == 10:
            l.append (t)
            t = list ()
            i = 0

    size = len (t)

    # Fill in the rest of the spots with none
    for i in range (0, 10 - size):
        t.append (None)

    l.append (t)

    size = len (l)
    for j in range (0, 10):
        for i in range (0, size):
            if l[i][j] == None:
                print "",
            else:
                print l[i][j] + " ",
        print "\n"

#####################################################################################################################
## Makes a dictionary of all lotto dates paired with the average value of that date.                               ##
##                                                                                                                 ##
## -> List lotto : The list of all LottoSet classes from the save file and from page requests this session.        ##
##                                                                                                                 ##
## <- Dict dic : Dictionary of lotto dates and their number averages.                                              ##
#####################################################################################################################
def findAverageValues (lotto):
    dic = dict ()

    for set in lotto:
        for nums in set.numbers:
            total = 0
            for num in nums.numbers:
                total += num

            total /= 6

            s = set.state + " " + nums.month + " " + str (nums.date) + " " + str (set.year)
            dic[s] = total

    return (dic)

#####################################################################################################################
## Makes a large list regarding how different numbers are linked together.                                         ##
##                                                                                                                 ##
## -> List lotto : The list of all LottoSet classes from the save file and from page requests this session.        ##
##                                                                                                                 ##
## <- Dict dic : Dictionary of number pairs and their frequency of occurance.                                      ##
#####################################################################################################################
def findWebbing (lotto):
    dic = dict ()

    maxNumber = 53 # Biggest possible number
    for n1 in range (1, maxNumber):
        for n2 in range (n1 + 1, maxNumber):
            dic[(n1, n2)] = 0

    for set in lotto:
        for nums in set.numbers:
            for num in nums.numbers:

                ## For each number, check it against every other number in the numbers
                for checknum in nums.numbers:
                    # Make sure tuple is (low val, high val)
                    comp = sorted ([num, checknum])
                    tup = (comp[0], comp[1])

                    # Add one to tuple freq
                    if dic.has_key (tup):
                        dic[tup] += 1

    return (dic)

#####################################################################################################################
## Prints a long list of the number pair and it's frequency of occurance.  List is split in order to fit into      ##
##   the Windows console buffer.  ==More== displays on the screen when the buffer is full.  Pressing any button    ##
##   will continue printing and freely remove past values from the buffer.                                         ##
##                                                                                                                 ##
## -> Dict dic : Dictionary of number pairs and their frequency of occurance.                                      ##
##                                                                                                                 ##
## <- None                                                                                                         ##
#####################################################################################################################
def printWebbing (dic):
    iter = 0
    l = list ()
    t = list ()
    MAX_VAL = 270

    maxNumber = 53 # Biggest possible number
    for n1 in range (1, maxNumber):
        for n2 in range (n1 + 1, maxNumber):
            if dic.has_key ((n1, n2)):
                t.append ("(%2.d - %2.d) : %2.d" % (n1, n2, dic[(n1, n2)]))
                iter += 1
            
            # If iter is >= MAX_VAL, a new column should be started
            if iter >= MAX_VAL:
                # If column is not full, pad with Nones
                if len(t) < MAX_VAL:
                    for i in range (MAX_VAL - len(t), MAX_VAL):
                        t.append (None)
                l.append (t)
                t = list ()
                iter = 0
    # Make sure the last non-filled column is appended to l and filled
    if len(t) < MAX_VAL:
        for i in range (MAX_VAL - len(t), MAX_VAL):
            t.append (None)
        l.append (t)

    # Print out columns
    for i in range (0, MAX_VAL):
        for j in range (0, len (l)):
            if l[j][i] == None:
                print "               ",
            else:
                print l[j][i] + " ",
        #print ""
        # More at halfway point
        if i == MAX_VAL / 2:
            print "===================================== More ====================================="
            while (1):
                # Ask for the input and throw it away
                raw_input ()
                break
    print "\n"

#####################################################################################################################
## Uses findWeb data in order to draw relationships on a Turtle canvas.                                            ##
##                                                                                                                 ##
## -> Dict dic : Dictionary of number pairs and their frequency of occurance.                                      ##
##                                                                                                                 ##
## <- None                                                                                                         ##
#####################################################################################################################
def drawWebbing (dic):
    t = initTurtle (400, 400)
    xDiv = 200 / 10
    yDiv = 200 / 5

    x = 200
    y = 200
    n = 1
    while (y < 200):
        while (x < 200):
            t.penup ()
            t.setposition (x, y)
            t.pendown ()
            t.write (str (n), ("Arial", 12, "normal"))
            n += 1
            x += xDiv
        x = 0
        y += yDiv


    turtle.done ()


#endregion Analysis

#region File IO
#####################################################################################################################
## Check that save directory and master file exits.  If not, make them.                                            ##
##                                                                                                                 ##
## -> None                                                                                                         ##
##                                                                                                                 ##
## <- Bool : If master file exists, return True.                                                                   ##
##    Bool : If master file does not exist, return False                                                           ##
#####################################################################################################################
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

#####################################################################################################################
## Read data in the master file into LottoSets and place into mew lotto list.                                      ##
##                                                                                                                 ##
## -> None                                                                                                         ##
##                                                                                                                 ##
## <- List lotto : The list of all LottoSet classes from this save file.                                           ##
##    NoneType : If master has tag "1234", returns None.                                                           ##
#####################################################################################################################
def readMaster ():
    flc = True
    lotto = list ()
    line = "\n"

    with open (APP_DATA_FOLDER + "/" + APP_DATA_MASTER, 'r') as f:
        while line != "":
            set = LottoSet ()

            set.numbers = list ()

            # Read header
            if line == "\n":
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
            line = f.readline ()

    return (lotto)

#####################################################################################################################
## Overwrite the master file with all data currently in the lotto list.                                            ##
##                                                                                                                 ##
## -> List lotto : The list of all LottoSet classes from the save file and from page requests this session.        ##
##                                                                                                                 ##
## <- None                                                                                                         ##
#####################################################################################################################
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
#endregion File IO

#region Web
#####################################################################################################################
## Read spruced soup and place data into LottoSets, which are added to the lotto list.                             ##
##                                                                                                                 ##
## -> BeautifulSoup parsedHTML : Spruced soup.                                                                     ##
## -> List lotto : The list of all LottoSet classes from the save file and for future data from this page.         ##  
## -> LottoSet set : A LottoSet set of lotto data that the numbers will go into.                                   ##
##                                                                                                                 ##
## <- List lotto: The updated lotto list.                                                                          ##
#####################################################################################################################
def parsePageData (parsedHTML, lotto, lottoSet):
    try:
        # Find all sets of lotto results
        data = parsedHTML.find_all ("div", "results")
        
        # Find all lotto result headers
        # NTS I don't understand why Beautiful Soup cannot find tags with links in them; it's the only thing
        #   it seems to have trouble with.  Using regex instead.
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

            if len (num.numbers) > 6:
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

#####################################################################################################################
## Gets the spruced up page data from the given link, sends to parsePageData.                                      ##
##                                                                                                                 ##
## -> String url : The URL that will be followed.                                                                  ##
## -> List lotto : The list of all LottoSet classes from the save file and for future data from this page.         ##  
## -> LottoSet set : A LottoSet set of lotto data that the numbers will go into.                                   ##
##                                                                                                                 ##
## <- List : The updated lotto list.                                                                               ##
#####################################################################################################################
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
#endregion Web

#region Console Control
#region DS
#####################################################################################################################
## Asks the user which of the state's valid years they would like to download lotto data from.                     ##
##                                                                                                                 ##
## -> LottoSource ls : Data regarding the chosen state (name, link, year list).                                    ##
##                                                                                                                 ##
## <- Tuple (String WEB_PATH, : Constructed string link for connecting to the requested page.                      ##
##           LottoSet) : Lotto set data to be sent to be filled with number data                                   ##
#####################################################################################################################
def dsGetYear (ls):
    numYears = len (ls.Years)
    print "The following arae all the valid years with lotta data for the state [%s]. Select a year from the list by entering the number to the left of the entry.  You can also select %d in order to download all available data.\n" % (ls.State, numYears)

    i = 0
    for year in ls.Years:
        print "[%d] %d" % (i, year)
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

        return ((WEB_PATH % (ls.Code, ls.Years[int (arg)]), LottoSet (ls.State, ls.Years[int (arg)])))

        #lotto = getPageData (WEB_PATH % (ls.Code, ls.Years[int (arg)]), lotto, LottoSet (ls.State, ls.Years[int (arg)]))

#####################################################################################################################
## Asks the user which of state from the STATES list they would like to download lotto data for.                   ##
##                                                                                                                 ##
## -> None                                                                                                         ##
##                                                                                                                 ##
## <- Tuple  (from dsGetYear)                                                                                      ##
#####################################################################################################################
def dsGetState ():
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

        return (dsGetYear (STATES[int (arg)]))

#####################################################################################################################
## Asks the user if they wish the download data, getting input from getInput ().                                   ##
##                                                                                                                 ##
## -> None                                                                                                         ##
##                                                                                                                 ##
## <- Tuple  (from dsGetState, dsGetYear)                                                                          ##
#####################################################################################################################
def dsGetDownloadInfo ():
    print "\nDownload additional data sets? [y/n]"

    while (1):
        arg = getInput (True)

        # Check for Y or N
        if arg == "Y" or arg == "YES":
            return (dsGetState ())
        elif arg == "N" or arg == "NO":
            print "Not downloading...\n"
            return
        else:
            continue
#endregion DE

def listSets (lotto):
    for set in lotto:
        print "%s %d" % (set.state, set.year)
        for nums in set.numbers:
            print nums.month + " " + str (nums.date) + " : " + str (nums.numbers) + " E " + str (nums.extra)

def showSets (lotto):
    i = 1
    for set in lotto:
        print "[%d] %s %d" % (i, set.state, set.year)
        i += 1

    print ""

#####################################################################################################################
## Gets data from the user via the console.                                                                        ##
##                                                                                                                 ##
## -> Bool upperize : Flag for changing the input text to upper case before returning.  Default to False.          ##
##                                                                                                                 ##
## <- String args[0] : The input data from the user.                                                               ##
##    NoneType : If argument is -h or --help, returns None.                                                        ##
#####################################################################################################################
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
#####################################################################################################################
## Initialize Turtle for turtle drawing                                                                            ##
##                                                                                                                 ##
## -> Int x : The x-ax-s size of the graphics window / canvas.                                                     ##
## -> Int y : The y-axis size of the graphics window / canvas.                                                     ##
##                                                                                                                 ##
## <- Turtle t : Graphics object storing graphics settings.                                                        ##
#####################################################################################################################
def initTurtle (x, y):
    # Wake the turtle
    t = turtle.Turtle ()
    # Max turtle speed
    t.speed (0)
    turtle.setup (x, y, 0, 0)
    # Create turtle playground
    #t.screen.screensize (x, y)
    #turtle.setworldcoordinates(0, y, x, 0)
    # Hide turtle head
    t.hideturtle ()
    # Hide turtle animations
    t.tracer ()

    return (t)

#####################################################################################################################
## Initializes state informations regarding links to lottonumbers.com using global variable STATES.                ##
##                                                                                                                 ##
## -> None                                                                                                         ##
##                                                                                                                 ##
## <- None                                                                                                         ##
#####################################################################################################################
def initStates ():
    STATES.append (LottoSource ("Illinois", "illinois-lotto", [2015, 2014, 2013, 2012, 2011, 2010, 2009]))
    STATES.append (LottoSource ("New-York", "new-york-lotto", [2015, 2014, 2013, 2012, 2011, 2010, 2009, 2008, 2007,
                                                               2006, 2005, 2004, 2003, 2002, 2001, 2000, 1999, 1998,
                                                               1997, 1996, 1995, 1994, 1993, 1992, 1991, 1990, 1989,
                                                               1988, 1987, 1986, 1985, 1984, 1983, 1982, 1981, 1980,
                                                               1979, 1978]))
    STATES.append (LottoSource ("Texas", "lotto-texas", [2015, 2014, 2013, 2012, 2011, 2010, 2009, 2008, 2007, 2006,
                                                         2005, 2004, 2003, 2002, 2001, 2000, 1999, 1998, 1997, 1996,
                                                         1995, 1994, 1993, 1992]))
    STATES.append (LottoSource ("Florida", "florida-lotto", [2015, 2014, 2013, 2012, 2011, 2010, 2009, 2008, 2007,
                                                             2006, 2005, 2004, 2003, 2002, 2001, 2000, 1999, 1998,
                                                             1997, 1996, 1995, 1994, 1993, 1992, 1991, 1990, 1989,
                                                             1988]))

#####################################################################################################################
## Initializes important constants and makes sure the save file exists.                                            ##
##                                                                                                                 ##
## -> None                                                                                                         ##
##                                                                                                                 ##
## <- List lotto :  The list of all LottoSet classes from the save file.                                           ##
#####################################################################################################################
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

    return (lotto)
#endregion Initialization

# Main entry
if __name__ == "__main__":
    init (autoreset=True) # Colorama init

    # Print program version
    print "Lotto thing - V%d.%d.%d\n" % (VERSION_MAJOR, VERSION_MINOR, VERSION_SMALL)

    # Print the help menu
    printHelp ()
    # Initialize the States
    initStates ()
    # Read the saved data into memory and show user what exists
    lotto = initLotto ()
    

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
            # [--ls] List Sets
            elif arg == "--ls":
                listSets (lotto)
            elif arg == "--ss":
                showSets (lotto)
            # [--ds] Download Sets
            elif arg == "--ds":
                (path, set) = dsGetDownloadInfo ()
                lotto = getPageData (path, lotto, set)
                writeMaster (lotto)
            elif arg == "--ff":
                dic = findNumberFrequency (lotto)
                printNumberFrequency (dic)
            elif arg == "--fa":
                dic = findAverageValues (lotto)
                # NTS add better printing function later
                for (key, value) in dic.iteritems ():
                    print "%s : %d" % (key, value)
            elif arg == "--fw":
                dic = findWebbing (lotto)
                printWebbing (dic)
            elif arg == "--drawWeb":
                dic = findWebbing (lotto)
                drawWebbing (dic)
            else:
                continue

        except Exception, e:
            print e