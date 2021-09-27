# Yagi designer

This is a simple Python 3 + QT5 utility for designing Yagi-uda antennas. It is using `nec2c` for calculations, so ensure `nec2c` package is installed in your system.

Each element of the antenna is described by just three parameters:
* diameter (shared among all)
* position (front/back)
* end-to-end length

## Usage
`./yagi.py -e 3`

`-e` specifies number of antenna elements. `3` means Reflector, Driven Element and single Director.

Then, use your keyboard or mouse wheel to modify elements' lengths and positions, while observing antenna parameters in real time.
