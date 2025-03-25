import xml.etree.ElementTree as ET
from FAP_positions import FAP_position
from threshold_positions import threshold_position

def main():
    FAP_file = "output/FAP_threshold_positions.kml"

    # Create the KML root
    kml = ET.Element('kml', xmlns="http://www.opengis.net/kml/2.2")
    document = ET.SubElement(kml, 'Document')

    def add_placemark(parent, name, lat, lon, altitude=None):
        placemark = ET.SubElement(parent, 'Placemark')
        ET.SubElement(placemark, 'name').text = name
        point = ET.SubElement(placemark, 'Point')
        coord_text = f"{lon},{lat}"
        if altitude is not None:
            coord_text += f",{altitude}"
        ET.SubElement(point, 'coordinates').text = coord_text

    # Add FAPs
    for rwy, fap in FAP_position.items():
        add_placemark(document, f"FAP {rwy}", fap.latitude, fap.longitude, fap.altitude)

    # Add Thresholds
    for rwy, threshold in threshold_position.items():
        add_placemark(document, f"Threshold {rwy}", threshold.latitude, threshold.longitude)

    # Convert to XML string
    tree = ET.ElementTree(kml)
    tree.write(FAP_file, encoding='utf-8', xml_declaration=True)

    print("KML file 'runways.kml' created successfully.")





if __name__ == '__main__':
    main()