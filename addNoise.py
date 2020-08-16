# -*- addNoise.py -*-
"""
add gaussian noise to the data sets in the provided CT set
version 0.0
created on 6th Sep 2016

run command: addNoise dicomPath noiselevel or addNoise.main(dicomPath, noiselevel)
original dicom files will be replaced, so be careful.

@author: Becket Hui
"""
import dicom, glob, numpy, os, sys
from random import gauss

def main(dcmdir, noiselv):
    fList = glob.glob(os.path.join(dcmdir, '*'))
    for f in fList:
        ds = dicom.read_file(f)
        if hasattr(ds, 'PixelData'):
            imageandNoise = addNoise2Image(ds.pixel_array, noiselv, ds.pixel_array.dtype)
            if imageandNoise is not None:
                ds.PixelData = imageandNoise.tostring()
                ds.save_as(f)

def addNoise2Image(image, noise, dtype = 'uint16'):
    if not isinstance(image, numpy.ndarray):
        return
    imageandNoise = numpy.zeros(image.shape)
    for ii in range(0,image.shape[0]):
        for jj in range(0,image.shape[1]):
            imageandNoise[ii][jj] = gauss(image[ii][jj], noise*image[ii][jj])
    if dtype == 'float16':
        imageandNoise = numpy.float16(imageandNoise)
    elif dtype == 'float32':
        imageandNoise = numpy.float32(imageandNoise)
    elif dtype == 'float64':
        imageandNoise = numpy.float_(imageandNoise)
    elif dtype == 'int8':
        imageandNoise = numpy.int8(imageandNoise)
    elif dtype == 'int16':
        imageandNoise = numpy.int16(imageandNoise)
    elif dtype == 'int32':
        imageandNoise = numpy.int32(imageandNoise)
    elif dtype == 'uint8':
        imageandNoise = numpy.uint8(abs(imageandNoise))
    elif dtype == 'uint32':
        imageandNoise = numpy.uint32(abs(imageandNoise))
    else:
        imageandNoise = numpy.uint16(abs(imageandNoise))
    return imageandNoise

if __name__ == '__main__':
    dcmdir = sys.argv[1]
    noiselv = float(sys.argv[2])
    main(dcmdir, noiselv)
