# peak.py ---
#
# Filename: peak.py
# Description:
#            peak analysis
# Author:    Yu Lu
# Email:     yulu@utexas.edu
# Github:    https://github.com/SuperYuLu
#
# Created: Tue Jun 26 16:50:12 2018 (-0500)
# Version:
# Last-Updated: Fri Aug 24 22:39:06 2018 (-0500)
#           By: yulu
#     Update #: 298
#


import pandas
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import quad

import scibeam
from . import base
from .gaussian import Gaussian
from . import tofseries


__all__ = [
    'SeriesPeak',
    'FramePeak',
    ]

class SeriesPeak(pandas.Series):
    """Peak analysis on 1D labeled / unlabeled data

    Build on top of pandas.Series, this adds more methods on peak analysis for
    pandas series data. The any class instance of SeriesPeak can still access
    all pandas sereis methods.

    By default, the indexes is treated as the time axis, while the values of
    series is the data value.

    Additionally, SeriesPeak is also designed as a mixin class which can be used
    as a method chain in other pandas dataframe / sereis based data formats.

    Attributes
    ----------
    self : pandas series
        pandas series data

    """
    def __init__(self, *args, **kwargs):
        """assign value to initialize SeriesPeak

        The initlization of this class can be done exactly as one initlize
        pandas series, for more information please pandas series documentation.

        """
        super().__init__(*args, **kwargs)

    @classmethod
    def _constructor(cls, *args, **kwargs):
        """class constructor

        The classmethod consturctor here are used to make sure the class
        instance element-wise operation still yields the object from the same
        class. Anther function is when it's used for a mixin class as for method
        chain, this will pass a copy of the class instance to make sure data
        is 'type safe'

        args, kwargs are the same as in __init__()

        """
        return cls(*args, **kwargs)


    def gausFit(self, plot = False, offset = False):
        """Fit series with gausssian function

        This gasussian fit function assumes the time or x-axis values is given
        by series index, while the measurement data or y-axis values is given by
        the values of sereis.

        Optionally the one can choose to plot the fitted gaussian curve together
        with the raw data to visuallize the fitting property.

        Parameters
        ----------
        plot : bool
            If True a plot will be generated with raw data and fitted gaussian
            curve. Others no plot will be generated. Default False.
        offset : bool
            If True, the gaussian fitting will consider also fit the data
            offset. If False (default), the fitting procedure will assume that
            the data has 0 offset.

        Returns
        -------
        popt : 1D array
            optimized parameters of gaussian fitting.
            [A, x0, sigma, y0(optional)] Where
            A: peak height of gaussian function
            x0: peak center x coordinates
            sigma: standard deviation
            y0: offset. Only exist if parameter offset is set to be 'True'
        pcov : 2D array
            Covariance matrix of fitted parameters corresponding to popt

        """
        popt, pcov = Gaussian.gausFit(x = self.index, y = self.values, offset = offset, plot = plot)
        return popt, pcov

    def idx(self, gauss_fit = False, offset = False):
        """find x-axis value corresponding to peak

        This funciton is to locate the corresponding x corrdinate or 'index' of
        the peak. Depend on the value of parameter 'gauss_fit', the x coordinate
        of peak can either come from the max value or gaussian fitting.

        The index of series is treated as the x coordinate of the data.

        Parameters
        ----------
        gauss_fit : bool
            If true, the x coordinate corresponding to peak is get by performing
            gaussian fitting on the data, as in member method gausFit.
            If false, the maxmium value of data will be treated as the 'peak',
            and its corresponding x coordinate will be returend.
        offset : bool
            If True, the gaussian fitting will consider also fit the data
            offset. If False (default), the fitting procedure will assume that
            the data has 0 offset.

        Returns
        -------
        float
            The x coordinate that corresponding to the peak

        """
        if gauss_fit:
            return self.gausFit(offset = offset)[0][1]
        else:
            return self.idxmax()

    def nidx(self, gauss_fit = False, offset = False):
        """number index of the peak

        Similar to member method idx, this one returns the number index rather
        than the real index, which means self.index[nidx] = idx

        """
        if gauss_fit:
            height = self.height(gauss_fit = gauss_fit, offset = offset)
            nidx = np.argmin(abs(self.values - height))
        else:
            nidx = np.argmax(self.values)
        return nidx

    def height(self, gauss_fit = False, offset = False):
        """calculate peak height 
        
        Calculated the peak height, either by gaussian fitting (if gauss_fit
        true), or simply return the maximium as the peak height (default)

        Parameters
        ----------
        gauss_fit : bool
            If true, the peak height is get by performing a gaussian fit
            If false, simply the maximium value in the given data 
        offset : bool
            If True, the gaussian fitting will consider also fit the data
            offset. If False (default), the fitting procedure will assume that
            the data has 0 offset.

        Returns
        -------
        float 
            Peak height 
        """
        if gauss_fit:
            return self.gausFit(offset = offset)[0][0]
        else:
            return self.max()

    def sigma(self, n_sigmas = 1, gauss_fit = False, offset = False):
        """Find peak width

        Find the peak width, with specified mutiples of standard deviation.
        The width can be obtained by literally calculate the full-width-half-max
        or by gaussian fitting, depend on the parameter value 'gauss_fit' to be
        true of false.

        Parameters
        ----------
        n_sigmas : integer 
            Multiplies of standard deviations of the peak width is wanted 
        gauss_fit : bool
            If true, the peak width is obtained from gaussian fitting
            If False (default), the peak width is calculated from literally 
            full-width-half-max.
        offset : bool
            If True, the gaussian fitting will consider also fit the data
            offset. If False (default), the fitting procedure will assume that
            the data has 0 offset.

        Returns
        -------
        float
            The peak width in terms of multiples of standard deviatioins

        """
        if gauss_fit:
            return n_sigmas * self.gausFit(offset = offset)[0][2]
        else:
            peak_values = max(self)
            peak_idx = np.argmax(self.values)
            half_max = peak_values / 2
            hwhm_idx_left = np.argmin(abs(self.iloc[:peak_idx].values - half_max))
            hwhm_idx_right = np.argmin(abs(self.iloc[peak_idx : ].values - half_max)) + peak_idx
            fwhm = self.index[hwhm_idx_right] - self.index[hwhm_idx_left]
            sigma = fwhm / np.sqrt(8*np.log(2))
            return sigma * n_sigmas

    def fwhm(self, gauss_fit = False, offset = False):
        """Full-Width-Half-Maximium

        Find the Full-Width-Half-Maximium (FWHM) of the peak, from 
        gaussian fitting or direction calculation.

        Parameters
        ----------
        gauss_fit : bool
            If true, fwhm is get from gaussian fitting 
            If false (default), fwhm is from direction calculation 
        offset : bool
            If True, the gaussian fitting will consider also fit the data
            offset. If False (default), the fitting procedure will assume that
            the data has 0 offset.
        Returns 
        -------
        float
            peak full-width-half-maximium value
        
        """
        sigma = self.sigma(n_sigmas = 1, gauss_fit = gauss_fit, offset = offset)
        return sigma * np.sqrt(8 * np.log(2))

    def area(self, gauss_fit = False, offset = False):
        
        if gauss_fit:
            popt, pcov = self.gausFit()
            # if with offset
            #area = quad(lambda x:Gaussian.gaus(x, *popt) - popt[-1], min(data_label), max(data_label))[0]
            # assume no offset
            area = quad(lambda x:Gaussian.gaus(x, *popt), min(self.index), max(self.index))[0]
        else:
            # if with offset
            # area = np.trapz(x = data_label, y = self - np.min(self))

            # assume no offset
            area = np.trapz(x = self.index, y = self.values)
        return area

    def region(self, n_sigmas = 4, plot = False, offset = False):
        """Auto find the peak region

        Locate the region where there exists a peak and return 
        the lower and upper bound index of the region.

        Parameters
        ----------
        
        """
        peak_nidx = self.nidx()
        peak_value = self.iloc[peak_nidx]

        hwhm_nidx_left = peak_nidx - np.argmin(abs(self.iloc[peak_nidx:0:-1].values - peak_value / 2))
        hwhm_nidx_right = np.argmin(abs(self.iloc[peak_nidx:].values - peak_value / 2)) + peak_nidx
        fwhm_nidx_range = hwhm_nidx_right - hwhm_nidx_left

        delta_nidx = int(fwhm_nidx_range / np.sqrt(8 * np.log(2)) * n_sigmas)
        lb,ub  = peak_nidx - delta_nidx, peak_nidx + delta_nidx
        lb = 0 if lb < 0 else lb
        ub = len(self) if ub > len(self) else ub

        if plot:
            plt.plot(self.index, self.values, '--', label = 'raw input')
            plt.plot(self.index[lb:ub], self.values[lb:ub], '-', label = 'detected peak')
        return lb, ub

    def autocrop(self, n_sigmas = 4, offset = False):
        lb, ub =  self.region(n_sigmas = n_sigmas, plot = False)
        return self._constructor(self.iloc[lb:ub])






class FramePeak(pandas.DataFrame):
    """
    Peak analysis on 1D labeled / unlabeled data
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _toTOFSeries(func):
        """
        Decorator to wrap series returns for method chain
        """
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if type(result) == pandas.core.series.Series:
                return tofseries.TOFSeries(result)
            else:
                return result
        return wrapper

    @classmethod
    def _constructor(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @_toTOFSeries
    def idx(self, axis = 0, gauss_fit = False, normalize = False):
        selfCopy = self.copy() if axis == 0 else self.copy().T
        if gauss_fit:
            idx =  selfCopy.apply(lambda s: Gaussian.gausFit(x = s.index, y = s.values, offset = False)[0][1])
        else:
            idx =  selfCopy.idxmax()
        if normalize:
            idx = idx / idx.max()
        return idx

    @_toTOFSeries
    def nidx(self, axis = 0, gauss_fit = False, normalize = False):
        selfCopy = self.copy() if axis == 0 else self.copy().T
        if gauss_fit:
            height = selfCopy.height(gauss_fit)
            n_idx = [np.argmin(abs(selfCopy[x].values - h)) for x, h in zip(selfCopy.columns, height)]
        else:
            n_idx = [np.argmax(selfCopy[x].values) for x in selfCopy.columns]
        n_idx = pandas.Series(n_idx, selfCopy.columns)
        if normalize:
            n_idx = n_idx / n_idx.max()
        return n_idx

    @_toTOFSeries
    def height(self, axis = 0, gauss_fit = False, normalize = False):
        selfCopy = self.copy() if axis == 0 else self.copy().T
        if gauss_fit:
            height =  selfCopy.apply(lambda s: Gaussian.gausFit(x = s.index, y = s.values, offset = False)[0][0])
        else:
            height =  selfCopy.max()
        if normalize:
            height = height / height.max()
        return height

    @_toTOFSeries
    def sigma(self, n_sigmas = 1, axis = 0, gauss_fit = False, normalize = False):
        selfCopy = self.copy() if axis == 0 else self.copy().T

        def col_sigma(series):
            if gauss_fit:
                return Gaussian.gausFit(x = series.index, y = series.values, offset = False)[0][2]
            else:
                peak_values = max(series)
                peak_idx = np.argmax(series.values)
                half_max = peak_values / 2
                try:
                    hwhm_idx_left = np.argmin(abs(series.iloc[:peak_idx].values - half_max))
                    hwhm_idx_right = np.argmin(abs(series.iloc[peak_idx : ].values - half_max)) + peak_idx
                except ValueError: # When there is no peak found
                    return 0
                fwhm = series.index[hwhm_idx_right] - series.index[hwhm_idx_left]
                sigma = fwhm / np.sqrt(8*np.log(2))
            return sigma * n_sigmas

        sigma =  selfCopy.apply(col_sigma)
        if normalize:
            sigma = sigma / sigma.max()
        return sigma

    @_toTOFSeries
    def fwhm(self, axis = 0, gauss_fit = False, normalize = False):
        sigma = self.sigma(n_sigmas = 1, axis = axis, gauss_fit = gauss_fit, normalize = False)
        fwhm = sigma * np.sqrt(8 * np.log(2))
        if normalize:
            fwhm  = fwhm / fwhm.max()
        return fwhm

    @_toTOFSeries
    def area(self, axis = 0, gauss_fit = False, normalize = False):
        selfCopy = self.copy() if axis == 0 else self.copy().T
        def col_area(series):
            if gauss_fit:
                for col in series.columns:
                    popt, pcov = Gaussian.gausFit(x = series.index, y = series[col].values)
                    area = quad(lambda x:Gaussian.gaus(x, *popt), min(series[col].index), max(series[col].index))[0]

            else:
                area = np.trapz(x = series.index, y = series.values)
            return area

        area = selfCopy.apply(col_area)

        if normalize:
            area = area / area.max()
        return area


    @_toTOFSeries
    def region(self, axis = 0, n_sigmas = 4, plot = False):
        """
        Locate the region where there exists a peak
        return the bound index of the region
        """
        selfCopy = self.copy()
        def col_region(series, plot = False):
            series = SeriesPeak(series.copy())
            peak_nidx = series.nidx()
            peak_value = series.iloc[peak_nidx]

            try:
                hwhm_nidx_left = peak_nidx - np.argmin(abs(series.iloc[peak_nidx:0:-1].values - peak_value / 2))
                hwhm_nidx_right = np.argmin(abs(series.iloc[peak_nidx:].values - peak_value / 2)) + peak_nidx
                fwhm_nidx_range = hwhm_nidx_right - hwhm_nidx_left
            except ValueError: # incase the peak is on the edge, e.g. no peak in the region
                return (int(len(series) / 2), int(len(series) / 2))

            delta_nidx = int(fwhm_nidx_range / np.sqrt(8 * np.log(2)) * n_sigmas)
            lb,ub  = peak_nidx - delta_nidx, peak_nidx + delta_nidx
            lb = 0 if lb < 0 else lb
            ub = len(series) if ub > len(series) else ub

            if plot:
                plt.plot(series.index, series.values, '--', label = 'raw input')
                plt.plot(series.index[lb:ub], series.values[lb:ub], '-', label = 'detected peak')
            return lb, ub

        if axis == 0:
            return selfCopy.apply(col_region)
        elif axis == 1:
            return selfCopy.T.apply(col_region)
        else: # Currently the 2D peak detect doesn't work well
            lb0 = min([x[0] for x in selfCopy.apply(col_region)])
            ub0 = max([x[1] for x in selfCopy.apply(col_region)])
            lb1 = min([x[0] for x in selfCopy.T.apply(col_region)])
            ub1 = max([x[1] for x in selfCopy.T.apply(col_region)])
            return lb0, ub0, lb1, ub1
