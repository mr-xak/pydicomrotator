import click
import pydicom
import os
import numpy as np
import random
from pydicom.uid import UID
from time import strftime, localtime
from PIL import Image
from pydicom._storage_sopclass_uids import SecondaryCaptureImageStorage

baseUID = '1.2.826.0.1.3680043.10.594'
ImplementationClassUID = '2.25.229451600072090404564544894284998027172'

def getEmptyDataset(filename : str, uid : pydicom.uid.UID):
    file_meta = pydicom.dataset.Dataset()
    file_meta.MediaStorageSOPClassUID = UID('1.2.840.10008.5.1.4.1.1.2')
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
    template.Rows = Rows
    template.Columns = Cols
    template.PixelSpacing = spacing
    template.SliceThickness = dataMeta['xSize']
    template.SOPClassUID = SecondaryCaptureImageStorage
    #template.FrameOfReferenceUID = UID("%s.0" % (uid, ))
    #template.ReferencedImageSequence[0].ReferencedSOPInstanceUID = UID("%s.0" % (uid, ))
    for i in range(imgMax):
        newName = "IM%03d.dcm" % (i, )
        #template.file_meta = getEmptyDataset(newName, UID("%s.%s" % (uid, str(i))))
        template.SliceLocation = i * dataMeta['xSize']
        template.ImagePositionPatient = [0, 0, i * dataMeta['xSize']]
        template.SOPInstanceUID = UID("%s.%s" % (uid, str(i)))
        #template.pixel_array = npData[i, :, :].tobytes()
        template.PixelData = Image.fromarray(npData[i, :, :]).tobytes()
        template.save_as(os.path.join(target, newName), write_like_original=False)


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
                template = flD
                isMetaSet = True
            pos = float(flD.ImagePositionPatient[2])
            zs.append(pos)
            datas.append(flD.pixel_array)

        
    zs, datas = (list(x) for x in zip(*sorted(zip(zs, datas), key=lambda pair: pair[0])))

    npData = np.array(datas)
    print(npData.shape)
    print(type(template))
    dataMeta.update({'zLen': npData.shape[0]})


    if dummy:
        createNewDataset(npData, dataMeta, target, template)
    pass

if __name__ == '__main__':
    runner()