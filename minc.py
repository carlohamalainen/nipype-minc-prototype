#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Synopsis: investigation of MINC support for Nipype.
# Author: Carlo Hamalainen <carlo@carlo-hamalainen.net>
#         http://carlo-hamalainen.net

# TODO Check exit-code behaviour of minc commands.

from nipype.interfaces.base import (
    TraitedSpec,
    CommandLineInputSpec,
    CommandLine,
    StdOutCommandLineInputSpec,
    StdOutCommandLine,
    File,
    InputMultiPath,
    traits,
)

import os

import warnings
warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)

def check_minc():
    return Info.version() is not None

def no_minc():
    return not check_minc()

class Info(object):
    """Handle MINC version information.

    version refers to the version of MINC on the system

    """

    @staticmethod
    def version():
        """Check for minc version on the system

        Parameters
        ----------
        None

        Returns
        -------
        version : str
           Version number as string or None if MINC not found

        """
        try:
            clout = CommandLine(command='mincinfo',
                                args='-version',
                                terminal_output='allatonce').run()
        except IOError:
            return None

        out = clout.runtime.stdout

        def read_program_version(s):
            if 'program' in s:
                return s.split(':')[1].strip()
            return None

        def read_libminc_version(s):
            if 'libminc' in s:
                return s.split(':')[1].strip()
            return None

        def read_netcdf_version(s):
            if 'netcdf' in s:
                return ' '.join(s.split(':')[1:]).strip()
            return None

        def read_hdf5_version(s):
            if 'HDF5' in s:
                return s.split(':')[1].strip()
            return None

        versions = {'minc':    None,
                    'libminc': None,
                    'netcdf':  None,
                    'hdf5':    None,
                   }

        for l in out.split('\n'):
            for (name, f) in [('minc',      read_program_version),
                              ('libminc',   read_libminc_version),
                              ('netcdf',    read_netcdf_version),
                              ('hdf5',      read_hdf5_version),
                             ]:
                if f(l) is not None: versions[name] = f(l)

        return versions

class ToRawInputSpec(StdOutCommandLineInputSpec):
    """
    For the MINC command minctoraw.
    """

    input_file = File(
                    desc='input file',
                    exists=True,
                    mandatory=True,
                    argstr='%s',
                    position=-2,)

    write_byte = traits.Bool(
                desc='Write out data as bytes',
                argstr='-byte',)

    write_short = traits.Bool(
                desc='Write out data as short integers',
                argstr='-short',)

    write_int = traits.Bool(
                desc='Write out data as 32-bit integers',
                argstr='-int',)

    write_long = traits.Bool(
                desc='Superseded by -int',
                argstr='-long',)

    write_float = traits.Bool(
                desc='Write out data as single precision floating-point values',
                argstr='-float',)

    write_double = traits.Bool(
                desc='Write out data as double precision floating-point values',
                argstr='-double',)

    write_signed = traits.Bool(
                desc='Write out signed data',
                argstr='-signed',)

    write_unsigned = traits.Bool(
                desc='Write out unsigned data',
                argstr='-unsigned',)

    write_range = traits.Tuple(
                traits.Float, traits.Float, argstr='-range %s %s',
                desc='Specify the range of output values\nDefault value: 1.79769e+308 1.79769e+308',) # FIXME minctoraw output is missing a negative?

    _xor_normalize = ('normalize', 'nonormalize',)

    normalize = traits.Bool(
                    desc='Normalize integer pixel values to file max and min',
                    argstr='-normalize',
                    xor=_xor_normalize,
                    mandatory=True)

    nonormalize = traits.Bool(
                    desc='Turn off pixel normalization',
                    argstr='-nonormalize',
                    xor=_xor_normalize,
                    mandatory=True)

class ToRawOutputSpec(TraitedSpec):
    # FIXME Not sure if I'm defining the outout specs correctly.

    output_file = File(
                    desc='output file',
                    exists=True,
                    genfile=True,)

class ToRawTask(StdOutCommandLine):
    input_spec  = ToRawInputSpec
    output_spec = ToRawOutputSpec
    cmd = 'minctoraw'

    def _gen_outfilename(self):
        """
        Convert foo.mnc to foo.raw.
        """
        return os.path.splitext(self.inputs.input_file)[0] + '.raw'

class ConvertInputSpec(CommandLineInputSpec):
    input_file = File(
                    desc='input file for converting',
                    exists=True,
                    mandatory=True,
                    argstr='%s',
                    position=-2,)

    output_file = File(
                    desc='output file',
                    mandatory=True,
                    genfile=False,
                    argstr='%s',
                    position=-1,)

    clobber = traits.Bool(
                desc='Overwrite existing file.',
                argstr='-clobber',)

    two = traits.Bool(
                desc='Create a MINC 2 output file.',
                argstr='-2',)

    template = traits.Bool(
                desc='Create a template file.',
                argstr='-template',)

    compression = traits.Enum(0, 1, 2, 3, 4, 5, 6, 7, 8, 9,
                            argstr='-compress %s',
                            desc='Set the compression level, from 0 (disabled) to 9 (maximum).',)

    chunk = traits.Trait(traits.TraitRange(0, None),
                        desc='Set the target block size for chunking (0 default, >1 block size).',
                        default=0,
                        usedefault=False,
                        argstr='-chunk %d',)

class ConvertOutputSpec(TraitedSpec):
    # FIXME Am I defining the output spec correctly?
    output_file = File(
                    desc='output file',
                    exists=True,)

class ConvertTask(CommandLine):
    input_spec  = ConvertInputSpec
    output_spec = ConvertOutputSpec
    cmd = 'mincconvert'

    def _list_outputs(self):
        # FIXME seems generic, is this necessary?
        outputs = self.output_spec().get()
        outputs['output_file'] = self.inputs.output_file
        return outputs

class CopyInputSpec(CommandLineInputSpec):
    """
    Implement minccopy? Its man page says:

        NOTE: This program is intended primarily for use with scripts such
        as mincedit.  It does not follow the typical design rules of most MINC
        command-line tools and therefore should be  used only with caution.

    It doesn't run on a standard MNC file, e.g.

        $ minccopy /home/carlo/tmp/foo.mnc /tmp/foo_copy.mnc
        (from miopen): Can't write compressed file
        ncvarid: ncid -1: NetCDF: Not a valid ID

    """

    input_file = File(
                    desc='input file to copy',
                    exists=True,
                    mandatory=True,
                    argstr='%s',
                    position=-2,)

    output_file = File(
                    desc='output file',
                    mandatory=True,
                    genfile=False,
                    argstr='%s',
                    position=-1,)

    pixel_values = traits.Bool(
                desc='Copy pixel values as is.',
                argstr='-pixel_values',)

    real_values = traits.Bool(
                desc='Copy real pixel intensities (default).',
                argstr='-real_values',
                usedefault=True,)

class CopyOutputSpec(TraitedSpec):
    # FIXME Am I defining the output spec correctly?
    output_file = File(
                    desc='output file',
                    exists=True,)

class CopyTask(CommandLine):
    input_spec  = CopyInputSpec
    output_spec = CopyOutputSpec
    cmd = 'minccopy'

    def _list_outputs(self):
        # FIXME seems generic, is this necessary?
        outputs = self.output_spec().get()
        outputs['output_file'] = self.inputs.output_file
        return outputs

class ToEcatInputSpec(CommandLineInputSpec):
    input_file = File(
                    desc='input file to convert',
                    exists=True,
                    mandatory=True,
                    argstr='%s',
                    position=-2,)

    output_file = File(
                    desc='output file',
                    mandatory=False,
                    genfile=True,
                    argstr='%s',
                    position=-1,)

    ignore_patient_variable = traits.Bool(
                    desc='Ignore informations from the minc patient variable.',
                    argstr='-ignore_patient_variable',)

    ignore_study_variable = traits.Bool(
                    desc='Ignore informations from the minc study variable.',
                    argstr='-ignore_study_variable',)

    ignore_acquisition_variable = traits.Bool(
                    desc='Ignore informations from the minc acquisition variable.',
                    argstr='-ignore_acquisition_variable',)

    ignore_ecat_acquisition_variable = traits.Bool(
                    desc='Ignore informations from the minc ecat_acquisition variable.',
                    argstr='-ignore_ecat_acquisition_variable',)

    ignore_ecat_main = traits.Bool(
                    desc='Ignore informations from the minc ecat-main variable.',
                    argstr='-ignore_ecat_main',)

    ignore_ecat_subheader_variable = traits.Bool(
                    desc='Ignore informations from the minc ecat-subhdr variable.',
                    argstr='-ignore_ecat_subheader_variable',)

    no_decay_corr_fctr = traits.Bool(
                    desc='Do not compute the decay correction factors',
                    argstr='-no_decay_corr_fctr',)

    voxels_as_integers = traits.Bool(
                    desc='Voxel values are treated as integers, scale and calibration factors are set to unity',
                    argstr='-label',)

class ToEcatOutputSpec(TraitedSpec):
    # FIXME Am I defining the output spec correctly?
    output_file = File(
                    desc='output file',
                    exists=True,)

class ToEcatTask(CommandLine):
    input_spec  = ToEcatInputSpec
    output_spec = ToEcatOutputSpec
    cmd = 'minctoecat'

    def _list_outputs(self):
        # FIXME seems generic, is this necessary?
        outputs = self.output_spec().get()
        outputs['output_file'] = self.inputs.output_file
        return outputs

    def _gen_filename(self, name):
        if name == 'output_file':
            return os.path.splitext(self.inputs.input_file)[0] + '.v'
        return None

class DumpInputSpec(StdOutCommandLineInputSpec):
    """
    For the MINC command mincdump.
    """

    input_file = File(
                    desc='input file',
                    exists=True,
                    mandatory=True,
                    argstr='%s',
                    position=-2,)

    _xor_coords_or_header = ('coordinate_data', 'header_data',)

    coordinate_data = traits.Bool(
                    desc='Coordinate variable data and header information',
                    argstr='-c',
                    xor=_xor_coords_or_header,)

    header_data = traits.Bool(
                    desc='Header information only, no data',
                    argstr='-h',
                    xor=_xor_coords_or_header,)

    _xor_annotations = ('annotations_brief', 'annotations_full',)

    # FIXME Instead of an enum, make a separate Bool trait called fortran_indices and another
    # called c_indices?

    annotations_brief = traits.Enum('c', 'f',
                            argstr='-b %s',
                            desc='Brief annotations for C or Fortran indices in data',
                            xor=_xor_annotations)

    annotations_full = traits.Enum('c', 'f',
                            argstr='-f %s',
                            desc='Full annotations for C or Fortran indices in data',
                            xor=_xor_annotations)

    variables = InputMultiPath(
                            traits.Str,
                            desc='Output data for specified variables only',
                            sep=',',
                            argstr='-v %s',)

    line_length = traits.Trait(traits.TraitRange(0, None),
                        desc='Line length maximum in data section (default 80)',
                        default=0,
                        usedefault=False,
                        argstr='-l %d',)

    netcdf_name = traits.Str(
                        desc='Name for netCDF (default derived from file name)',
                        argstr='-n %s',)

    precision = traits.Either(
                        traits.Int(),
                        traits.Tuple(traits.Int, traits.Int),
                        desc='Display floating-point values with less precision',
                        argstr='%s',)

class DumpOutputSpec(TraitedSpec):
    # FIXME Not sure if I'm defining the outout specs correctly.

    output_file = File(
                    desc='output file',
                    exists=True,
                    genfile=True,)

class DumpTask(StdOutCommandLine):
    input_spec  = DumpInputSpec
    output_spec = DumpOutputSpec
    cmd = 'mincdump'

    def _format_arg(self, name, spec, value):
        if name == 'precision':
            if isinstance(value, int):
                return '-p %d' % value
            elif isinstance(value, tuple):
                return '-p %d,%d' % (value[0], value[1],)
            else:
                raise NotImplemented # FIXME some other exception?
        return super(DumpTask, self)._format_arg(name, spec, value)

    # FIXME Are we forced to send outout to a file? Can we pipe it
    # to another minc command directly?
    def _gen_outfilename(self):
        """
        Dump foo.mnc to foo.txt.
        """
        return os.path.splitext(self.inputs.input_file)[0] + '.txt'

class AverageInputSpec(CommandLineInputSpec):
    input_files = InputMultiPath(
                    traits.File,
                    desc='input file(s) for averaging',
                    exists=True,
                    mandatory=True,
                    sep=' ', # FIXME test with files that contain spaces - does InputMultiPath do the right thing?
                    argstr='%s',
                    position=-2,) # FIXME test with multiple files, is order ok?

    output_file = File(
                    desc='output file',
                    mandatory=True,
                    genfile=False,
                    argstr='%s',
                    position=-1,)

    two = traits.Bool(desc='Produce a MINC 2.0 format output file', argstr='-2')

    _xor_clobber = ('clobber', 'no_clobber')

    clobber     = traits.Bool(desc='Overwrite existing file.',                  argstr='-clobber',      xor=_xor_clobber)
    no_clobber  = traits.Bool(desc='Don\'t overwrite existing file (default).', argstr='-noclobber',    xor=_xor_clobber)

    _xor_verbose = ('verbose', 'quiet',)

    verbose = traits.Bool(desc='Print out log messages (default).', argstr='-verbose',  xor=_xor_verbose)
    quiet   = traits.Bool(desc='Do not print out log messages.',    argstr='-quiet',    xor=_xor_verbose)

    debug   = traits.Bool(desc='Print out debugging messages.', argstr='-debug')

    # FIXME How to handle stdin option here? Not relevant?
    foo = traits.File(desc='Specify the name of a file containing input file names (- for stdin).', argstr='-filelist %s',)

    _xor_check_dimensions = ('check_dimensions', 'no_check_dimensions',)

    check_dimensions    = traits.Bool(desc='Check that dimension info matches across files (default).', argstr='-check_dimensions',     xor=_xor_check_dimensions)
    no_check_dimensions = traits.Bool(desc='Do not check dimension info.',                              argstr='-nocheck_dimensions',   xor=_xor_check_dimensions)


    # FIXME mincaverage seems to accept more than one of these options; I assume
    # that it takes the last one, and it makes more sense for these to be
    # put into an xor case.

    _xor_format = ('format_filetype', 'format_byte', 'format_short',
                   'format_int', 'format_long', 'format_float', 'format_double',
                   'format_signed', 'format_unsigned',)

    format_filetype     = traits.Bool(desc='Use data type of first file (default).',                    argstr='-filetype', xor=_xor_format)
    format_byte         = traits.Bool(desc='Write out byte data.',                                      argstr='-byte',     xor=_xor_format)
    format_short        = traits.Bool(desc='Write out short integer data.',                             argstr='-short',    xor=_xor_format)
    format_int          = traits.Bool(desc='Write out 32-bit integer data.',                            argstr='-int',      xor=_xor_format)
    format_long         = traits.Bool(desc='Superseded by -int.',                                       argstr='-long',     xor=_xor_format)
    format_float        = traits.Bool(desc='Write out single-precision floating-point data.',           argstr='-float',    xor=_xor_format)
    format_double       = traits.Bool(desc='Write out double-precision floating-point data.',           argstr='-double',   xor=_xor_format)
    format_signed       = traits.Bool(desc='Write signed integer data.',                                argstr='-signed',   xor=_xor_format)
    format_unsigned     = traits.Bool(desc='Write unsigned integer data (default if type specified).',  argstr='-unsigned', xor=_xor_format) # FIXME mark with default=?


    max_buffer_size_in_kb = traits.Trait(traits.TraitRange(0, None),
                                desc='Specify the maximum size of the internal buffers (in kbytes).',
                                default=4096, # FIXME is this doing what I think it's doing? Write some tests.
                                usedefault=False,
                                argstr='-max_buffer_size_in_kb %d',)

    _xor_normalize = ('normalize', 'nonormalize',)
    normalize   = traits.Bool(desc='Normalize data sets for mean intensity.', argstr='-normalize', xor=_xor_normalize)
    nonormalize = traits.Bool(desc='Do not normalize data sets (default).',   argstr='-nonormalize', xor=_xor_normalize, default=True) # FIXME check default=? behaviour

    voxel_range = traits.Tuple(
                traits.Int, traits.Int, argstr='-range %d %d',
                desc='Valid range for output data.',)

    sdfile = traits.File(
                desc='Specify an output sd file (default=none).',
                argstr='-sdfile %s',)

    _xor_copy_header = ('copy_header, no_copy_header')

    copy_header     = traits.Bool(desc='Copy all of the header from the first file (default for one file).',            argstr='-copy_header',   xor=_xor_copy_header)
    no_copy_header  = traits.Bool(desc='Do not copy all of the header from the first file (default for many files)).',  argstr='-nocopy_header', xor=_xor_copy_header)

    avgdim = traits.Str(desc='Specify a dimension along which we wish to average.', argstr='-avgdim %s')

    binarize = traits.Bool(desc='Binarize the volume by looking for values in a given range.', argstr='-binarize')

    binrange = traits.Tuple(
                traits.Float, traits.Float, argstr='-binrange %s %s',
                desc='Specify a range for binarization. Default value: 1.79769e+308 -1.79769e+308.') # FIXME shouldn't that be -1.79769e+308 1.79769e+308? Min then max?

    binvalue = traits.Float(desc='Specify a target value (+/- 0.5) for binarization. Default value: -1.79769e+308', argstr='-binvalue %s')
		
    weights = InputMultiPath(
                            traits.Str,
                            desc='Specify weights for averaging ("<w1>,<w2>,...").',
                            sep=',',
                            argstr='-weights %s',)

    width_weighted = traits.Bool(desc='Weight by dimension widths when -avgdim is used.', argstr='-width_weighted', requires=('avgdim',))

class AverageOutputSpec(TraitedSpec):
    # FIXME Am I defining the output spec correctly?
    output_file = File(
                    desc='output file',
                    exists=True,)

class AverageTask(CommandLine):
    input_spec  = AverageInputSpec
    output_spec = AverageOutputSpec
    cmd = 'mincaverage'

    def _list_outputs(self):
        # FIXME seems generic, is this necessary?
        outputs = self.output_spec().get()
        outputs['output_file'] = self.inputs.output_file
        return outputs


if __name__ == '__main__':
    convert = ConvertTask(input_file='/home/carlo/tmp/foo.mnc', output_file='/tmp/foo.mnc', two=True, clobber=True, compression=3, chunk=2, template=True)
    print convert.cmdline
    convert_result = convert.run()

    print
    print

    toraw = ToRawTask(input_file='/home/carlo/tmp/foo.mnc', normalize=True)
    print toraw.cmdline
    toraw.run()

    print
    print

    copy = CopyTask(input_file='/home/carlo/tmp/foo.mnc', output_file='/tmp/foo_copy.mnc')
    print copy.cmdline
    # FIXME minccopy fails on my sample file...

    print
    print

    toecat1 = ToEcatTask(input_file='/home/carlo/tmp/foo.mnc', ignore_patient_variable=True) # output not specified, uses _gen_filename()
    print toecat1.cmdline

    toecat2 = ToEcatTask(input_file='/home/carlo/tmp/foo.mnc', output_file='/tmp/sdfsdf.v') # output_file specified
    print toecat2.cmdline

    print
    print

    dump1 = DumpTask(input_file='/home/carlo/tmp/foo.mnc', precision=(3,4), line_length=34, variables=['image'],)
    print dump1.cmdline
    dump1.run()

    print
    print

    average1 = AverageTask(input_files=['/home/carlo/tmp/foo.mnc', '/home/carlo/tmp/foo.mnc'], output_file='/home/carlo/tmp/foo_averaged.mnc', width_weighted=True, avgdim='image', binvalue=-1.123123213e+200)
    print average1.cmdline


