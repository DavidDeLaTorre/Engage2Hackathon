#!/usr/bin/env python3

import csv
from tools_prob import get_time, get_time_full

def main():
    # Replace with your actual file path
    #file_path = 'engage-hackaton-checkpoint/checkpoint_YourTeamName_option1.csv'
    #output_file = 'results/checkpoint_RAD_option2_new.csv'

    file_path = 'engage-hackaton-scenarios/predictions_YourTeamName.csv'
    output_file = 'results/predictions_RAD.csv'

    with open(file_path, mode='r', newline='') as infile, open(output_file, mode='w', newline='') as outfile:

        # Load the files, input and output
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames  # use original headers
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)

        # Write the headers
        writer.writeheader()

        # Per every case (row in the input file)
        for row in reader:
            # Header be like:
            # id_scenario,icao24,runway,seconds_to_threshold

            # Load the scenario (ex: scenario_00)
            input_file = f"engage-hackaton/samples/{row['id_scenario']}.parquet"
            # Load the icao24 code (ex: 484fde)
            icao24 = row['icao24']
            # Load the runways (ex: 14L/32R)
            # Need to split by the slash ("/") and check only the ones starting with 18 or 32
            runway_string = row['runway']
            runway_to_land = ""
            if not runway_string:
                continue  # skip if empty
            runways_split = runway_string.split('/')
            for runway in runways_split:
                if runway.startswith("18") or runway.startswith("32"):
                    # Once found, keep the runway, and leave
                    runway_to_land = runway
                    break

            # Ask the timer, to compute the runway
            landing_time = get_time(runway_to_land)

            # Save the value
            row['seconds_to_threshold'] = landing_time

            # Write the entire line to the output file
            writer.writerow(row)

if __name__ == '__main__':
    main()
