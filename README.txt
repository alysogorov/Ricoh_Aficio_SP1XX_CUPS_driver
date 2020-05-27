------------------------------
﻿Linux Driver for RICOH aficio sp100 series
and can work possibly for SP2XX(not 
tested)

------------------------------
Tested on RICOH aficio sp111(Ubuntu 14.04).
It was inspired by madlynx driver - https://github.com/madlynx/ricoh-sp100

------------------------------
External software needed : 
  1.GhostScript (apt-get install ghostscript)
  2.pbmtojbg (apt-get install jbigkit)
  3.Python 2.7!!! 
to check requirements for installed software- run the file:
  check-requirements

------------------------------
Driver is able:
  1.Print at resolution : tested at 600dpi(seem could work at 1200 dpi also, but 
  not tested)

  2.Print A4,A5,A6, Letter paper size(tested)

  3.Print in Duplex Mode (flip on long edge)
  ATTENTION!!! In the current version, driver prints duplex with next simplest 
  strategy:
    - prints odd pages 1,3,5,7...
    - then printer stops and waits paper flipping, you must PROPERLY flip paper, 
      and press feed button on printer 
    - then it prints pages 2,4,6,8...
  This strategy is just simulation of "print odd,print even pages" method.
  This strategy differs from strategy of windows driver!!! Take care! 
  Pages flipping is different!

  4.Features as: printing in direct, reverse page order, printing odd/even
  pages provides CUPS itself, so it must work automatically 

------------------------
	 DISCLAIMER  !!!	
	ability to print few copies removed in current version, because of primitive command 
	line encoder of the driver invocation. CUPS calls the driver giving him few parameters, 
	but order of parameters, names, presence, format.. are not well known by author. 
	if some error in interpretation of params occures, driver could do things, we do not expect.
	There was such a trouble with "number_of_copies" parameter , which looks in some invocations 
	as forth number in command line, but sometimes forth param was something else, and driver 
	worked wrong. So, to not spend a time for it, i just ignore number of copies. so , to print 
	few copies, you've to print each of them manually, one by one.

------------------------
	DEBUG MODE:

In debug mode driver can:
  1.write rich dump of its activity to arbitrary file

  2.write outcoming stream not to stdout, but to arbitrary file for analysis(suitable if filter is 
used from CUPS).

############################
Driver usage:

  1. I'm using small bash stub script which calls the driver - <ricoh-sp1xx>
  READ REMARK BELOW

  driver itself is <ricoh-sp1xx-drv.py>
  you must create some dir, for example in your user folder. 
  And put real driver there, then correct path to driver in the stub ricoh-sp1xx, 
  now stub calls real driver from your dir.

  2. put stub script <ricoh-sp1xx> into directory - /usr/lib/cups/filter
  and give him root ownership and rights to be executable by <root> user.

  so CUPS will call stub from his filters directory.

  3. add printer to CUPS using http interface at adress:
  http://localhost:631/, USING GIVEN .ppd file, which has 
  reference to <ricoh-sp1xx> inside. 

  3. Turn your printer on.
  4. for testing try to print small text file or CUPS test page.

  5. If printer is in idle mode, it must "click" at beginning of printing.
  It shows that host has sent a file to the printer, and filter has not failed. 
  If there is no click, it could be "filter failed" error(probably because of access rights).

  6. If there is no printing, check in CUPS http interface which report cups gives
  for the printer. if print job failed - remove it from the list of active jobs.

REMARK:
  I use stub script for easy developement only. If you want to avoid stub, just 
  rename the driver to the stub name and put the driver itself into /usr/lib/cups/filter, 
  and give him the same rights as for the stub. 


################################
HOW TO TEST THE DRIVER WITHOUT CUPS(or manually try to print something).
################################

  1. To create RICOH printer binary file(a file which printer could print) from some
  text file: enter the string in terminal(here you need installed <enscript> programm):

  enscript --media=A4 -o - TEST_FILE.txt |python ricoh-sp1xx-drv.py PageSize=A4  > XXX.OUT

  here <enscript> creates postscript file of A4 size from TEST_FILE.txt(or some 
  your text file, and sends it to stdout), driver gets data from stdin and sends 
  resulting file to your XXX.OUT file(filenames are arbitrary)

sentence : 
	python ricoh-sp1xx-drv.py PageSize=A4
 
is an invocation of the driver. 
common driver invocation string is - python ricoh-sp1xx-drv.py [paramList]

paramList is a sequence of parameters, given below(not all of given parameters are interpreted by driver)

page size:
		"PageSize=A4" (default, if not PageSize is given, A4 will be chosen)
		"PageSize=A5"
		"PageSize=A6"
		"PageSize=Letter"
		"PageSize=Legal"
		"PageSize=B5"
		"PageSize=B6"

resolution:
		"Resolution=600dpi" (default value)
		"Resolution=1200dpi"

input slot(driver ignores it):
		"InputSlot=Auto"(default, driver still won't interpret any other kind of input slot)

media_type(ignored):
		"MediaType=PLAINRECYCLE" (default)
		"MediaType=PAPER"
		"MediaType=THIN"
		"MediaType=THICK1"
		"MediaType=RECYCLE"

output order(ignored):		
		"OutputOrder=Reverse" 

page set:		
		"page-set=even"
		"page-set=odd"

duplex:
		"Duplex=DuplexNoTumble"
		"Duplex=DuplexTumble"

		an order of options is not fixed, driver just searches, from the beginning of the option string, 
		a substring which he can understand as known option. options must look exactly as I write, 
		without blanks(f.e. is is wrong "PageSize =A5")

		example of a correct driver call 
			python ricoh-sp1xx-drv.py PageSize=A5  MediaType=THIN Resolution=1200dpi

	
	The driver creates a file, which can be sent to a printer.
	The output file has PJL format(native for this printer).
	see link - http://h10032.www1.hp.com/ctg/Manual/bpl13208

  2. The output file can be explored with some binary editor(kinda GHex)
  or be sent to printer:
   sudo cat XXX.OUT >/dev/usb/lp0  

----------------------
If there is something wrong, pls open an issue.
Happy printing
alys.



	 
