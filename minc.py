#!/usr/bin/env python
# -*- coding: utf-8 -*- 

# Synopsis: investigation of MINC support for Nipype.
# Author: Carlo Hamalainen <carlo@carlo-hamalainen.net>
#         http://carlo-hamalainen.net

from nipype.interfaces.base import (
    TraitedSpec,
    CommandLineInputSpec,
    CommandLine,
    File
)
import os

from nipype.interfaces.base import (traits, TraitedSpec, OutputMultiPath, File, isdefined)

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
    output_file = File(
                    desc='output file',
                    exists=True,)
    provenance_json = File(
                        desc='provenance file (json)',
                        exists=True,)
    provenance_provn = File(
                        desc='provenance file (provn)',
                        exists=True,)

class ConvertTask(CommandLine):
    input_spec  = ConvertInputSpec
    output_spec = ConvertOutputSpec
    cmd = 'mincconvert'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['output_file'] = self.inputs.output_file
       
        # FIXME provenance files end up the the current working directory, is this ok?
        outputs['provenance_json'] = os.path.join(os.getcwd(), 'provenance.json')
        outputs['provenance_provn'] = os.path.join(os.getcwd(), 'provenance.provn')

        return outputs

if __name__ == '__main__':
    c = ConvertTask(input_file='/home/carlo/tmp/foo.mnc', output_file='/tmp/foo.mnc', two=True, clobber=True, compression=3, chunk=2, template=True)
    print c.cmdline
    c.run()
