#!/usr/bin/python
############################################################################
#                                                                          #
#  Name: Kismet Log Viewer (KLV) v2 w/ extended features                   #
#                                                                          #
#  Description: KLV accepts one or more Kismet .netxml files, summarizes   #
#               & de-duplicatesthe data, and creates a readable summary    #
#               in either html or csv format.                              #
#                                                                          #
#  Usage: ./klv3.py -h                                                     #
#         ./klv3.py /root/kismet-logs/                                     #
#         ./klv3.py -t csv /root/kismet-logs/                              #
#                                                                          #
#  Requirements: Python                                                    #
#                one or more Kismet .netxml log files                      #
#                                                                          #
#  Website: http://klv.professionallyevil.com                              #
#  Author:  Nathan Sweaney - nathan@sweaney.com                            #
#  Date:   July 9, 2013                                                    #
#                                                                          #
#  -- Extended features                                                    #
#  Website: https://github.com/illegalPointer                              #
#  Author: IllegalPointer                                                  #
#  Date: Jun, 1, 2015                                                      #
#       @NEW GPS,SignalInfo,HTML code on HTML creation (clean CSV)         #
#            -n argument, Modify HTML, Clean \n on CSV, CSV headers        #
#            -o default mode change                                        #
#                                                                          #
############################################################################
"""
Todo:
* add client data
  - To start, just summarize the number of clients for each network.
* add packet data
  - Count of packets seen on each network
* better handling of wireless security - currently only works well for html
  - Maybe use bit counting to keep track of types, then handle output in the output functions.
* add options for sorting
* add option to group BSSIDs
  - effectively de-duplicating SSIDs with all BSSIDs in one table.
  - not sure how this looks in CSV format
* add option to show only specific network types
  - do probe requests & responses need additional information?
* check to see if summary file exists before creating
* name summary file with timestamp
* allow input of specific files, not just a folder
* cool stylesheets
* gracefully handle missing oui.txt file
* gracefully handle no .netxml files
* download updated oui.txt file?
* (*done*) Support GPS info
* create variable for version number instead of spreading it through code
"""

import os    
import sys
import datetime
import xml.etree.ElementTree as ET
import argparse

#Vars
oui_file = open('oui.txt')
network_matrix = []
bssid_list = []
log_file_list = []

now = datetime.datetime.now()
# used on the HTML page output
timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

# process command-line arguments
parser = argparse.ArgumentParser(description='Kismet Log Viewer v3.01.beta creates a readable summary of Kismet .netxml log files.')
parser.add_argument('log_file_path', metavar='LogFilePath',
                   help='A directory containing one or more Kismet .netxml log files. KLV will process all .netxml files in the directory but will ignore all other files.')
parser.add_argument('-o', default="both", choices=['html', 'csv', 'both'],
                   help='Output format (default: html)')
# *Unfinished* parser.add_argument('-s', default="essid", choices=['essid', 'security', 'bssid', 'manufacturer', 'clients', 'packets'], help='Sort output (default: essid) (***unfinished***)')
# *Unfinished parser.add_argument('-g', default="no", choices=['yes', 'no'], help='Group by essid (default: no) (***unfinished***)')
# *Unfinished parser.add_argument('-t', default="beacon", nargs=1, choices=['beacon', 'request', 'response'], help='Show network types (default: beacon only) (***unfinished***)')
parser.add_argument('-n', default="Kismet-Log-Summary", help='Name for the processed files. Filename default: Kismet-Log-Summary')
args = parser.parse_args()
output_format = args.o
summaryFilename = args.n

# add the ending slash in case it was left off
if args.log_file_path[-1:] <> "/":
   args.log_file_path = args.log_file_path + "/"

def main():
   # cycle through each file in the directory
   files_in_dir = os.listdir(args.log_file_path)
   for file_in_dir in files_in_dir:
      if file_in_dir[-7:] == ".netxml":
         print "Adding file: ", file_in_dir 
         log_file_list.append(file_in_dir)

         xml_tree = ET.parse(args.log_file_path + file_in_dir)
         xml_root = xml_tree.getroot()
   
         # loop through each XML node of type "wireless-network"
         for network in xml_root.findall('wireless-network'):
   
            network_type = network.get('type')
   
            # ignoring probes right now
            if network_type <> 'probe':
               network_essid = ""
               network_encryption = ""
               network_bssid = ""
               network_manufacturer = ""
               network_min_signal_dbm = ""
               network_max_signal_dbm = ""
               network_min_signal_rssi = ""
               network_max_signal_rssi = ""
               network_gps_avg_lat = ""
               network_gps_avg_lon = ""
               network_gps_avg_alt = ""
               network_oui = ""
               for network_detail in network:
   
                  if network_detail.tag == 'SSID':
                     for child_network in network_detail:
                        if child_network.tag == 'essid':
                           if child_network.attrib.get("cloaked") == "true":
                              cloaked = "cloaked"
                           else:
                              cloaked = ""
                           if child_network.text is None:
                              network_essid = "" + cloaked
                           else:
                              network_essid = child_network.text + cloaked
   
                        if child_network.tag == 'encryption':
                           network_encryption += child_network.text + '\n'
   
                  if network_detail.tag == 'BSSID':
                     network_bssid = network_detail.text
                     network_oui = network_bssid[0:2] + "-" + network_bssid[3:5] + "-" + network_bssid[6:8]
                     oui_file.seek(0)
                     for line in oui_file:
                        if network_oui in line:
                           network_manufacturer = line[20:]
                           break

                  #Signal Info parsing
                  if network_detail.tag == 'snr-info':
                     for child_network in network_detail:
                        if child_network.tag == 'min_signal_dbm':
                          network_min_signal_dbm += child_network.text
                        if child_network.tag == 'max_signal_dbm':
                          network_max_signal_dbm += child_network.text
                        if child_network.tag == 'min_signal_rssi':
                          network_min_signal_rssi += child_network.text
                        if child_network.tag == 'max_signal_rssi':
                          network_max_signal_rssi += child_network.text
   
                  #GPS Info parsing
                  if network_detail.tag == 'gps-info':
                     for child_network in network_detail:
                        if child_network.tag == 'avg-lat':
                          network_gps_avg_lat += child_network.text
                        if child_network.tag == 'avg-lon':
                          network_gps_avg_lon += child_network.text
                        if child_network.tag == 'avg-alt':
                          network_gps_avg_alt += child_network.text
               
               #OM NOM NOM
               if network_bssid not in bssid_list:
                  bssid_list.append(network_bssid)
                  network_matrix.append([network_essid, network_encryption, network_bssid, network_manufacturer, network_min_signal_dbm, network_max_signal_dbm, network_min_signal_rssi, network_max_signal_rssi, network_gps_avg_lat, network_gps_avg_lon, network_gps_avg_alt])
   
   if output_format == 'both':
     create_html_file(network_matrix)
     create_csv_file(network_matrix)
   elif output_format == 'html':
      create_html_file(network_matrix)
   elif output_format == 'csv':
      create_csv_file(network_matrix)
   
#output to CSV
def create_csv_file(network_matrix):
   summary_file = open(summaryFilename + '.csv','w')
   summary_file.write("ESSID,Security,BSSID,Manufacturer,Min. DBM,Max. DBM,Min. RSSI,Max. RSSI,Lat.,Lon.,Alt.\n")
   for network in network_matrix:
      summary_file.write(network[0] + ',' +network[1].replace('\n', ' ') + ',' + network[2] + ',' + '\"'  + network[3].replace('\n','') + '\"' + ',' + network[4] + ',' + network[5] + ',' + network[6] + ',' + network[7] + ',' + network[8] + ',' + network[9] + ',' + network[10] + '\n')
   summary_file.close()

# output to HTML
def create_html_file(network_matrix):

   summary_file = open(summaryFilename + '.html','w')

   # print header
   summary_file.write('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">\n')
   summary_file.write('<html>\n')
   summary_file.write('  <head>\n')
   summary_file.write('    <title>' + summaryFilename + '</title>\n')
   summary_file.write('  </head>\n')
   summary_file.write('  <body>\n')
   summary_file.write('    <table width="760" border="0" align="center" cellpadding="5" cellspacing="1" bgcolor="#efefef">\n')
   summary_file.write('      <tr>\n')
   summary_file.write('        <td colspan=5 align="left">' + summaryFilename + '</td>\n')
   summary_file.write('        <td colspan=5 align="right"><font size="2">Created: ' + timestamp + '</font></td>\n')
   summary_file.write('      </tr>\n')

   summary_file.write('      <tr bgcolor="#cecece">\n')
   summary_file.write('        <th><font size="2">ID</font></th>\n')
   summary_file.write('        <th align=left><font size="2">Name (ESSID)</font></th>\n')
   summary_file.write('        <th><font size="2">Security</font></th>\n')
   summary_file.write('        <th><font size="2">BSSID</font></th>\n')
   summary_file.write('        <th><font size="2">Manufacturer</font></th>\n')
   summary_file.write('        <th><font size="2">Min. DBM</font></th>\n')
   summary_file.write('        <th><font size="2">Max. DBM</font></th>\n')
   summary_file.write('        <th><font size="2">Min. RSSI</font></th>\n')
   summary_file.write('        <th><font size="2">Max. RSSI</font></th>\n')
   summary_file.write('        <th><font size="2">Lat.</font></th>\n')
   summary_file.write('        <th><font size="2">Lon.</font></th>\n')
   summary_file.write('        <th><font size="2">Alt.</font></th>\n')
#  summary_file.write('        <th><font size="2">&lt;Clients&gt;</font></th>\n')
#  summary_file.write('        <th><font size="2">&lt;Packets&gt;</font></th>\n')
   summary_file.write('      </tr>\n')

   row_toggle = 1
   row = 1
   for network in network_matrix:

      # this flip-flops the background color for each row
      if row_toggle == 1:
         summary_file.write('      <tr>\n')
         row_toggle = 0
      else:
         summary_file.write('      <tr bgcolor="#FFFFFF">\n')
         row_toggle = 1

      summary_file.write('        <td align="center"><font size="2"> ' + str(row) + ' </font></td>\n')
      summary_file.write('        <td><font size="2">' + network[0] + '<br /></font></td>\n')
      summary_file.write('        <td align="center"><font size="2">' + network[1] + '<br /></font></td>\n')
      summary_file.write('        <td align="center"><font size="2">' + network[2] + '<br /></font></td>\n')
      summary_file.write('        <td align="center"><font size="2">' + network[3] + '<br /></font></td>\n')
      summary_file.write('        <td align="center"><font size="2">' + network[4] + '<br /></font></td>\n')
      summary_file.write('        <td align="center"><font size="2">' + network[5] + '<br /></font></td>\n')
      summary_file.write('        <td align="center"><font size="2">' + network[6] + '<br /></font></td>\n')
      summary_file.write('        <td align="center"><font size="2">' + network[7] + '<br /></font></td>\n')
      summary_file.write('        <td align="center"><font size="2">' + network[8] + '<br /></font></td>\n')
      summary_file.write('        <td align="center"><font size="2">' + network[9] + '<br /></font></td>\n')
      summary_file.write('        <td align="center"><font size="2">' + network[10] + '<br /></font></td>\n')
#     summary_file.write('        <td align="center"><font size="2">' + '</font></td>\n')
#     summary_file.write('        <td align="center"><font size="2">' + '</font></td>\n')
      summary_file.write('      </tr>\n')
      row += 1

   summary_file.write('    </table>\n')
   summary_file.write('<br />\n')
   
   # print list of log files
   summary_file.write('    <table width="760" border="0" align="center" cellpadding="5" cellspacing="1" bgcolor="#efefef">\n')
   summary_file.write('      <tr bgcolor="#cecece">\n')
   summary_file.write('        <td align="center">Log files included:</td>\n')
   summary_file.write('      </tr>\n')

   row_toggle = 1
   for log_file in log_file_list:
      # this flip-flops the background color for each row
      if row_toggle == 1:
         summary_file.write('      <tr>\n')
         row_toggle = 0
      else:
         summary_file.write('      <tr bgcolor="#FFFFFF">\n')
         row_toggle = 1
   
      summary_file.write('        <td align="center"><font size="2">' + log_file + '</font></td>\n')
      summary_file.write('      </tr>\n')
   
   summary_file.write('    </table>\n')

   # print footer
   summary_file.write('<br />\n')
   summary_file.write('    <table width="760" border="0" align="center" cellpadding="5" cellspacing="1" bgcolor="#efefef">\n')
   summary_file.write('      <tr>\n')
   summary_file.write('        <td></td>\n')
   summary_file.write('      </tr>\n')
   summary_file.write('      <tr bgcolor="#FFFFFF">\n')
   summary_file.write('        <td align="center"><font size="2">Based on Kismet Log Viewer v2.01 - written by Nathan Sweaney</font></td>\n')
   summary_file.write('        <td align="center"><font size="2">Developed by <a href="https://github.com/illegalPointer">Illegal Pointer</a></font></td>\n')
   summary_file.write('      </tr>\n')
   summary_file.write('      <tr>\n')
   summary_file.write('        <td></td>\n')
   summary_file.write('      </tr>\n')
   summary_file.write('    </table>\n')
   
   summary_file.write('  </body>\n')
   summary_file.write('</html>\n')

   summary_file.close()


main()


