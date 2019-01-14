import re
import os
import psutil
import time
from pprint import pprint
import sys

# --------------------------------------
# Check for other instances and stop self if found
# --------------------------------------
def chk_and_stopall(file_name_in):

   proc_lst = _get_proc_lst(file_name_in)

   for process in proc_lst:

         rtn = process.kill()

         # Get parent if
         #ppid = process.ppid()
         #if ppid :
         #   pprocess = psutil.Process(ppid)
         #   rtn = pprocess.terminate()
   
   time.sleep(1)
   return(len(proc_lst))

# --------------------------------------
# Check for other instances and stop self if found
# --------------------------------------
def chk_and_stopself(file_name_in):

   proc_lst = _get_proc_lst(file_name_in)

   if ( len(proc_lst) > 0 ):
      sys.exit(0)

   return(1)

# ---------------------------------------
def _get_proc_lst(file_name_in):

   file_name_in = os.path.basename(file_name_in)
   pid = os.getpid()

   proc_lst = []

   for process in psutil.process_iter():
      cmdline = process.cmdline()
      if len(cmdline) < 2:
         continue

      # Get the basename of the file called
      file_name_called = cmdline.pop()
      file_name_called = os.path.basename(file_name_called)

      if re.match(file_name_in,file_name_called):

         if pid == process.pid:
            print('Skip self!')
            continue

         proc_lst.append(process)

   return(proc_lst)
