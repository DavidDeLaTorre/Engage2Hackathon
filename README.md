# Engage 2 Hackathon

## Information
This event will bring together new talents to the aviation industry for two days of intense collaboration and creativity. 
Participants will have the opportunity to tackle the industry’s digitalization challenge, 
featuring a 24-hour coding session to tackle proposed ATM-related challenges.

https://wikiengagektn.com/hackathons/

## Repository set-up
Once this repository has been cloned for the first time in a new machine, you need to sync all the submodules.
Launch these commands from the repository root directory:

```shell
git submodule init
git submodule sync
git submodule update
```

## Repository update
To pull (update) all git changes from this repository and all its submodules:

```bash
# First, update the main branch
git pull

# Then, update the submodules (recursively)
git submodule update --recursive --remote
```

## Python virtual environment

If your project uses Python, you will need to set up a virtual environment.
If you are using an IDE, it will take care of it.
If you are running this repo from a server, you will need to create it manually:

```bash
python3 -m venv venv
```

> This step only needs to be done once.

Then, each time you want to load the venv:

```bash
source venv/bin/activate
```

With the venv loaded, install any python requirements in your project:

```bash
pip3 install -r requirements.txt
```

---

## Detailed Technical Report on ADS‐B Parquet File

This report analyzes the sample Parquet file: 
`38bd94f6e9d049fd971369e17607c6ad.snappy.parquet`
which was inspected using a custom Python script. 
The file contains ADS‐B aircraft trajectory data and is one of many ~25MB files comprising a larger dataset.

---

### 1. File Metadata Overview

- **Total Rows:** 1,352,317  
  The dataset spans over 1.35 million rows, reflecting a high-frequency sampling typical in ADS‐B data streams.

- **Row Groups:** 2  
  - **Row Group 0:** 1,048,576 rows  
  - **Row Group 1:** 303,741 rows  
  Splitting the file into row groups supports efficient I/O and potential parallel processing during analysis.

- **Creator Information:**  
  Created by `parquet-cpp-arrow version 18.1.0`, which indicates the file was generated using Apache Arrow’s Parquet implementation.

- **Compression:**  
  The file name includes “snappy”, suggesting that Snappy compression is applied to reduce file size while 
  maintaining rapid decompression speeds.

---

### 2. Schema and Data Structure

The schema is defined as a required group containing 137 optional fields. This flexibility (with optional fields) 
is important since not all ADS‐B messages carry every type of information. The schema comprises:

- **Data Types:**
  - **BYTE_ARRAY:** Used for string-based fields (e.g., `df`, `squawk`, `icao24`, `callsign`, various `bds` fields).
  - **DOUBLE:** For numerical values such as airspeed (`bds60_IAS`, `bds60_Mach`), 
    altitude (`altitude`, `selected_altitude`), and positional information (`lat_deg`, `lon_deg`).
  - **INT64:** Used for timestamp data (`ts`).
  - **BOOLEAN:** For flags indicating operational statuses (e.g., `tcas_operational`, `autopilot`, `vnav_mode`, etc.).

- **Optional Nature of Fields:**  
  Every column is marked as optional, implying that many rows may contain nulls. 
  This design is common in ADS‐B datasets where not every transmission carries a full suite of parameters.

---

### 3. Detailed Field Analysis

#### Identification and Communication

- **icao24:**  
  Likely represents the unique 24-bit transponder address for each aircraft.
- **callsign:**  
  Indicates the flight identifier assigned to an aircraft.
- **squawk:**  
  Contains the squawk code, a four-digit code assigned by air traffic control.
- **df:**  
  Although defined as a binary string, its preview values (e.g., 21, 17, 20) suggest it might represent
  a numeric flag or data format identifier.

#### Navigation and Performance Parameters

- **Airspeed and Heading:**  
  Fields such as `bds60_heading`, `bds60_IAS` (Indicated Airspeed), and `bds60_Mach` provide information 
  on the aircraft’s direction and speed.
- **Altitude Information:**  
  Columns like `altitude`, `selected_altitude`, and `barometric_setting` are key for altitude tracking.
- **Positional Data:**  
  A set of fields (`lat_cpr`, `lon_cpr`, `lat_deg`, `lon_deg`) likely offers position information in both CPR 
  (Compact Position Reporting) and standard degree formats.
- **Groundspeed and Track:**  
  Fields such as `groundspeed` and `track` capture motion over the ground.

#### BDS (Binary Data Source) Fields

A significant portion of the schema is dedicated to various `bds`-prefixed fields:
  
- **bds60, bds40, bds45, bds50:**  
  These groups likely represent different types of ADS‐B messages or parameters extracted from Mode S transponder data. For example:
  - **bds60_bds, bds60_heading:**  
    Relate to airspeed and heading measurements.
  - **bds45_*** fields (e.g., `bds45_static_temperature`, `bds45_static_pressure`) hint at environmental 
    measurements or static aircraft parameters.
  - **bds50_*** fields provide additional performance metrics such as roll, track rate, and true airspeed (`bds50_TAS`).

- **bds10, bds17, bds44, bds30:**  
  These fields further subdivide into status flags and detailed sensor readings:
  - **bds10_*** flags (e.g., `bds10_config`, `bds10_mode_s`) indicate system configurations or operational statuses.
  - **bds17_*** series (e.g., `bds17_bds05`, `bds17_bds40`) likely capture specialized ADS‐B message segments.
  - **bds44_*** fields capture wind speed, direction, temperature, pressure, turbulence, and humidity.
  - **bds30_*** fields are Boolean flags that might indicate the issuance, termination, or multiplicity of certain message types.

#### Flight Control and System Status

Boolean fields indicate various system statuses:
  
- **tcas_operational, autopilot, vnav_mode, alt_hold, approach_mode, lnav_mode:**  
  These flags show whether specific systems (e.g., Traffic Collision Avoidance System, autopilot,  
  lateral/vertical navigation modes) are active.
  
- Additional fields such as `selected_heading`, `vertical_rate`, and `tc` provide dynamic operational metrics.

---

### 4. Row Group Storage and Encoding

- **Encoding Strategies:**  
  Most columns are encoded using `PLAIN_DICTIONARY` and `RLE` (Run-Length Encoding). 
  These are typical for Parquet files to compress repetitive or categorical data efficiently.

- **Row Group Details:**
  - **Row Group 0:**  
    Contains the majority (1,048,576 rows) of the dataset.
  - **Row Group 1:**  
    Contains 303,741 rows.  
  Using multiple row groups facilitates optimized parallel reads and efficient query performance in large-scale data processing.

---

### 5. Data Preview and Observations

The preview of the first 5 rows (across 137 columns) reveals:

- **Mixed Data Population:**  
  Some fields (e.g., `df`, `squawk`, `bds60_bds`) have populated values while many fields remain null. 
  This pattern is consistent with the optional nature of the schema.
  
- **Data Type Inconsistencies:**  
  Although `df` is stored as a binary string, its previewed values appear numeric. 
  This might require additional data cleaning or type conversion during downstream processing.
  
- **Sparse Population in ADS‐B Messages:**  
  Many of the specialized BDS fields are sparsely populated, which is common in ADS‐B datasets 
  since not all aircraft or messages will include the full range of optional parameters.

---
