cmake_minimum_required (VERSION 3.0)

project ("pydicomrotator" LANGUAGES Python)

find_package(Python COMPONENTS Interpreter REQUIRED)

set(INPUT_DICOM_DIR "Input DICOM folder" CACHE PATH)
set(TARGET_DICOM_DIR "Target DICOM folder" CACHE PATH)
set(DUMMY_MODE "Use Dummy Mode" CACHE BOOL OFF)

if(DUMMY_MODE)
add_custom_target(run1 ALL COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/pydicomrotator.py --input="${START_DICOM_DIR}" --target="${TARGET_DICOM_DIR}" --dummy=1)
else()
add_custom_target(run1 ALL COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/pydicomrotator.py --input="${START_DICOM_DIR}" --target="${TARGET_DICOM_DIR}" --dummy=0)
endif()