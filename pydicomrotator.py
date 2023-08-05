import click
import pydicom
import os
import numpy as np
import random
from pydicom.uid import UID
from time import strftime, localtime
from PIL import Image
from pydicom._storage_sopclass_uids import SecondaryCaptureImageStorage
from pydicom._uid_dict import UID_dictionary
import uuid

baseUID = '1.2.826.0.1.3680043.10.594'
ImplementationClassUID = '2.25.229451600072090404564544894284998027172'

def generateUID(_uuid=None):
    """Returns a new DICOM UID based on a UUID, as specified in CP1156 (Final)."""
    if _uuid is None:
        _uuid = uuid.uuid1()
    return "2.25.%i" % _uuid.int

def getPDCMUID(name):
    # print("{" + "\n".join("{}: {}".format(k, v) for k, v in dicom.UID.UID_dictionary.items()) + "}")
    return [k for k, v in UID_dictionary.items() if v[0] == name][0]

def getEmptyDataset(filename : str, uid : pydicom.uid.UID):
    file_meta = pydicom.dataset.Dataset()
    #file_meta.MediaStorageSOPClassUID = UID('1.2.840.10008.5.1.4.1.1.2')
    file_meta.MediaStorageSOPClassUID = getPDCMUID("CT Image Storage")
    file_meta.MediaStorageSOPInstanceUID = uid
    file_meta.ImplementationClassUID = ImplementationClassUID
    file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
    #ds = pydicom.dataset.FileDataset(filename, {}, file_meta=file_meta, preamble="\0"*128)
    preamble=b"\x00" * 128
    ds = pydicom.dataset.FileDataset(filename, {}, file_meta=file_meta, preamble=preamble)
    return ds

def genNewUID() -> str:
    dtFormat = "%d%m%Y%H%M%S"
    dtLine = strftime(dtFormat, localtime())
    uid = "%s.%s%2d" % (baseUID, dtLine, random.randint(100, 999))
    return uid

def createNewDataset(npData : np.ndarray, dataMeta : dict, target : str, template : pydicom.dataset.FileDataset) -> bool:
    if not os.path.isdir(target):
        os.mkdir(target)
    npNewData = npData.swapaxes(0, 2)
    #npNewData = npNewData.swapaxes(0, 1)
    #npNewData = npNewData.swapaxes(0, 2)
    npNewData = npNewData.swapaxes(1, 2)
    Rows = dataMeta['zLen']
    Cols = dataMeta['yLen']
    imgMax = dataMeta['xLen']
    spacing = [dataMeta['zSize'], dataMeta['ySize']]
    uid = genNewUID()
    print(npNewData.shape)
    #template.FrameOfReferenceUID = UID("%s.0" % (uid, ))
    #template.ReferencedImageSequence[0].ReferencedSOPInstanceUID = UID("%s.0" % (uid, ))
    ptBaseUID = generateUID()
    for i in range(imgMax):
        newName = "IM%03d.dcm" % (i, )
        sopInstanceUID = "%s.%i" % (ptBaseUID, i)
        template2 = getEmptyDataset(newName, sopInstanceUID)
        template2.SeriesInstanceUID = template.SeriesInstanceUID
        template2.StudyInstanceUID = template.StudyInstanceUID
        template2.Modality = "CT"
        template2.SOPClassUID = getPDCMUID("CT Image Storage")
        template2.Rows = Rows
        template2.Columns = Cols
        template2.PixelSpacing = spacing
        template2.SliceThickness = dataMeta['xSize']
        #template2.SOPClassUID = SecondaryCaptureImageStorage
        #template.file_meta = getEmptyDataset(newName, UID("%s.%s" % (uid, str(i))))
        #template2.FrameOfReferenceUID = UID("%s.0" % (uid, ))
        #template2.FrameOfReferenceUID = "%s.%i" % (ptBaseUID, 0)
    #template.ReferencedImageSequence[0].ReferencedSOPInstanceUID = UID("%s.0" % (uid, ))
        template2.SliceLocation = i * dataMeta['xSize']
        template2.ImagePositionPatient = [0.0, 0.0, i * dataMeta['xSize']]
        #template2.PatientPosition = [0.0, 0.0, i * dataMeta['xSize']]
        template2.PatientPosition = template.PatientPosition
        template2.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
        #template2.SOPInstanceUID = UID("%s.%s" % (uid, str(i)))
        #template2.SOPInstanceUID = getPDCMUID("CT Image Storage")
        template2.SOPInstanceUID = sopInstanceUID
        template2.ImageType = "ORIGINAL\SECONDARY\AXIAL"
        template2.SamplesPerPixel = 1
        template2.PhotometricInterpretation = "MONOCHROME2"
        template2.BitsAllocated = 16
        template2.BitsStored = 16
        template2.HighBit = 15
        template2.KVP = ""
        template2.AcquisitionNumber = ""
        template2.PixelRepresentation = template.PixelRepresentation

        template2.RescaleSlope = dataMeta['slope']
        template2.RescaleIntercept = dataMeta['intercept']
        #template.pixel_array = npData[i, :, :].tobytes()
        template2.PixelData = npNewData[i, :, :].tobytes()
        #template2.PixelData = Image.fromarray(npNewData[i, :, :]).tobytes()
        template2.save_as(os.path.join(target, newName), write_like_original=False)


    pass

def extractFeatures(flD : pydicom.dataset.FileDataset) -> dict:
    return { 
        'xLen' : int(flD.Rows), 
        'yLen': int(flD.Columns), 
        'xSize': float(flD.PixelSpacing[0]), 
        'ySize': float(flD.PixelSpacing[1]), 
        'zSize': float(flD.SliceThickness),
        'slope': float(flD.RescaleSlope),
        'intercept': float(flD.RescaleIntercept),
        }
 

@click.command()
@click.option("--input", default="./input", help="Input DICOM folder")
@click.option("--target", default="./target", help="Target DICOM folder")
@click.option("--dummy", default=1, help="Dummy swaping axis or do numerical calculations")
def runner(input : str,  target : str, dummy : bool):
    print("Dumping %s into %s" %(input, target, ))
    if '"' in input:
        input = input.replace("\"", "")
    if '"' in target:
        target = target.replace("\"", "")        
    isMetaSet = False
    datas = []
    zs = []
    dataMeta = {}
    template = None
    for flN in os.listdir(input):
        flD = pydicom.dcmread(os.path.join(input, flN), force=True)
        if "SOPClassUID" not in flD:
          continue
        if (("CT Image Storage" in str(flD.SOPClassUID)) or ("1.2.840.10008.5.1.4.1.1.2" in str(flD.SOPClassUID))):
            if not hasattr(flD, 'TransferSyntaxUID'):
                flD.TransferSyntaxUID = '1.2.840.10008.1.2'
            if not hasattr(flD.file_meta, 'TransferSyntaxUID'):
                flD.file_meta.TransferSyntaxUID = '1.2.840.10008.1.2'
            if not isMetaSet:
                dataMeta = extractFeatures(flD)     
                template = flD.copy()
                isMetaSet = True
            pos = float(flD.ImagePositionPatient[2])
            zs.append(pos)
            datas.append(flD.pixel_array)

        
    zs, datas = (list(x) for x in zip(*sorted(zip(zs, datas), key=lambda pair: pair[0])))

    npData = np.array(datas)
    print(npData.shape)
    print(type(template))
    #del template.file_meta
    dataMeta.update({'zLen': npData.shape[0]})


    if dummy:
        createNewDataset(npData, dataMeta, target, template)
    pass

if __name__ == '__main__':
    runner()