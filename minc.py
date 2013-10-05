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
    traits,
)

import os

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
                traits.Float, traits.Float, argstr='-range %f %f', # FIXME check if %f is appropriate
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

if __name__ == '__main__':
    convert = ConvertTask(input_file='/home/carlo/tmp/foo.mnc', output_file='/tmp/foo.mnc', two=True, clobber=True, compression=3, chunk=2, template=True)
    print convert.cmdline
    convert.run()

    print
    print

    toraw = ToRawTask(input_file='/home/carlo/tmp/foo.mnc', normalize=True)
    print toraw.cmdline
    toraw.run()

    print
    print

    copy = CopyTask(input_file='/home/carlo/tmp/foo.mnc', output_file='/tmp/foo_copy.mnc')
    print copy.cmdline

