# -*- readTomoControlPts -*-#
"""
SYNOPSIS
    Read Tomo plan and output control points

DESCRIPTION


EXAMPLES
    Show some examples of how to use this script.

VERSION 0.0
AUTHOR
    ch4jm on 1/2018

"""
import glob, os, re, sys
import pydicom as dcm
from numpy import average, max, nonzero, zeros

def main(dicomPlanFile):
    ds = dcm.read_file(dicomPlanFile)
    NCP = ds.BeamSequence[0].NumberOfControlPoints
    presPara = zeros((1,6))
    ctrPara = zeros((NCP, 4))
    ctrPts = zeros((NCP-1, 64))

    planType = ds.BeamSequence[0].BeamType
    print('Plan type is %s' %planType)
    target = re.search('of the (.*?) volume', ds.PrescriptionDescription)
    target = target.group(1)
    print('Plan volume is %s' %target)

    # prescription paramters
    # target dose, fractions, pitch, jaw size, total treatment time, modulation factor
    presPara = {}
    presPara['target dose'] = ds.FractionGroupSequence[0].ReferencedDoseReferenceSequence[0].TargetPrescriptionDose
    presPara['total fractions'] = ds.FractionGroupSequence[0].NumberOfFractionsPlanned
    pitch = re.search('Beam pitch (\d*\.\d+|\d+)', ds.BeamSequence[0].BeamDescription)
    presPara['pitch'] = float(pitch.group(1))
    fs = re.search('Field size (\d*\.\d+|\d+)', ds.BeamSequence[0].BeamDescription)
    presPara['jaw size'] = float(fs.group(1))
    presPara['treatment time'] = float(ds.FractionGroupSequence[0].ReferencedBeamSequence[0].BeamMeterset)*60

    # check if direct
    isdirect = ds.BeamSequence[0].ControlPointSequence[0].GantryRotationDirection == 'NONE'

    # control points
    if not isdirect:
        for kk in range(0,NCP-1):
            # control point #, gantry angle, z, MU
            ctrPara[kk, 0] = ds.BeamSequence[0].ControlPointSequence[kk].ControlPointIndex
            ctrPara[kk, 1] = ds.BeamSequence[0].ControlPointSequence[kk].GantryAngle
            ctrPara[kk, 2] = ds.BeamSequence[0].ControlPointSequence[kk].IsocenterPosition[2]
            ctrPara[kk, 3] = ds.BeamSequence[0].ControlPointSequence[kk].CumulativeMetersetWeight
            # LOTs %
            arrStr = ds.BeamSequence[0].ControlPointSequence[kk][0x300d, 0x10a7].value.decode('utf-8').split('\\')
            if arrStr[0] != '':
                for ll in range(0,63):
                    ctrPts[kk,ll] = float(arrStr[ll])
        ctrPara[NCP-1, 0] = ds.BeamSequence[0].ControlPointSequence[NCP-1].ControlPointIndex
        ctrPara[NCP-1, 1] = ds.BeamSequence[0].ControlPointSequence[NCP-1].GantryAngle
        ctrPara[NCP-1, 2] = ds.BeamSequence[0].ControlPointSequence[NCP-1].IsocenterPosition[2]
        ctrPara[NCP-1, 3] = ds.BeamSequence[0].ControlPointSequence[NCP-1].CumulativeMetersetWeight
    mf = max(ctrPts)/average(ctrPts[nonzero(ctrPts)])
    print('Modulation fator = %1.2f' %mf)
    presPara['modulation factor'] = mf

    return target, presPara, ctrPara, ctrPts

if __name__ == '__main__':
    file = sys.argv[1]
    ctrPts = main(file)