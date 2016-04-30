#!/usr/bin/python
# -*- coding: utf-8 -*-
#####################################
#ALYS: Driver for Ricoh sp1xx printer(tested on ricoh 111)
#####################################
import sys
import os
import uuid
import time
import subprocess
#import utils
#####################################
#set default values
__pagesize="A4" #default page size
__resolution="600"
__copies = "1"
__mediasource="AUTO" #__mediasource="TRAY1"

#this modes are implemented in cups, user sets them in printing settings,
#the driver receives proper pages(all,odd,even) in proper order(direct,
# reversed) we ignore them n code
__outputOrder="DIRECT" #direct or reversed order
__printPages="ALL" #all, even, odd pages to be printed

##############################
__base = sys.path[0]+"/" #script dir
##############################
#######
#for debugging, if everyting is OK, set empty strings to this values
#here filenames are relative to dir of this driver, redirection of driver output
#hardcoded here to catch output if driver has been called via cups.
__out_fn ="driver.out" #will redirect output not to stdio, but to this file
__log_fn ="session.log"#will dump logs to this file

#####################################
__out = sys.stdout #select data output to stdout(cups filter send data there)
if __out_fn!="":
    __out = open(__base+__out_fn,"w")



##################################
#logging
__log_stream = None

if __log_fn!="":
    __log_stream = open(__base+__log_fn, "w") #open log file
    sys.stderr = __log_stream

def log(fs):
    if not __log_stream is None: __log_stream.write(fs+'\n')

def closeLog():
    if not __log_stream is None: __log_stream.close()

###################################
#get script parameters
def param(i):
    if i<len(sys.argv): return sys.argv[i]
    else: return "undefined"

log('Argument List:'+ str(sys.argv))

#__log_stream.close()
#exit(0)

__user = param(2)# user name
__title=param(3)# file name
__copies=param(4)#number of copies(just a number)
#__options=param(5)#
__date = time.strftime('%Y/%m/%d %H:%M:%S') #"this is date"
log("Current Date is "+__date)

#find string in a string array
def _find_(farr, fs):
    i=1;
    while i<len(farr):
      if farr[i]==fs: return True
      i=i+1
    return False

#find option
def find_option(fs):
    return _find_(sys.argv,fs)


#parse options to override defaults
if    (find_option("PageSize=A5")):     __pagesize="A5"
elif  (find_option("PageSize=A6")):     __pagesize="A6"
elif  (find_option("PageSize=Letter")): __pagesize="Letter"

log("PageSize="+__pagesize) #dump paper size for debugging

#check slot(paper?)...but my printer has only one slot - AUTO(from Windows driver caption)
#because some printers could have different slots, this option is essential for them
if find_option("InputSlot=Auto"): __mediasource = "AUTO"

if find_option("OutputOrder=Reverse"): _outputOrder="REVERSE"
  
if   find_option('page-set=even'): _printPages="EVEN"
elif find_option('page-set=odd'):  _printPages="ODD"

########
#options obtained for multipage printing(few pages on one paper sheet)
#still not process this modes
# 'number-up=16'
# 'number-up-layout=lrtb'
##########################

#terminal command
def term(fs):
    log("TERM:"+fs)
    lr = os.system(fs)
#  lret = lr&0xffff >> 8; #process return code
    lret = lr
    log("RETURN CODE="+str(lret));
    if lret!=0: 
      log("COMMAND ERROR:EXIT(1)")
      exit(1) #driver failed

########### create temporary dir ###############
#__uid = __base+"TEMP" #for debigging use fixed subfolder
__uid = __base+ str(uuid.uuid4())
term("mkdir "+__uid) #create temp dir
__temp_dir = __uid +"/"


#######################################
def out(fs): #send data to output file
    log(fs)
    __out.write(fs)
    
#send string to output file
def outLine(fs):
    log(fs)
    __out.write(fs+'\r\n') # \r\n is essential here! printer can read ms-dos strings only!!!
 
#emit "@pjl set" command
def pjlLine(fs):
    outLine("@PJL SET "+fs)

#######################
# i obtained that for A4 paper, windows driver gives 7016 pixels paper 
# width,while ghostscript could give 7017, hanging printer.
# so to avoid this error I cut dimenstions to recommended in 
# different papers.
# reference:
# http://www.a4papersize.org/a4-paper-size-in-pixels.php
# http://www.papersizes.org/a-sizes-in-pixels.htm
# seems both links give different pixel dimensions for same paper 
# at least this works good for all mentioned paper sizes for 600 dpi
# 1200 dpi still not tested
def metric_dimensions(fpaper, fres, fw,fh):
   if fpaper=="A4":
      if fres=="600": return 4961,7016
      if fres=="1200": return  9921, 14031
   elif fpaper=="Letter":
      if fres=="600": return 5100,6600
      if fres=="1200":return 10200,13200
   elif fpaper == "A5":
      if fres=="600": return 3502, 4958 #Pixels
      if fres=="1200": return 7004,9916 #Pixels 
   elif fpaper == "A6":
      if fres=="600": return 2480, 3508 #Pixels
      if fres=="1200": return  4961, 6992 #Pixels 
   else: return 4961,7016 #A4 * 600dpi

#cut dimensions to fit metric values
def cut_dimensions(fpaper, fres, fw,fh):
    lw,lh = metric_dimensions(fpaper,fres,fpaper,fres)
    if lw>fw: lw=fw
    if lh>fh: lh=fh
    return lw,lh

#ricoh ddst file must have proper header
def send_file_head():
    log ("sending file header")
    outLine("\x1b%-12345X@PJL") #magic bla-bla
    pjlLine("TIMESTAMP="+__date)
    pjlLine("FILENAME="+__title)
    pjlLine("COMPRESS=JBIG") #compression type, do not know if he can use another compression
    pjlLine("USERNAME="+__user)
    pjlLine("COVER=OFF")  #needed
    pjlLine("HOLD=OFF")  #needed 

#ricoh ddst file must have proper footer
def sendFileFoot():
    log ("sending file footer")
    outLine("@PJL EOJ") #end of job
    outLine("\x1b%-12345X")	#magic bla-bla, last string of the file MUST have!!! \r\n else printer stays in printing mode!!!

# append data of fsrc file to fdst file, buffered
def appendFile(fdst, fsrc, fbuffer_size=1024*16):
    fsrc.seek(0)    
    while True:
        ldata = fsrc.read(fbuffer_size)
        if not ldata: break
        fdst.write(ldata)

#Get width and height of PBM image from its file
# Each PBM image consists of the following:
#    A "magic number" for identifying the file type. A pbm image's magic number is the two characters "P4". 
#    Whitespace (blanks, TABs, CRs, LFs). 
#    The width in pixels of the image, formatted as ASCII characters in decimal. 
#    Whitespace. 
#    The height in pixels of the image, again in ASCII decimal. 
#    Newline or other single whitespace character.
def parsePbmSize(ffile):
    lf = open(ffile,"rb")
    lf.readline();   #log(">>>>"+lr) #magic P4
    lf.readline();   #log(">>>>"+lrr) #comment
    lrrr = lf.readline();  #log(">>>>"+lrrr) #width height
    ls = lrrr.split(" ")
    lf.close()
    #return 4961,7016    
    return int(ls[0]),int(ls[1])

# send wellformed PJL page to output stream
def addPage(fpage):
#lraster_size =`wc -c < $uid/raster.jbig`
    log("sending page:"+fpage)
    if not os.path.exists(fpage): return False

	# Converting page to JBIG format (parameters are very special for this printer!)
    lraster = __temp_dir+"raster.jbig"
#convert PBM page file to JBIG compressed file
#   term("pbmtojbg -p 72 -o 3 -m 0 -q < $page > $uid/raster.jbig")
#    term("pbmtojbg -p 72 -o 3 -m 0 -q "+fpage+" "+lraster)
    term("pbmtojbg -p 72 -o 3 -m 0 -q "+fpage+" "+lraster)
# Taking image size
#		jsize=`wc -c < $uid/raster.jbig`
#    term( "wc -c < "+lraster)

		# Taking image dimensions
#  read fn ft xs ys garb < <(identify $page | tr "x" " ")
#  log "Identified as ${xs}x${ys}"

    lw, lh = parsePbmSize(fpage) #get raster dimensions in pixels
    log("PAGE ORIGINAL DIMS="+str(lw)+"x"+str(lh))
    lw,lh = cut_dimensions(__pagesize,"600",lw, lh)
    #lwidth, lheight = "4961","7016"
    log("PAGE CROPPED DIMS="+str(lw)+"x"+str(lh))
  
    lbytes = os.stat(lraster).st_size #get raster size in bytes
    log("RASTER SIZE ="+str(lbytes));
    lfile = open(lraster, "rb");

    pjlLine("PAGESTATUS=START")
    pjlLine("COPIES="+__copies) #number of copies
    pjlLine("MEDIASOURCE="+__mediasource) #paper tray to feed
    pjlLine("MEDIATYPE=PLAINRECYCLE") #kind of paper
    pjlLine("PAPER="+__pagesize) #size of paper:A4,A5...
    pjlLine("PAPERWIDTH="+str(lw))   # x dimension in pixels
    pjlLine("PAPERLENGTH="+str(lh))  # y dimention in pixels
    pjlLine("RESOLUTION="+__resolution) #resolution (dpi)
    pjlLine("IMAGELEN="+str(lbytes)) #bytes in image
#append page raster
#    global __out
    appendFile(__out,lfile)
#    if not __copy_stream is None: append_file(__copy_stream,lfile)
#send page footer
    pjlLine("DOTCOUNT=777") # here we use fake dotcount
    pjlLine("PAGESTATUS=END")# end of page command
    return True
############def end send_page


#get driver data source
def getInput():
    return " -" 

#    log ("### create faked input from test file ###")  
#    lout = __temp_dir+"test.ps"
#    linput = " " #if input is empty - reads from stdio
#    term("enscript --media="+__pagesize+" -o "+ lout +" "+ linput)
 #  term("sam2p gerb.png EPS: "+__input) #convert from picture
 #  term("sam2p dog.jpg EPS: " + linput)
#    log ("### Faked input created ###")
#    return lout

########################################################
########################################################
########################################################

#PRINT ENTIRE FILE
#DO NOT USE THIS FUNCTION, IT IS FROM OLD VERSION,
#MUST BE REMADEN!!!
def doJob() :
  linput = getInput()
  log("########### convertion to PostScript done###########")

  __gs_ops = "-dQUIET -dBATCH -dNOPAUSE -dSAFER" #standard Ghost Script options from GS tutorial
  #__gs_ops = "-dQUIET -dBATCH -dSAFER" #standard Ghost Script options from GS tutorial

  #term("gs " + __gs_ops+" -sDEVICE=ps2write -sOutputFile=-" + " -r"+__resolution + __input
  #	+" | gs "+ __gs_ops+" -sDEVICE=pbmraw	-sOutputFile="+ __uid+"%03d-page.pbm"	+" -r"+__resolution	+" -"
  #)

  #convert incoming postscript to PBM...because seems we cannot convert PS -> JBIG directly
  #we can convert only PBM->JBIG(needed by printer)
  #term("gs "+ __gs_ops+" -sDEVICE=pbmraw -sOutputFile="+__temp_dir+"%03d-page.pbm"	+" -r"+__resolution +" "+ __input)
  term("gs "+ __gs_ops+" -sDEVICE=ps2write -sOutputFile="+__temp_dir+"%03d-page.ps"	+" -r"+__resolution +" "+ linput)
  sys.exit()


  #subprocess.call(["gs", __gs_ops,"-sDEVICE=pbmraw", "-sOutputFile="+__temp_dir+"%03d-page.pbm","-r"+__resolution,__input])
  p = subprocess.Popen(
    ["gs"
    , __gs_ops
    ,"-sDEVICE=pbmraw"
    ,"-sOutputFile="+__temp_dir+"%03d-page.pbm"
    ,"-r"+__resolution
    ,linput]
    , shell=False
    , stdin=subprocess.PIPE 
    , stdout = subprocess.PIPE
   ) 

  #term("gs "+ __gs_ops+" -sDEVICE=pbmraw -sOutputFile="+__temp_dir+"%03d-page.pbm"	+" -r"+__resolution +" "+ __input)
  #log("pages converted")
  #quit()

  #print pages
  #let we make output file - wellformed file to be sent to usb port
  #p.stdin.write("\n")

  send_file_head() # make header
  #p.communicate('\n')	

  page = 1; # scan pages images and send them to file, first page has index 1, not 0
  while True:
      log("waiting gs question")
  #    p.stdout.flush()
  #    if not p.poll(): break
      ls = p.stdout.readline();
  #    if not ls: break
      log(ls)
  #    time.sleep(1)
      if p.poll():
          p.stdin.write('\n')
      
      lpage = __temp_dir+'%03d'%(page) + "-page.pbm" #make page file name from index
      if not addPage(lpage): break
      #clean page file and temporary JBIG raster
  #    term("rm "+lfile)
  #    term("rm "+lrasterfile)
      page=page+1 # next page

  #### file generated, add footer ####
  sendFileFoot()
  __out.close()#close ouput file

  #clean up
  term("rm -rf "+ __uid)

  #cleanup 
  log("printing done")
################################

#cleanup
def driverCleanup():
#    if not __copy_stream is None: __copy_stream.close()
#    term("rm -rf "+ __uid) #delete temp folder
    if __out!=sys.stdout:__out.close()
    closeLog()

###############################################
###############################################
###############################################
#create page file name
def makePageFN(inx,fmask):
    return __temp_dir+'%03d'%(inx) + fmask #make page file name from index

#PRINT ENTIRE FILE in trivial fashion
#just convert all incoming data to pbm pages, and then create "ricoh file" page by page
#pros: simple and fast
#cons: - pbm pages are quite big, for A4(600dpi) it is about 4mb, so 100 pages will occupy 400 mb.
#but for small documents and plenty of memory it works good. 
def doJobTrivial():
    linput = getInput()
    #__gs_ops = "-dQUIET -dBATCH -dNOPAUSE -dSAFER -sPAPERSIZE="+__pagesize #standard Ghost Script options from GS tutorial
    lgs_ops = "-dQUIET -dBATCH -dNOPAUSE -dSAFER" #standard Ghost Script options from GS tutorial

    #convert incoming postscript to PBM...because seems we cannot convert PS -> JBIG directly
    #we can convert only PBM->JBIG(needed by printer)
    term("gs "+ lgs_ops+" -sDEVICE=pbmraw -sOutputFile="+__temp_dir+"%03d-page.pbm"	+" -r"+__resolution +" "+ linput)
  #  sys.exit()
    inx = 1; # iterate pages images and send them to file, first page has index 1, not 0
    lheader = False 
    while True:
        lpage = makePageFN(inx,"-page.pbm") #make page file name from index
        log("doing page: "+lpage)
        if not os.path.exists(lpage): break #end of pages
        if inx==1: 
            send_file_head() # send header before the first page, if page exists
            lheader = True
        if not addPage(lpage): break
        term("rm "+lpage) #remove page
        inx=inx+1 # next page
    #### file generated, add footer ####
    if lheader: sendFileFoot() #there header had been sent, so send footer
#    if __faked: __out.close()#close ouput file


#find last page - used for backward printing and to avoid extrapage of 
#ps2write device
def findLastPage(fmask):
    llast = -1;
    i  = 1;
    while True:
        lpage = makePageFN(i,fmask) #make page file name from index
        if not os.path.exists(lpage): break #end of pages
        llast = i
        i=i+1
    return llast;

################################
#PRINT ENTIRE FILE
#more advanced than Trivial, splits incoming PostScript file in pages, and then 
#page by page creates PBM, converts to JBIG page and adds to output stream
#pros: only one PBM page stored, so needs way less memory for printing
#cons: uses additional stage for conversion, so works slower them Trivial
#also device ps2Write adds ending extra page to a file(seems bug???).
#to avoid extrapage i'm scipping it, pls report if something is wrong
def doJobSimple():
    linput = getInput()
    #  __gs_ops = "-dQUIET -dBATCH -dNOPAUSE -dSAFER -sPAPERSIZE="+__pagesize #standard Ghost Script options from GS tutorial
    lgs_ops = "-dQUIET -dBATCH -dNOPAUSE -dSAFER" #standard Ghost Script options from GS tutorial
      #convert incoming postscript to page files
    term("gs "+ lgs_ops+" -sDEVICE=ps2write -sOutputFile="+__temp_dir+"%03d-page.ps"	+" -r"+__resolution +" "+ linput)
    #  sys.exit()
    lfooter = False
    inx = 1; # iterate pages images and send them to file, first page has index 1, not 0
    lpbm_out = __temp_dir+"page.pbm"
    llast_page = findLastPage("-page.ps")    
    while inx<llast_page:
        lpage = makePageFN(inx,"-page.ps") #make page file name from index
        log("doing page: "+lpage)
    #   if not os.path.exists(lpage): break #end of pages
        if inx==1: 
            send_file_head() # send header before the first page, if page exists
            lfooter = True
        #convert ps page to curr_page.pbm
        term("gs "+lgs_ops+" -sDEVICE=pbmraw"+" -sOutputFile="+ lpbm_out + " -r"+__resolution+" "+lpage)
        if not addPage(lpbm_out): break
        term("rm "+lpbm_out) #remove page
        inx=inx+1 # next page
    
      #### file generated, add footer ####
    if lfooter: sendFileFoot()
    #cleanup
################################

#doJobTrivial()
doJobSimple()
log("printing: OK")
driverCleanup()
 
exit(0)
