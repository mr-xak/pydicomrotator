import click
import pydicom
import os
import numpy as np
import random
from pydicom.uid import UID
from time import strftime, localtime
from PIL import Image
#from pydicom._storage_sopclass_uids import SecondaryCaptureImageStorage
from pydicom._uid_dict import UID_dictionary
import uuid
#from skimage.transform import resize
#import matplotlib.pyplot as plt

ImplementationClassUID = '2.25.229451600072090404564544894284998027172'

def generateUID(_uuid=None):
    """
    The function generates a new DICOM UID based on a UUID.
    
    :param _uuid: The `_uuid` parameter is an optional parameter that represents a UUID (Universally
    Unique Identifier). If no value is provided for `_uuid`, a new UUID will be generated using the
    `uuid.uuid1()` function
    :return: a new DICOM UID based on a UUID.
    """
    if _uuid is None:
        _uuid = uuid.uuid1()
    return "2.25.%i" % _uuid.int

def getPDCMUID(name):
    """
    The function `getPDCMUID` returns the UID corresponding to a given name from the `UID_dictionary`.
    
    :param name: The `name` parameter is a string that represents the name of a DICOM UID
    :return: the PDCM UID (Unique Identifier) associated with the given name.
    """
    # print("{" + "\n".join("{}: {}".format(k, v) for k, v in dicom.UID.UID_dictionary.items()) + "}")
    return [k for k, v in UID_dictionary.items() if v[0] == name][0]

def getEmptyDataset(filename : str, uid : pydicom.uid.UID):
    """
    The function `getEmptyDataset` creates an empty DICOM dataset with specified file meta information
    and returns it.
    
    :param filename: The filename parameter is a string that represents the name of the file that you
    want to create or modify. This file will be used to store the DICOM dataset
    :type filename: str
    :param uid: The `uid` parameter is a unique identifier for the SOP Instance. It is used to uniquely
    identify a specific instance of a DICOM object (e.g., an image or a series)
    :type uid: pydicom.uid.UID
    :return: a pydicom.dataset.FileDataset object.
    """
    file_meta = pydicom.dataset.Dataset()
    file_meta.MediaStorageSOPClassUID = getPDCMUID("CT Image Storage")
    file_meta.MediaStorageSOPInstanceUID = uid
    file_meta.ImplementationClassUID = ImplementationClassUID
    file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
    #ds = pydicom.dataset.FileDataset(filename, {}, file_meta=file_meta, preamble="\0"*128)
    preamble=b"\x00" * 128
    return pydicom.dataset.FileDataset(filename, {}, file_meta=file_meta, preamble=preamble)

def genNewUID() -> str:
    dtFormat = "%d%m%Y%H%M%S"
    dtLine = strftime(dtFormat, localtime())
    uid = "%s.%s%2d" % (baseUID, dtLine, random.randint(100, 999))
    return uid

def createNewDataset(npData : np.ndarray, dataMeta : dict, target : str, template : pydicom.dataset.FileDataset) -> bool:
    """
    The function `createNewDataset` takes in a numpy array, metadata, target directory, and a template
    DICOM file, and creates a new dataset by swapping axes, setting various DICOM attributes, and saving
    the new dataset as DICOM files in the target directory.
    
    :param npData: The parameter `npData` is a NumPy array containing the image data
    :type npData: np.ndarray
    :param dataMeta: The `dataMeta` parameter is a dictionary that contains metadata information about
    the dataset. It includes the following keys:
    :type dataMeta: dict
    :param target: The `target` parameter is the directory where the new dataset will be saved
    :type target: str
    :param template: The `template` parameter is an instance of the `pydicom.dataset.FileDataset` class.
    It represents a DICOM file that will be used as a template for creating new DICOM files
    :type template: pydicom.dataset.FileDataset
    """
    if not os.path.isdir(target):
        os.mkdir(target)
    npNewData = npData.swapaxes(0, 2)
    npNewData = npNewData.swapaxes(1, 2)
    Rows = dataMeta['zLen']
    Cols = dataMeta['yLen']
    imgMax = dataMeta['xLen']
    spacing = [dataMeta['zSize'], dataMeta['ySize']]
    #uid = genNewUID()
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
        template2.SliceLocation = i * dataMeta['xSize']
        template2.ImagePositionPatient = [0.0, 0.0, i * dataMeta['xSize']]
        template2.PatientPosition = template.PatientPosition
        template2.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
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
    """
    The function `extractFeatures` takes a pydicom dataset as input and returns a dictionary containing
    various extracted features from the dataset.
    
    :param flD: The parameter `flD` is a `pydicom.dataset.FileDataset` object. This object represents a
    DICOM file and contains various attributes and methods to access and manipulate the data within the
    file
    :type flD: pydicom.dataset.FileDataset
    :return: a dictionary containing various features extracted from the input pydicom dataset. The keys
    of the dictionary represent the names of the features, and the values represent the corresponding
    values extracted from the dataset.
    """
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
@click.option("--dummy", default=True, help="Dummy swaping axis or do numerical calculations")
def runner(input : str,  target : str, dummy : bool):
    """
    The `runner` function takes in an input directory containing DICOM files, sorts them based on their
    z-coordinate, resizes the images, and creates a new dataset in the target directory.
    
    :param input: The `input` parameter is a string that represents the directory path where the DICOM
    files are located. These DICOM files will be processed in the function
    :type input: str
    :param target: The `target` parameter in the `runner` function is a string that represents the
    target directory where the output will be saved
    :type target: str
    :param dummy: The `dummy` parameter is a boolean flag that determines whether to create a new
    dataset dummy. If `dummy` is `True`, a new dataset will be created using the `createNewDataset`
    function. If `dummy` is `False`, the data array will be resized first, and then `createNewDataset`
    called with updated data and meta.
    :type dummy: bool
    """
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
    else:
        npNewData = np.zeros((npData.shape[0], npData.shape[0], npData.shape[0]), dtype=npData.dtype)
        for i in range(npData.shape[0]):
            #npNewData[i, :, :] = resize(npData[i, :, :], (dataMeta['zLen'], dataMeta['zLen'], ))
            npNewData[i, :, :] = Image.fromarray(npData[i, :, :]).resize((dataMeta['zLen'], dataMeta['zLen'], ))
            # fig, ax = plt.subplots(ncols=2)
            # ax[0].imshow(npData[i, :, :], plt.cm.bone)
            # ax[1].imshow(npNewData[i, :, :], plt.cm.bone)
            # plt.show()
        dataMeta.update({'xLen': npData.shape[0], 'yLen': npData.shape[0], 
                        'xSize': dataMeta['xSize'] * npData.shape[1] / npData.shape[0],
                        'ySize': dataMeta['ySize'] * npData.shape[2] / npData.shape[0],
        })
        createNewDataset(npNewData, dataMeta, target, template)
    pass

if __name__ == '__main__':
    runner()