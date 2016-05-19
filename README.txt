Driver developed for ricoh aficio sp100 series
and can work possibly for SP2XX.
Tested on ricoh aficio sp111(Ubuntu 14.04).
It was inspired by madlynx driver - https://github.com/madlynx/ricoh-sp100

Needed external software - 
  1.GhostScript (apt-get install ghostscript)
  2.pbmtojbg (apt-get install jbigkit)
  3.Python 

to check requirements for installed software- run file:
  check-requirements

############################
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

  4.Features as: printing in direct, reverse page order, priniting odd/even
  pages provides CUPS itself, so it works automatically 

In debug mode driver can:
  1.write rich dump to arbitrary file

  2.write outcoming stream not to stdout but to some file for analysis(suitable if filter is 
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
  4. Try to print small text file to test or CUPS test page.

  5. If printer is in idle mode, it must "click" at beginning of printing.
  It shows that host have sent a file to priter, and filter not failed. If there 
  is no click, it could be "filter failed" error(mostly because of access rights).

  6. If there is no printing, check in CUPS http interface which report cups gives
  for the printer. if print job failed - remove it from the list of active jobs.

REMARK:
  I use stub script for easy developement only. If you need to avoid stub, just 
  rename the driver to the stub name and put into /usr/lib/cups/filter, and give 
  the same rights as for the stub

################################
How to test driver without cups:
################################
  1. Create ricoh printer binary file from some text file:
  enter the string in terminal(here you need installed <enscript> programm):

  enscript --media=A4 -o - TEST_FILE.txt |python ricoh-sp1xx-drv.py PageSize=A4  > XXX.OUT

  here <enscript> creates postscript file of A4 size from TEST_FILE.txt(or some 
  your text file, and sends it to stdout), driver gets data from stdin and sends 
  resulting file to your XXX.OUT

  2. The output file can be explored with some binary editor(kinda GHex)
  or be sent to printer:
   sudo cat XXX.OUT >/dev/usb/lp0  


If there is something wrong, pls open an issue.
Happy printing
alys.



	 
