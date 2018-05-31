# Brian Blaylock
# May 31, 2018                            Poor GOES-17 is having cooling issues

"""
Match data collected from the GOES-16 Geostationary Lightning Maper (GLM) with
the Advanced Baseline Imager (ABI) data collection windows.

New GLM files are created every 20 seconds
New ABI files are created every 5 minutes (however, the scan is about 2.5 mins)
Thus, we expect 15 GLM data files for the 5 minute window.

This function gets the GLM files that have ending dates between the ABI scan 
start and five minutes after the scan start. In other words, I want to collect
all the lightning observations during the ABI 5 minute interval.

Approximate Timeline of 5 minutes of ABI and GLM data collection:
    ABI scan    |----------------|_____________|
    GLM scan    |-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.|

    Where:
        - (dash) is 10 seconds of data collection
        _ (underscore) is 10 seconds of no data collection
        . (period) is the interval that the GLM writes a file
"""

import os 
import numpy as np 
from datetime import datetime, timedelta
from netCDF4 import Dataset

import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

import sys
sys.path.append('/uufs/chpc.utah.edu/common/home/u0553130/pyBKB_v2/')
sys.path.append('B:\pyBKB_v2')


def get_GLM_for_ABI(FILE):
    """
    Get all the GLM 'flashes' data the occurred within the 5-minute scan window
    for an ABI scan.

    Input:
        FILE - the path and file name of an ABI scan
    """
    # GOES16 ABI and GLM data is stored on horel-group7 and on Pando
    HG7 = '/uufs/chpc.utah.edu/common/home/horel-group7/Pando/GOES16'

    # Get info from the file name
    FILE_SPLIT = FILE.split('_')
    product = '-'.join(FILE_SPLIT[1].split('-')[:-1]) # remove the scan mode
    sDATE = datetime.strptime(FILE_SPLIT[3], 's%Y%j%H%M%S%f')
    eDATE = sDATE + timedelta(minutes=5)

    # Build path of file on horel-group7
    ABI = '%s/%s/%s/%s' % (HG7, product, sDATE.strftime('%Y%m%d'), FILE)

    # Need to pay attention to weather or not the sDATE.hour and eDATE.hour 
    # are equal. If they are not, then we need to grab GLM data from two 
    # dirtories because the ABI scan spans two different hours.

    if sDATE.hour == eDATE.hour:
        GLM_DIR = '%s/GLM-L2-LCFA/%s/%02d' % (HG7, sDATE.strftime('%Y%m%d'), sDATE.hour)
        GLM = os.listdir(GLM_DIR)
        GLM = ['%s/%s' % (GLM_DIR, i) for i in GLM]
    else:
        GLM_DIR1 = '%s/GLM-L2-LCFA/%s/%02d' % (HG7, sDATE.strftime('%Y%m%d'), sDATE.hour)
        GLM1 = os.listdir(GLM_DIR1)
        GLM1 = ['%s/%s' % (GLM_DIR1, i) for i in GLM1]

        GLM_DIR2 = '%s/GLM-L2-LCFA/%s/%02d' % (HG7, eDATE.strftime('%Y%m%d'), eDATE.hour)
        GLM2 = os.listdir(GLM_DIR2)
        GLM2 = ['%s/%s' % (GLM_DIR2, i) for i in GLM2]
        
        GLM = GLM1 + GLM2

    GLM_FILES = filter(lambda x: datetime.strptime(x.split('_')[4], 'e%Y%j%H%M%S%f') < eDATE
                            and  datetime.strptime(x.split('_')[4], 'e%Y%j%H%M%S%f') >= sDATE, GLM)

    return_this = {'Files': GLM_FILES,
                   'Range': [sDATE, eDATE]                  
                  }
    
    return return_this


if __name__ == '__main__':
    ## ABI File
    #ABI_FILE = 'OR_ABI-L2-MCMIPC-M3_G16_s20181280332199_e20181280334572_c20181280335091.nc'
    ABI = 'OR_ABI-L2-MCMIPC-M3_G16_s20181282357201_e20181282359574_c20181290000075.nc'

    ## Get Cooresponding GLM files
    GLM = get_GLM_for_ABI(ABI)

    ## Make a new map object for the HRRR model domain map projection
    mH = Basemap(resolution='i', projection='lcc', area_thresh=5000, \
                width=1800*3000, height=1060*3000, \
                lat_1=38.5, lat_2=38.5, \
                lat_0=38.5, lon_0=-97.5)

    ## Plot each GLM file on the map
    plt.figure(figsize=[15, 10])

    print 'Datetime Range:', GLM['Range']

    colors = ['k','b','r','g','crimson','dodgerblue','darkgrey', 'coral']*2
    for i, FILE in enumerate(GLM['Files']):
        G = Dataset(FILE, 'r')
        # Marker for each flash
        mH.scatter(G.variables['flash_lon'][:], G.variables['flash_lat'][:],
                marker='+',
                color=colors[i],
                latlon=True)
        G.close()

    mH.drawmapboundary(fill_color='k')
    mH.drawcoastlines(color='w')
    mH.drawcountries(color='w')
    mH.drawstates(color='w')

    plt.title('GOES-16 GLM Flashes', fontweight='semibold', fontsize=15)
    plt.title('Start: %s\nEnd: %s' % (GLM['Range'][0].strftime('%H:%M:%S UTC %d %B %Y'), GLM['Range'][1].strftime('%H:%M:%S UTC %d %B %Y')), loc='right')    