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
#####################################

#set default values
__pageSize = "A4"  #  default page size
__resolution = "600" #ricoh SP1XX supports 600*600 and 1200*600 resolution
__copies = "1"
__mediaSource = "AUTO"  #__mediasource="TRAY1"
__mediaType = "PLAINRECYCLE"

# this modes are implemented in cups, user sets them in printing settings,
# this driver receives proper pages(all,odd,even) in proper order(direct,
# reversed), so we can ignore them our code
__outputOrder="DIRECT" # direct or reversed order
__printPages="ALL" # all, even, odd pages to be printed

#hardware duplex print, we take it into account
__duplex =False

# ricoh printer acceps "the size of page raster in dots",
# which, as people say, could be used to control lifetime of 
# cartrige, but printers sustains faked values, unreally low,
# and doesn't check them. So to possibly improve catrige lifetime
# we can give him low values (real values for text, A4,600dpi are 
# about 200000-300000 dots)
__faked_dotcount="777" 

#############################
__base = sys.path[0]+"/" #script dir
##############################
#######
#for debugging:
#if everyting is OK, set empty strings to this values

__out_fn ="" #default output to sdtout
#__out_fn =__base+"driver.out" #redirects output to this file, not stdout

__log_fn =""#won't dump any
#__log_fn =__base+"LOG.LOG"#will dump logs to this file
#####################################

__out = None #ouput stream

if __out_fn=="":
    __out = sys.stdout #to stdout(normal behaviour)
else:    
    __out = open(__out_fn,"w") #to real file

##################################
#logging
__log_stream = None

if __log_fn != "":
    __log_stream = open(__log_fn, "w") #open log file
    sys.stderr = __log_stream

def log(fs):
    if not __log_stream is None:
        __log_stream.write(fs+'\n')

def closeLog():
    if not __log_stream is None:
        __log_stream.close()

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

#parse options to override default - A4
if    find_option("PageSize=A5"):     __pageSize="A5"
elif  find_option("PageSize=A6"):     __pageSize="A6"
elif  find_option("PageSize=Letter"): __pageSize="Letter"

log("PageSize="+__pageSize) #dump paper size for debugging

#check slot(paper?)...but my printer has only one slot - AUTO(from Windows driver caption)
#because some printers could have different slots, this option is essential for them
if find_option("InputSlot=Auto"): __mediaSource = "AUTO"

#get mediaType
if find_option("MediaType=PLAINRECYCLE"): __mediaType = "PLAINRECYCLE"

if find_option("OutputOrder=Reverse"): _outputOrder="REVERSE"
  
if   find_option('page-set=even'): _printPages="EVEN"
elif find_option('page-set=odd'):  _printPages="ODD"

#printer duplex mode
if find_option("Duplex=DuplexNoTumble"): __duplex = True

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
# at 1200 dpi ricoh sp1xx has 1200*600 resolution
def metric_dimensions(fpaper, fres, fw,fh):
   if fpaper=="A4":
      if fres=="600": return 4961,7016
      if fres=="1200": return  9921, 7016   #9921, 14031
   elif fpaper=="Letter":
      if fres=="600": return 5100,6600
      if fres=="1200":return  10200,6600    #10200,13200
   elif fpaper == "A5":
      if fres=="600": return 3502, 4958 #Pixels
      if fres=="1200": return 7004,4958 #Pixels   #7004,9916 #Pixels 
   elif fpaper == "A6":
      if fres=="600": return 2480, 3508 #Pixels
      if fres=="1200": return 4961, 3508 #4961, 6992 #Pixels 
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
    
    if fsrc!=sys.stdin: fsrc.seek(0)    
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

# send PJL page to output stream
def addPage(fpage, faskflip=False):
    log("sending page:"+fpage)
    if not os.path.exists(fpage): return False

	# Converting page to JBIG format (parameters are very special for this printer!)
    lraster = __temp_dir+"raster.jbig"
    #convert PBM page file to JBIG compressed file
    term("pbmtojbg -p 72 -o 3 -m 0 -q "+fpage+" "+lraster)
    lw, lh = parsePbmSize(fpage) #get raster dimensions in pixels
    log("PAGE ORIGINAL DIMS="+str(lw)+"x"+str(lh))
    lw,lh = cut_dimensions(__pageSize,__resolution,lw, lh)
    
    #lwidth, lheight = "4961","7016"
    log("PAGE CROPPED DIMS="+str(lw)+"x"+str(lh))
  
    lbytes = os.stat(lraster).st_size #get raster size in bytes
    log("RASTER SIZE ="+str(lbytes));
    lfile = open(lraster, "rb");


    if faskflip: # used for hardware duplex mode - printer stops
        pjlLine("MANUALDUPLEX=FLIPSIDE")
    pjlLine("PAGESTATUS=START")
    pjlLine("COPIES="+__copies) #number of copies
    pjlLine("MEDIASOURCE="+__mediaSource) #paper tray to feed
    pjlLine("MEDIATYPE="+__mediaType) #kind of paper
    pjlLine("PAPER="+__pageSize) #size of paper:A4,A5...
    pjlLine("PAPERWIDTH="+str(lw))   # x dimension in pixels
    pjlLine("PAPERLENGTH="+str(lh))  # y dimention in pixels
    pjlLine("RESOLUTION="+__resolution) #resolution (dpi)
    global __duplex    
    if __duplex:
        pjlLine("PURPOSE=MANUALDUPLEXEMPTYPAPER")
        
    pjlLine("IMAGELEN="+str(lbytes)) #bytes in image
#append page raster

    appendFile(__out,lfile)
    log("raster data appended")    
#    if not __copy_stream is None: append_file(__copy_stream,lfile)
#send page footer
    pjlLine("DOTCOUNT="+__faked_dotcount) # here we use fake dotcount
    pjlLine("PAGESTATUS=END")# end of page command
    return True
############def end send_page

#get driver data source
def getInput():
    return " -" 

#cleanup
def driverCleanup():
#    if not __copy_stream is None: __copy_stream.close()
    term("rm -rf "+ __uid) #delete temp folder
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


#find last page - used for backward printing and to avoid extrapage of 
#ps2write device
def findLastPage(fmask):
    llast = -1;
    i  = 1;
    while True:
        lpage = makePageFN(i,fmask) #make page file name from index
        if not os.path.exists(lpage): break #end of pages
        llast = i
        i+=1
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
    log("METHOD: DOING JOB SIMPLE")    
    linput = getInput()
    #  __gs_ops = "-dQUIET -dBATCH -dNOPAUSE -dSAFER -sPAPERSIZE="+__pagesize #standard Ghost Script options from GS tutorial
    lgs_ops = "-dQUIET -dBATCH -dNOPAUSE -dSAFER" #standard Ghost Script options from GS tutorial

    #convert incoming postscript to page files
    term("gs "+ lgs_ops+" -sDEVICE=ps2write -sOutputFile="+__temp_dir+"%03d-page.ps"	+" -r"+__resolution +" "+ linput)
    #  sys.exit()
    lfooter = False
    inx = 1; # iterate pages and send them to file, first page has index 1, not 0
    lpbm_out = __temp_dir+"page.pbm"
    llast_page = findLastPage("-page.ps")    
    log("LAST PAGE = "+str(llast_page))
    if not __duplex: #one side mode     
        while inx<llast_page:
            lpage = makePageFN(inx,"-page.ps") #make page file name from index
            log(">>> doing page: "+lpage)
        #   if not os.path.exists(lpage): break #end of pages
            if inx==1: 
                send_file_head() # send header before the first page, if page exists
                lfooter = True
            #convert ps page to curr_page.pbm
            term("gs "+lgs_ops+" -sDEVICE=pbmraw"+" -sOutputFile="+ lpbm_out + " -r"+__resolution+" "+lpage)
            if not addPage(lpbm_out): break
            term("rm "+lpbm_out) #remove page
            inx+=1 # next page
        
          #### file generated, add footer ####
    else: #Duplex mode
#        lpagesCount=0
        while inx<llast_page: #print odd pages
            lpage = makePageFN(inx,"-page.ps") #make page file name from index
            log(">>> doing page: "+lpage)
        #   if not os.path.exists(lpage): break #end of pages
            if inx==1: 
                send_file_head() # send header before the first page, if page exists
                lfooter = True
            #convert ps page to curr_page.pbm
            term("gs "+lgs_ops+" -sDEVICE=pbmraw"+" -sOutputFile="+ lpbm_out + " -r"+__resolution+" "+lpage)
            if not addPage(lpbm_out): break
#            lpagesCount+=1
            term("rm "+lpbm_out) #remove page
            inx+=2 # next page

        #print even pages
        inx=2
        while inx<llast_page: #print odd pages
            lpage = makePageFN(inx,"-page.ps") #make page file name from index
            log(">>> doing page: "+lpage)
            #convert ps page to curr_page.pbm
            term("gs "+lgs_ops+" -sDEVICE=pbmraw"+" -sOutputFile="+ lpbm_out + " -r"+__resolution+" "+lpage)
            if not addPage(lpbm_out, inx==2): #at inx==2 printer must ask user to flip paper
                break
#            lpagesCount+=1
            term("rm "+lpbm_out) #remove page
            inx+=2 # next page
    
#    log("TOTAL PAGES = "+str(lpagesCount))    
    if lfooter: sendFileFoot()


#more sophisticated print
#we are starting GS as subpocess in interactive page by page mode(expecting user prompt)
#every prompt signals that page is ready, we process this page, delete it, and wait next 
#page. Here is only one conversion, and disc usage is minimal
#but we need to copy incoming PS from stdin to a file
def doJob() :
#copy stdin to a file
  lsavfn =  __temp_dir+"TEMP.PS" #filename for saved file
  lin = open(lsavfn,"w")
  appendFile(lin,sys.stdin,1024)
  lin.close()    

#run conversion PS->PBM as subprocess with pipes
  p =subprocess.Popen(
     ["gs"
     ,"-dQUIET"
     ,"-dBATCH"
     ,"-dSAFER"  
     ,"-sDEVICE=pbmraw"
     ,"-sOutputFile="+__temp_dir+"%03d-page.pbm"
     ,"-r"+__resolution
      #,linput]
     ,lsavfn]
     , shell=False
     , stdin  = subprocess.PIPE 
     , stdout = subprocess.PIPE
   ) 
  
  lfooter=False
  inx = 1; # scan pages images and send them to file, first page has index 1, not 0
  while True:
      log("waiting gs prompt")
      ls = p.stdout.readline(); #wait for propmt
      if ls!="": p.stdin.write('\n') #reply to the pronpt
      log(ls) #log the prompt for debugging
      if inx==1: 
          send_file_head() # send header before the first page, if page exists
          lfooter = True
     
      lpage =  makePageFN(inx,"-page.pbm")#make page file name from index
      if not addPage(lpage): break
      term("rm "+lpage) #delete processed page
      inx+=1 # next page

  #### file generated, add footer ####
  if lfooter: sendFileFoot()

################################
#doJobTrivial()
doJobSimple() #just now omly JobSimple supports duplex mode
#doJob()
log("printing: OK")
driverCleanup()
 
exit(0)