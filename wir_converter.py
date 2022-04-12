from argparse import ArgumentParser
import xml.etree.ElementTree as ET
from pathlib import Path
import os



def convert_wir(wir_file, output_file):
    with open(wir_file, "rb") as ir_data:
        data_bytes = bytearray(ir_data.read(os.path.getsize(wir_file)))
        data_view = memoryview(data_bytes)
        # restore chunk header
        data_view[0:4] = b'RIFF'
        data_view[8:12] = b'WAVE'

        # modify bits per sample
        # original is 23(0x17)...why?
        data_view[34] = 32

        data_view.release()

        # write to output file
        with open(output_file, "wb") as wav_file:
            wav_file.write(data_bytes)



def parse_xps(file_name):
    tree_root = ET.parse(file_name)
    preset_xml = tree_root.findall("./Preset")
    
    for preset in preset_xml:
        preset_name = preset.get("Name")
        print(f"Preset \"{preset_name}\" Found")

        for variation in preset.findall(".//PluginSpecific[@DataType='NoData']"):
            ir_file_name = Path(variation.find(".//Descriptor[@Name='IRFileNameFull']").text).name
            actual_location = list(Path(file_name).parent.glob("**/" + ir_file_name))[0]

            input_channel = int(variation.find(".//Descriptor[@Name='NumInChannels']").text)
            output_channel = int(variation.find(".//Descriptor[@Name='NumOutChannels']").text)
            
            # mono to mono
            if input_channel == 1 and output_channel == 1:
                output_file = actual_location.with_name(preset_name + "_mono.wav")
                print(f"Process Mono...", end = "")
            # mono to stereo
            elif input_channel == 1 and output_channel == 2:
                output_file = actual_location.with_name(preset_name + "_stereo.wav")
                print(f"Process Stereo...", end = "")
            # stereo to stereo
            elif input_channel == 2 and output_channel == 2:
                output_file = actual_location.with_name(preset_name + "_true_stereo.wav")
                print(f"Process True Stereo...", end = "")
            
            convert_wir(actual_location, output_file)

            print("Done!")



def main():
    parser = ArgumentParser(description = "Waves IR Converter")
    parser.add_argument("file_name", nargs = 1, metavar = "xps_file", help = "IR-L preset file(.xps)")

    args = parser.parse_args()
    
    # get presets
    parse_xps(args.file_name[0])



if __name__ == "__main__":
    main()