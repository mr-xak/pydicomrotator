# pydicomrotator

Short script to swap (rotate) axes on DICOM CT series. Reads folder containg multiple CT Image Storage SOPClassUIDs, rearranging axes Z -> X and making new CT Image Storages for each slice along new Z.


Run as following
```
python pydicomrotator.py --input=D:\\inputDicomFolder --target=D:\\targetDicomFolder --dummy=0
```

* Option dummy=0 will resize each image (Num of slices, Rows, Columns) to (Num of slices, Num of slices, Num of slices) first and than store the resulted cube as separated images, PixelSpacing will be rescaled approprietly in each direction

* Option dummy=1 will create Rows files each having [Num of slices, Columns] frame, PixelSpacing and SliceThickness are numerically overwritten.
