from argparse import ArgumentParser
import xml.etree.ElementTree as ET
from pathlib import Path
import os
import soundfile as sf

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



def split_true_stereo_ir(wav_file):
    wav_path = Path(wav_file)
    with sf.SoundFile(str(wav_path), "r") as true_stereo_ir:
        left_ir = sf.SoundFile(str(wav_path.with_stem(wav_path.stem + " L")), "w",
                               samplerate = true_stereo_ir.samplerate,
                               channels = 2,
                               subtype = true_stereo_ir.subtype,
                               endian = true_stereo_ir.endian,
                               format = true_stereo_ir.format)
        right_ir = sf.SoundFile(str(wav_path.with_stem(wav_path.stem + " R")), "w",
                                samplerate = true_stereo_ir.samplerate,
                                channels = 2,
                                subtype = true_stereo_ir.subtype,
                                endian = true_stereo_ir.endian,
                                format = true_stereo_ir.format)
        samples = true_stereo_ir.read(dtype = "float32")
        left_ir.write(samples[0:, :2])
        right_ir.write(samples[0:, 2:])

        left_ir.close()
        right_ir.close()



def normalize_ir(wav_file, norm_factor = None):
    wav_path = Path(wav_file)
    with sf.SoundFile(str(wav_path), "r+") as ir_file:
        samples = ir_file.read(dtype = "float32")

        if norm_factor == None:
            norm_factor = abs(samples).max()

        samples /= norm_factor
        ir_file.seek(0)
        ir_file.write(samples)



def parse_xps(file_name, normalize):
    tree_root = ET.parse(file_name)
    preset_xml = tree_root.findall("./Preset")
    
    for preset in preset_xml:
        preset_name = preset.get("Name").replace("<", "").replace(">", "")
        print(f"Preset \"{preset_name}\" Found")

        for variation in preset.findall(".//PluginSpecific[@DataType='NoData']"):
            file_name_node = variation.find(".//Descriptor[@Name='IRFileNameFull']")
            ir_file_name = Path(file_name_node.text).name if file_name_node is not None else ""
            actual_location = list(Path(file_name).parent.glob("**/" + ir_file_name))[0]

            input_channel = int(variation.find(".//Descriptor[@Name='NumInChannels']").text)
            output_channel = int(variation.find(".//Descriptor[@Name='NumOutChannels']").text)
            
            # mono
            if input_channel == 1 and output_channel == 1:
                output_file = actual_location.with_name(preset_name + "_mono.wav")
                print(f"Process Mono...")
            # stereo
            elif input_channel == 1 and output_channel == 2:
                output_file = actual_location.with_name(preset_name + "_stereo.wav")
                print(f"Process Stereo...")
            # true stereo
            elif input_channel == 2 and output_channel == 2:
                output_file = actual_location.with_name(preset_name + "_true_stereo.wav")
                print(f"Process True Stereo...")
            # mono to binaural (proper usage is unknown)
            elif input_channel == 1 and output_channel == 3:
                output_file = actual_location.with_name(preset_name + "_mono_binaural.wav")
                print(f"Processing Mono Binaural...")
            # stereo to binaural (proper usage is unknown)
            elif input_channel == 2 and output_channel == 3:
                output_file = actual_location.with_name(preset_name + "_stereo_binaural.wav")
                print(f"Processing Stereo Binaural...")
            # not supported format
            # there is an another format like mono to surround (input = 1ch, output = 4ch)
            else:
                print(f"This format is not supported! (input = {input_channel}ch, output = {output_channel}ch)")
                continue

            convert_wir(actual_location, output_file)
            print("Done!")

            if normalize == "preset":
                norm_factor = float(variation.find(".//Descriptor[@Name='Norm']").text)
                print("Normalize Gain (Preset Based)...")
                print(f"Normalize Factor: {norm_factor}")
                normalize_ir(output_file, norm_factor)
                print("Done!")
            elif normalize == "sample":
                print("Normalize Gain (Sample Based)...")
                normalize_ir(output_file)
                print("Done!")
            
            # split true stereo IR file to left and right parts
            if input_channel == 2 and output_channel == 2:
                split_true_stereo_ir(output_file)



def main():
    parser = ArgumentParser(description = "Waves IR Converter")
    parser.add_argument("file_name", nargs = 1, metavar = "xps_file", help = "IR-L preset file(.xps)")
    parser.add_argument(
        "--normalize",
        type = str,
        choices = ["preset", "sample"],
        help = "Normalize IR samples | preset: Using \"Norm\" factor in preset file | sample: Normalize to 0.0 dB maximum")

    args = parser.parse_args()
    
    # get presets
    parse_xps(args.file_name[0], args.normalize)



if __name__ == "__main__":
    main()