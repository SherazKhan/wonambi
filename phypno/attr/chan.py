# -*- coding: utf-8 -*-
"""Module to work with channels.

It provides a general class to work with channels. Channels is the general term
that refers to the points where signal comes from, it's an abstract concept.
Electrodes, magnetometer, axiometers and gradiometers are the actual recording
devices measuring the signal. For example, in the case of EEG, you need two
electrodes to have one signal, where one signal is the difference between the
two electrodes.

In other words, the channel is where you want to plot the signal.

"""
from logging import getLogger
lg = getLogger(__name__)

from os.path import splitext

from numpy import zeros, asarray

from ..utils import UnrecognizedFormat


mu = '\N{GREEK SMALL LETTER MU}'


def _convert_unit(unit):
    """Convert different names into SI units.

    Parameters
    ----------
    unit : str
        unit to convert to SI

    Returns
    -------
    str
        unit in SI format.

    Notes
    -----
    SI unit such as mV (milliVolt, mVolt), μV (microVolt, muV).

    """
    if unit is None:
        return ''

    prefix = None
    suffix = None
    if unit[:5].lower() == 'milli':
        prefix = 'm'
        unit = unit[5:]
    elif unit[:5].lower() == 'micro':
        prefix = mu
        unit = unit[5:]
    elif unit[:2].lower() == 'mu':
        prefix = mu
        unit = unit[2:]

    if unit[-4:].lower() == 'volt':
        suffix = 'V'
        unit = unit[:-4]

    if prefix is None and suffix is None:
        unit = unit
    elif prefix is None and suffix is not None:
        unit = unit + suffix
    elif prefix is not None and suffix is None:
        unit = prefix + unit
    else:
        unit = prefix + suffix

    return unit


def _read_csv(elec_file):
    """TODO:documentation

    """
    chan_label = []
    num_lines = sum(1 for line in open(elec_file))
    chan_pos = zeros((num_lines, 3))

    with open(elec_file, 'r') as f:
        for i, l in enumerate(f):
            a, b, c, d = [t(s) for t, s in zip((str, float, float, float),
                          l.split(','))]
            chan_label.append(a)
            chan_pos[i, :] = [b, c, d]

    return chan_label, chan_pos


def detect_format(filename):
    """Detect file format of the channels based on extension.

    Parameters
    ----------
    filename : str
        name of the filename

    Returns
    -------
    str
        file format

    """
    if splitext(filename)[1] == '.csv':
        recformat = 'csv'
    else:
        recformat = 'unknown'

    return recformat


def export_csv(chan, elec_file):
    """Write the elec coordinates into a csv file.

    Parameters
    ----------
    chan : instance of class Chan
        the definition of the channels
    elec_file : str
        path to file where to save csv

    """
    with open(elec_file, 'w') as f:
        for one_chan in chan.chan:
            line = '{0}, {1:.4}, {2:.4}, {3:.4}\n'.format(one_chan.label,
                                                        one_chan.xyz[0],
                                                        one_chan.xyz[1],
                                                        one_chan.xyz[2],
                                                        )
            f.write(line)


class Chan():
    """Provide class Chan, for individual channels.

    Parameters
    ----------
    label : str
        name of the channel
    xyz : numpy.ndarray or list or tuple
        1d vector of 3 elements
    chtype : str, optional
        channel type (can be any string)
    unit : str, optional
        units, using SI
    attr : dict
        dictionary where you can store additional information per channel. Use
        chan.attr.update({'new_key': new_value})

    """
    def __init__(self, label, xyz=None, unit=None, attr=None):
        self.label = label
        self.xyz = asarray(xyz)
        self.unit = _convert_unit(unit)
        if attr is None:
            self.attr = {}
        else:
            self.attr = attr


class Channels():
    """Provide class Chan, generic class for channel location.

    You can read from a file, and then you pass only one argument.
    Or you can directly assign the chan names and the coordinates.

    Parameters
    ----------
    chan : list of instance of Chan
        list of channels (which are instances of Chan)

    Parameters
    ----------
    chan_input : various formats
        information about the channels

    Parameters
    ----------
    labels : list of str
        the name of the channel
    coords : numpy.ndarray
       location in 3D, with shape (3, n_chan)

    Attributes
    ----------
    chan : list of instance of phypno.attr.chan.Chan
        list of channels

    Raises
    ------
    UnrecognizedFormat
        If the format is not recognized

    Notes
    -----
    chan_input can be a csv file without header and with format:
    label, x-pos, y-pos, z-pos

    """
    def __init__(self, *args):

        if len(args) == 1 and isinstance(args[0], list):
            self.chan = args[0]
        else:
            self.chan = []

            labels = None
            xyz = None

            if len(args) == 1:
                format_ = detect_format(args[0])
                if format_ == 'csv':
                    labels, xyz = _read_csv(args[0])
                else:
                    raise UnrecognizedFormat('Unrecognized format ("' +
                                             format_ + '")')

            elif len(args) == 2:
                labels = args[0]
                if args[1].shape[1] == 3:
                    xyz = args[1]
                else:
                    raise ValueError('Incorrect shape: the second dimension '
                                     'should be 3, not ' +
                                     str(args[1].shape[1]))

            for idx, one_label in enumerate(labels):
                self.chan.append(Chan(one_label, xyz[idx, :]))

    def __call__(self, func=None):
        """Return a new instance of Channels, with a subset of channels.

        Parameters
        ----------
        func : function
            function to execute on each instance of Chan, should return True or
            False (include the channel or not).

        Returns
        -------
        new instance of Channels
            new instance of Channels, but instances of Chan are not deep-copied

        """
        chans = []
        for one_chan in self.chan:
            if func(one_chan):
                chans.append(one_chan)

        return Channels(chans)

    def return_label(self):
        """Returns the labels for all the channels.

        Returns
        -------
        list of str
            list of the channel labels.

        """
        return [x.label for x in self.chan]

    def return_xy(self, labels=None):
        """Returns the location in xy for some channels.

        Parameters
        ----------
        labels : list of str, optional
            the names of the channels.

        Returns
        -------
        numpy.ndarray
            a 2xn vector with the position of a channel.

        Notes
        -----
        TODO

        """
        return None

    def return_xyz(self, labels=None):
        """Returns the location in xy for some channels.

        Parameters
        ----------
        labels : list of str, optional
            the names of the channels.

        Returns
        -------
        numpy.ndarray
            a 3xn vector with the position of a channel.

        """
        all_labels = self.return_label()

        if labels is None:
            labels = all_labels

        xyz = []
        for one_label in labels:
            idx = all_labels.index(one_label)
            xyz.append(self.chan[idx].xyz)

        return asarray(xyz)

    def return_attr(self, attr, labels=None):
        """return the attributes for each channels.

        Parameters
        ----------
        attr : str
            attribute specified in Chan.attr.keys()

        """
        all_labels = self.return_label()

        if labels is None:
            labels = all_labels

        all_attr = []
        for one_label in labels:
            idx = all_labels.index(one_label)
            try:
                all_attr.append(self.chan[idx].attr[attr])
            except KeyError:
                possible_attr = ', '.join(self.chan[idx].attr.keys())
                lg.debug('key "{}" not found, '.format(attr) +
                         'possible keys are {}'.format(possible_attr))
                all_attr.append(None)

        return all_attr

    def n_chan(self):
        """Returns the number of channels."""
        return len(self.chan)

    def export(self, elec_file):
        """Export channel name and location to file.

        Parameters
        ----------
        elec_file : str
            path to file where to save csv

        """
        ext = splitext(elec_file)[1]
        if ext == '.csv':
            export_csv(self, elec_file)


def assign_region_to_channels(channels, anat, approx=3):
    """Assign a brain region based on the channel location.

    Parameters
    ----------
    channels : instance of phypno.attr.chan.Channels
        channels to assign regions to
    anat : instance of phypno.attr.anat.Freesurfer
        anatomical information taken from freesurfer.
    chan_name : list of str, optional
        the channel name (if not specified, it uses them all)
    approx : int, optional
        approximation to define position of the electrode.

    Returns
    -------
    instance of phypno.attr.chan.Channels
        same instance as before, now Chan have attr 'region'

    """
    for one_chan in channels.chan:
        one_region, approx = anat.find_brain_region(one_chan.xyz)
        one_chan.attr.update({'region': one_region, 'approx': approx})

    return channels


def find_chan_in_region(channels, anat, region_name):
    """Find which channels are in a specific region.

    Parameters
    ----------
    channels : instance of phypno.attr.chan.Channels
        channels, that have locations
    anat : instance of phypno.attr.anat.Freesurfer
        anatomical information taken from freesurfer.
    region_name : str
        the name of the region, according to FreeSurferColorLUT.txt

    Returns
    -------
    chan_in_region : list of str
        list of the channels that are in one region.

    """
    if 'region' not in channels.chan[0].attr.keys():
        channels = assign_region_to_channels(channels, anat)

    chan_in_region = []
    for one_chan in channels.chan:
        if region_name in one_chan.attr['region']:
            chan_in_region.append(one_chan.label)

    return chan_in_region
