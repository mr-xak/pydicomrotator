cmake_minimum_required (VERSION 3.0)

project ("pydicomrotator")

find_package(Python COMPONENTS Interpreter REQUIRED)

set(INPUT_DICOM_DIR "" CACHE PATH "Input DICOM folder")
set(TARGET_DICOM_DIR "" CACHE PATH "Target DICOM folder")
set(DUMMY_MODE OFF CACHE BOOL "Use DUMMY mode")

if(DUMMY_MODE)
add_custom_target(run1 ALL COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/pydicomrotator.py --input="${INPUT_DICOM_DIR}" --target="${TARGET_DICOM_DIR}" --dummy=1)
else()
add_custom_target(run1 ALL COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/pydicomrotator.py --input="${INPUT_DICOM_DIR}" --target="${TARGET_DICOM_DIR}" --dummy=0)
endif()