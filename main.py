# project: p5
# submitter: wlangas
# partner: none
# hours: 17

import sys, time, csv, json, os, re
import netaddr, geopandas
import pandas as pd
from zipfile import ZipFile
from io import TextIOWrapper
import matplotlib.pyplot as plt
import numpy as np

idx = 0

def ip_checker(ips):
    small = 999999999999
    large = 999999999999
    prev = None
    
    with open("ip2location.csv") as f:
        results = list()
    
        file = csv.reader(f)
        header = next(file) # skip over the header row
        data = list(file)
        length = len(data)
        region = None # Initialize the region value
        
        middle = length // 2 # Integer division split the length of the data
    
        for ip in ips:
            start = time.time() # Record start time
            current = dict()
            
            int_ip = int(netaddr.IPAddress(str(ip))) # Cast to Int
            
            if int_ip <= int(large) and int_ip >= int(small):
                region = prev
            else:
                if (int_ip >= int(data[middle][0])):
                    start = middle
                else:
                    start = 0 # reset the start time 
             
                for i in range(int(start), int(length)):
                    if int_ip >= int(data[i][0]) and int_ip <= int(data[i][1]):
                        region = data[i][3]
                        small  = data[i][0]
                        large = data[i][1]
                                
            end = time.time() # end time
            
            current["ip"] = ip
            current["int_ip"] = int_ip
            current["region"] = region
            current["ms"] = end - start
            results.append(current)
            
            prev = region
        print(json.dumps(results)) # print the results
    return results

# From sample hints
def zip_csv_iter(name):
    with ZipFile(name) as zf:
        with zf.open(name.replace(".zip", ".csv")) as f:
            reader = csv.reader(TextIOWrapper(f))
            for row in reader:
                yield row

# Key for sorting the ips by, also fixes the random letters at the end of the IP
def ip_sort(ip):
    return int(netaddr.IPAddress(str(ip[0][:-4] + ".000")))
                
def sample(zip1, zip2, mod):
    global idx
    reader = zip_csv_iter(zip1) # create a reader object
    header = next(reader) # strip the header off, added to the file later
      
    ips = list() # will hold the actual ip addresses
    results = list() # will hold all the information for each ip
    
    for row in reader:
        if (idx % mod == 0): # if the count matches the stride
            results.append(row)
            
            ip_int = int(netaddr.IPAddress(str(row[0][:-4] + ".000"))) # manipulate the ip
            ips.append(ip_int) # add to the list that will be ip checked later
        idx = idx + 1
        
    ip_dict = ip_checker(ips)
    idx = 0
    for item in ip_dict:
        results[idx].append(item.get("region")) # add the region to the results list
        idx = idx + 1
    
    results.sort(reverse=False, key=ip_sort) # sort all the results by the ID
    
    header.append("region") # add region to the header then put it into the results, which is then written to zip below
    results.insert(0, header)
    
    with ZipFile(zip2, "w") as zf:
        with zf.open(zip2.replace("zip", "csv"), "w") as f:
            with TextIOWrapper(f) as tio:
                csv_writer = csv.writer(tio, lineterminator="\n")
                for item in results:
                    csv_writer.writerow(item)
                    
# https://piazza.com/class/kjomvrz8kyl64u?cid=774
def world(zip1, file_name):
    
    # Creates the graph to plot
    world = geopandas.read_file(geopandas.datasets.get_path('naturalearth_lowres'))
    non_ant = world["continent"] != "Antarctica"
    world = world[non_ant] 
    
    sample(zip1, "world.zip", 1) # Now we have a zip with all the tracked IPs of the data
    
    # Now we need to read through them and make a dict of the countries
    reader = zip_csv_iter("world.zip")
    header = next(reader)
    requests = dict()
    for row in reader:
        if row[15] in requests.keys():
            requests[row[15]] += 1
        else:
            requests[row[15]] = 0
            
    world["requests"] = world["name"].map(requests) # Add the requests data to the dataframe
    
    # All the plot formatting
    world.plot(
    column="requests",
    legend=True,
    scheme="quantiles",
    figsize=(15, 10),
    missing_kwds={
            "color": "lightgrey",
            "edgecolor": "red",
            "label": "Missing values",
        },
    ).get_figure().savefig(file_name,format="svg")

# https://piazza.com/class/kjomvrz8kyl64u?cid=826
def phone(zip1):
    # open the zip up
    with ZipFile(zip1) as zf:
        files = zf.namelist()
        for file_name in files:
            with zf.open(file_name, "r") as f:
                tio = TextIOWrapper(f)
                text = tio.read()
                phone_lookup(text)
        
def phone_lookup(text):
    results = []
    results += re.findall(r'\(\d{3}\)d{3}-\d{4}', text) # Pattern 1: Parens
    results += re.findall(r'[1-9]\d{2}-\d{3}-\d{4}', text) # Pattern 2: No Parens
    results += re.findall(r'\(\d{3}\)\s*\d{3}-\d{4}', text) # Pattern 3: Spaces in there
    
    results = set(results)
    results = list(results) # Trying to remove duplicates
    
    numbers = []
    [numbers.append(x) for x in results if x not in numbers] # Trying again, not sure why it's not working
    
    for number in numbers:
        print(number)
    
def main(): # Handle the inputs to the program
    if len(sys.argv) < 2:
        print("usage: main.py <command> args...")
    elif sys.argv[1] == "ip_check":
        ips = sys.argv[2:]
        ip_checker(ips)
    elif sys.argv[1] == "sample":
        zip1 = sys.argv[2]
        zip2 = sys.argv[3]
        mod = int(sys.argv[4])
        print(mod)
        sample(zip1, zip2, mod)
    elif sys.argv[1] == "world":
        zip1 = sys.argv[2]
        file_name = sys.argv[3]
        world(zip1, file_name)
    elif sys.argv[1] == "phone":
        phone(sys.argv[2])
    else:
        print("unknown command: "+sys.argv[1])

if __name__ == '__main__':
     main()