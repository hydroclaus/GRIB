#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This script
- loads grib files using pygrib
- processes them
- plots a map of the wind field
"""

import sys
import os
import numpy as np

import pygrib as grb

import datetime
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap, cm

__author__ = "Claus Haslauer (mail@planetwater.org)"
__version__ = "$Revision: 0.1 $"
__date__ = datetime.datetime(2014,02,01)
__copyright__ = "Copyright (c) 2014 Claus Haslauer"
__license__ = "Python"

def main():
    plt.ioff()

    # adapt for location of datasources
    grb_path = os.getcwd()
    grb_file = 'Mediterranean.wind.3day.grb'
    grb_fobj = os.path.join(grb_path, grb_file)

    # load data
    grbs = grb.open(grb_fobj)

    # i guess i wanted to use a dictionary to be ready when using
    #     additional data sources
    grb_sets = {'globalmarinenet': grbs }

    # data_lst is a list containing 24 grib files
    #   12 snapshots in time
    #   6 hours apart
    #   for U and V components
    data_lst_all = get_grb_data(grb_sets)

    # if jump=1 it plots all data
    # if jump is any other positive integer, 
    #     it jumps over that many data sources
    jump = 1
    data_lst = data_lst_all[::jump]

    n_cols = 3
    n_rows = int(len(data_lst)/(2.0*n_cols))

    one_ax_x = 10
    one_ax_y = 6
    fig_size = (one_ax_x*n_cols, one_ax_y*n_rows)

    cur_date = data_lst_all[0][-2]
    cur_time = data_lst_all[0][-1]
    date_string = 't_0__%i_%i' % (cur_date, cur_time)
    t_zero = datetime.datetime(int(str(cur_date)[:4])
                             , int(str(cur_date)[4:6])
                             , int(str(cur_date)[6:])
                             , int(str(cur_time)[:1])
                             , int(str(cur_time)[1:])
                             )

    print "t_zero: ", t_zero

    # -----------------------
    # make the plots
    fig, axes = plt.subplots(nrows=n_rows
                           , ncols=n_cols
                           , figsize=fig_size
#                            , sharex=True
#                            , sharey=True
                            )
    plt.subplots_adjust(left=0.1, bottom=0.1, right=0.9, top=0.9,
                wspace=None, hspace=None)

    for ax_ctr, ax in enumerate(axes.flat):
        grb_1 = data_lst[ax_ctr*2]
        grb_2 = data_lst[(ax_ctr*2)+1]
        make_wind_map(ax
                    , ax_ctr
                    , grb_1
                    , grb_2
                    , jump
                    , t_zero
                    )

    plt.suptitle(date_string)
    #plt.show()
    plt.tight_layout()
    plt.savefig(date_string+'.png', dpi=150)

    print "Done!"

def get_grb_data(grb_sets, talk_to_me=True):

    """
    to find out what is in a grb file:
        for item in cur_grb.keys():
            print item
    """

    grbs = grb_sets['globalmarinenet']

    data_lst = []

    grbs.seek(0)
    for cur_grb in grbs:
        temp = []
        print cur_grb

        cur_lats, cur_lons = cur_grb.latlons()
        cur_data = cur_grb['values']
        cur_data_date = cur_grb['dataDate']
        cur_data_time = cur_grb['dataTime']

        temp = [cur_data, cur_lats, cur_lons, cur_data_date, cur_data_time]
        data_lst.append(temp)

        if talk_to_me == True:
            print cur_lats.shape, cur_lats.min(), cur_lats.max(), cur_lons.shape, cur_lons.min(), cur_lons.max()
            print cur_data.shape, cur_data.min(), cur_data.max()
            print "grid definition: ", cur_grb['gridDefinition']
            print cur_grb['yearOfCentury'], cur_grb['month'], cur_grb['day'], cur_grb['hour']
            print "units: ", cur_grb['units']
            print "data date: ", cur_data_date
            print "data time: ", cur_data_time
            print "validity date: ", cur_grb['validityDate']
            print '---'

    return data_lst


def make_wind_map(ax, ax_ctr, grb_1, grb_2, jump, t_zero, use_knots=True):
    """
    Convention for barbs:
      - Each half of a flag depicts five knots
      - Each full flag depicts 10 knots
      - Each pennant (filled triangle) depicts 50 knots[4]

      http://de.wikipedia.org/wiki/Windgeschwindigkeit

      1 kn      = 1 sm/h (exakt)           = 1,852 km/h (exakt)    = 0,514 m/s
      1 m/s     = 3,6 km/h (exakt)         = 1,944 kn              = 2,237 mph
      1 km/h    = 0,540 kn                 = 0,278 m/s             = 0,621 mph
      1 mph     = 1,609344 km/h (exakt)    = 0,8690 kn             = 0,447 m/s
    """
    u = grb_1[0]
    v = grb_2[0]
    if use_knots == True:
        u = u * 1.944
        v = v * 1.944
    wind_v = np.sqrt(u**2. + v**2.)
    print "min: %d,    max: %d" % (wind_v.min(), wind_v.max())

    cur_lats = grb_1[1]
    cur_lons = grb_2[2]

    cur_t = 6.0 + (ax_ctr * (jump * 6.0))
    time_delta = datetime.timedelta(hours=cur_t)
    cur_time = t_zero + time_delta

    # create polar stereographic Basemap instance.
    m = Basemap(projection='cyl'    # Stereographic
#               , lon_0 = 0.
#               , lat_0 = 90.
#               , lat_ts = 0.
              , llcrnrlat = cur_lats.min()
              , urcrnrlat = cur_lats.max()
              , llcrnrlon = cur_lons.min()
              , urcrnrlon=cur_lons.max()
#               , rsphere=6371200.
              , resolution='l'
              , area_thresh=10000
              , ax=ax)

    # draw parallels.
    parallels = np.arange(0.,90,10.)
    m.drawparallels(parallels,labels=[1,0,0,0],fontsize=10)
    # draw meridians
    meridians = np.arange(0.,180.,10.)
    m.drawmeridians(meridians,labels=[0,0,0,1],fontsize=10)

    ny = wind_v.shape[0]
    nx = wind_v.shape[1]
    lons, lats = m.makegrid(nx, ny) # get lat/lons of ny by nx evenly space grid.
    x, y = m(lons, lats) # compute map proj coordinates.

    # draw filled contours.
    #clevs = [0,1,2.5,5,7.5,10,15,20,30,40,50,70,100,150,200,250,300,400,500,600,750]
    #cs = m.contourf(x,y,wind_v,clevs,cmap=cm.s3pcpn)

    barbs = m.barbs(x,y,u,v
                    , length=6
                    , barbcolor='k'
                    , flagcolor='r'
                    , linewidth=0.5
                    , zorder=999
                    )

    # draw coastlines, state and country boundaries, edge of map.
    m.drawcoastlines(color = "Gray", zorder = 0)
    #m.drawmapboundary(fill_color='aqua')
    #m.drawstates()
    #m.drawcountries()
    m.fillcontinents(color='coral',lake_color='aqua', alpha=0.2, zorder=1)

    # add colorbar.
    #cbar = m.colorbar(cs,location='bottom',pad="5%")
    #cbar.set_label('m/s')

    # add title
    cur_ti_str = cur_time.strftime('%Y-%m-%d, %H:%M')
    ax.set_title('t_0 + %ih | %s' % (cur_t, cur_ti_str))


if __name__ == '__main__':
    main()