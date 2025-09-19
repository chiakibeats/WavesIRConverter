# Waves IR File (*.xps / *.wir) Converter
## Usage
`python wir_converter.py preset.xps`

`--help` option available

This script converts true stereo IR into 3 files: left part (L suffix), right part (R suffix), and original quad channel file 

## Gain Normalization
* `--normalize preset`

    Normalize gain based on preset value

* `--normalize sample`

    Normalize gain based on max sample amplitude (0.0 dB maximum)
