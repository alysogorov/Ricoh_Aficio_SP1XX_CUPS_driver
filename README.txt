Driver written for ricoh aficio sp100 series
and can work possibly for SP2XX.
Tested on ricoh oficio sp111.

############################
Driver can -
1.Resolution is tested at 600dpi(seem could work at 1200 dpi also, but 
not tested)
2.print A4,A5,A6 papers
3.Features as: printing in direct, reverse page order, priniting odd/even
pages provides CUPS itself, so it works automatically 
4.write rich dump to arbitrary file for debugging
5.copy outcoming stream to some file for analysis(could be debug if filter is 
used from CUPS).
############################

How to use driver:
1. I'm using small bash stub script which calls driver - <ricoh-sp1xx>

driver itself is <ricoh-sp1xx-drv.py>
you must create some dir, for example in your user folder. 
And put real driver there, then correct path to driver in the stub ricoh-sp1xx, 
now stub calls real driver from your dir.

2. put stub <ricoh-sp1xx> into directory - /usr/lib/cups/filt
and give him root ownership and rights to be executable by <root> user.

so CUPS will call stub from his filters directory.

3. add printer to CUPS using http interface at adress:
http://localhost:631/, USING GIVEN .ppd file, which has 
reference to <ricoh-sp1xx> inside. 

3. Turn your printer on.
4. Try to print small text file to test or CUPS test page.

5. if printer is in idle mode, it must "click" at beginning of printing.
It shows that host have sent a file to priter, and filter not failed. If there 
is no click, it could be "filter failed" error(mostly because of access rights).

6. if there is no printing, check in CUPS http interface which report cups gives
for the printer. if print job failed - remove it from the list of active jobs.



#############################
How to test driver without cups:
################################
1. Create ricoh printer binary file from some text file:
enter the string in terminal:
 enscript --media=A4 -o - TEST_FILE.txt |python xxx.py PageSize=A4  > XXX.OUT
here enscript creates postscript file of A4 size from TEST_FILE.txt(or some 
your text file, and sends it to stdout), driver gets data from stdio and sends 
resulting file to your XXX.OUT

2. Output file can be explored in some binary editor(kinda GHex)
or be sent to printer:
 sudo cat XXX.OUT >/dev/usb/lp0  

happy printing
alys.



	 
