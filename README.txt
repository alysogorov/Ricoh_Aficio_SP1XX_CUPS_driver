what printer driver can -
1.Resolution is still fixed at 600dpi
2.print A4,A5,A6 papers
3.write rich dump to arbitrary file
4.copy outcoming stream to some file for analysis(could be use to find problems,
if it is used by CUPSi

How to use driver:
I'm using small bash stub script which calls driver.


How to test driver:

################################
1. Create ricoh printer binary file from some text file:
enter the string in terminal:
 enscript --media=A4 -o - TEST_FILE.txt |python xxx.py PageSize=A4  > XXX.OUT
here enscript creates postscript file of A4 size from TEST_FILE.txt(or some 
your text file, and sends it to stdout), driver gets data from stdio and send 
resulting file to your XXX.OUT

2. Output file can be explored in some binary editor(kinda GHex)
or be sent to printer:
 sudo cat XXX.OUT >/dev/usb/lp0  

3. if something went wrong - 


happy printing
alys.



	 
