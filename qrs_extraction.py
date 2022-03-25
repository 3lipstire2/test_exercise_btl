import argparse
import json
import xmltodict
import numpy as np

from typing import Dict, List, Tuple


def extract_qrs_borders(events: List) -> List[Tuple[int, int]]:
    """
    Extracts qrs borders from array of tick events, converts them from 2000Hz frequency to 500 Hz frequency
    """
    borders = []
    for event in events:
        offset = int(event['@tickOffset'])

        common_lead = [lead for lead in event['leadValues'] if lead['@lead'] == 'Common'][0]
        qrs_on = int([x['#text'] for x in common_lead['value'] if 'QRS_TimeOn' in x['@name']][0])
        qrs_off = int([x['#text'] for x in common_lead['value'] if 'QRS_TimeOff' in x['@name']][0])

        qrs_on_absolute_2000Hz = offset + qrs_on
        qrs_off_absolute_2000Hz = (offset + qrs_off)

        qrs_on_absolute_500Hz = qrs_on_absolute_2000Hz//4
        qrs_off_absolute_500Hz = qrs_off_absolute_2000Hz//4
        borders.append((qrs_on_absolute_500Hz, qrs_off_absolute_500Hz))

    return borders


def extract_leads(waves: Dict) -> Dict[str, np.ndarray]:
    """
    Extracts signal from lead and converts it to np array
    """
    return {wave['@lead']: np.fromstring(wave['#text'], sep=" ") for wave in waves}


def cut_qrs_segments(leads: Dict[str, np.ndarray], borders: List[Tuple[int, int]]) -> Dict[str, List[List[float]]]:
    """
    Cuts qrs segments from lead signals
    """
    segments = {}
    for lead_name, wave in leads.items():
        segments[lead_name] = [wave[start:end].tolist() for start, end in borders]

    return segments


def main():
    """The script extracts QRSon-QRSoff segments from ECG file

    Run
        python3 qrs_extraction.py --input-file <PATH-TO-INPUT-FILE> --output-file <PATH-TO-OUTPUT-FILE>
    """
    parser = argparse.ArgumentParser(
        description="Extracts and prints QRSonn-QRSoff parts of signal",
    )

    parser.add_argument("--input-file", dest="input_file", help="Path to input file")
    parser.add_argument("--output-file", dest="output_file", help="Paht to output file")

    args = parser.parse_args()

    with open(args.input_file, "rb") as input_file:
        input_data = xmltodict.parse(input_file)

    analysis = input_data["exportHeader"]["patient"]["examination"]["analysis"]

    borders = extract_qrs_borders(analysis['blockExtended']['eventTable']['event'])
    leads = extract_leads(analysis['blockExtended']['signal']['wave'])
    segments = cut_qrs_segments(leads, borders)

    with open(args.output_file, 'w') as output_file:
        json.dump(segments, output_file, indent=4)


if __name__ == "__main__":
    main()
