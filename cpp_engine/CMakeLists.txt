cmake_minimum_required(VERSION 3.20)
project(spia_engine VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

find_package(pybind11 REQUIRED)
find_package(Boost REQUIRED COMPONENTS graph)

file(GLOB_RECURSE SPIA_SOURCES
    src/*.cpp
)

pybind11_add_module(spia_engine
    ${SPIA_SOURCES}
)

target_include_directories(spia_engine PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${Boost_INCLUDE_DIRS}
)

target_link_libraries(spia_engine PRIVATE
    ${Boost_LIBRARIES}
)

if(MSVC)
    target_compile_options(spia_engine PRIVATE /W4 /O2)
else()
    target_compile_options(spia_engine PRIVATE -Wall -Wextra -O3)
endif()
