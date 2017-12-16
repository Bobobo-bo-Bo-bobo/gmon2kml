#!/usr/bin/env python

import sys
import xml.dom.minidom


def kml_content(w):
    """
    Generate KML content from dictionary
    :param w: dictionary
    :return: string
    """
    result = """<?xml version="1.0" encoding="UTF-8"?>
    <kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
    <Style id="open">
        <IconStyle>
            <Icon>
                <href>icons/open.png</href>
            </Icon>
        </IconStyle>
    </Style>
    <Style id="wep">
        <IconStyle>
            <Icon>
                <href>icons/wep.png</href>
            </Icon>
        </IconStyle>
    </Style>
    <Style id="wpapsk">
        <IconStyle>
            <Icon>
                <href>icons/wpapsk.png</href>
            </Icon>
        </IconStyle>
    </Style>
    <Style id="wpa2">
        <IconStyle>
            <Icon>
                <href>icons/wpa2.png</href>
            </Icon>
        </IconStyle>
    </Style>
    <Style id="unknown">
        <IconStyle>
            <Icon>
                <href>icons/unknown.png</href>
            </Icon>
        </IconStyle>
    </Style>
    """

    for bssid in w:
        placemark = xml.dom.minidom.Element("Placemark")
        name = xml.dom.minidom.Element("name")
        description = xml.dom.minidom.Element("description")
        point = xml.dom.minidom.Element("Point")
        coord = xml.dom.minidom.Element("coordinates")

        # name is SSID
        ntext = xml.dom.minidom.Text()
        ntext.data = w[bssid]["ssid"]

        # coordinates
        ctext = xml.dom.minidom.Text()
        ctext.data = "%s,%s" % (w[bssid]["lon"], w[bssid]["lat"])

        # description
        dtext = xml.dom.minidom.Text()
        dtext.data = """
<table style="width:100%%">
    <tr>
        <th><b>SSID</b></th>
        <th>%s</th>
    </tr>
    <tr>
        <td><b>BSSID</b></td>
        <td>%s</td>
    </tr>
    <tr>
        <td><b>Encryption</b></td>
        <td><b>%s</b></td>
    </tr>
    <tr>
        <td><b>Channel</b></td>
        <td>%s</td>
    </tr>
    <tr>
        <td><b>Seen</b></td>
        <td>%s %s</td>
    </tr>
</table>
""" % (w[bssid]["ssid"], bssid, w[bssid]["crypt"], w[bssid]["channel"], w[bssid]["date"], w[bssid]["time"])

        style = xml.dom.minidom.Element("styleUrl")
        stext = xml.dom.minidom.Text()

        if w[bssid]["crypt"] == "Open":
            stext.data = "#open"
        elif w[bssid]["crypt"] == "Wep":
            stext.data = "#wep"
        elif w[bssid]["crypt"] == "WpaPsk":
            stext.data = "#wpapsk"
        elif w[bssid]["crypt"] == "WPA2":
            stext.data = "#wpa2"
        else:
            stext.data = "#unknown"

        coord.appendChild(ctext)
        description.appendChild(dtext)
        name.appendChild(ntext)
        point.appendChild(coord)
        style.appendChild(stext)

        placemark.appendChild(style)
        placemark.appendChild(name)
        placemark.appendChild(description)
        placemark.appendChild(point)

        result += placemark.toxml()

    result += """    </Document>
</kml>"""

    return result


def usage():
    """
    Show usage information.
    :return: None
    """
    print("""Usage: %s <input>
    
    Read data from G-Mon input file <input> in CSV format and output KML data to stdout.
    
    """ % (sys.argv[0], ))


def read_gmon_csv(f):
    """
    Read CSV data from file
    :param f: input file
    :return: list of lines
    """
    sys.stderr.write("Reading %s ... " % (f, ))
    try:
        fd = open(sys.argv[1], "r")
        raw = fd.readlines()
        fd.close()
    except IOError as ioe:
        sys.stderr.write("FAILED, %s\n" % (ioe.strerror, ))
        return None

    sys.stderr.write("OK\n")
    return raw


def parse_gmon_csv(data, header=True):
    """
    Parse G-Mon CSV data
    :param data: list of lines
    :param header: first line is header information
    :return: dictionary of parsed data with BSSID as key
    """
    __data = {
        "lat": None,
        "lon": None,
        "ssid": None,
        "crypt": None,
        "beacon interval": None,
        "connection mode": None,
        "channel": None,
        "rxl": None,
        "date": None,
        "time": None,
    }

    result = {}
    if header:
        raw = data[1:]
    else:
        raw = data
        
    sys.stderr.write("Parsing data ... ")
    for line in raw:
        bssid, lat, lon, ssid, crypt, bint, cmode, chan, rxl, gdate, gtime = line.split(";", 10)
        if bssid not in result:
            result[bssid] = __data.copy()

        result[bssid]["lat"] = lat
        result[bssid]["lon"] = lon
        result[bssid]["ssid"] = ssid
        result[bssid]["crypt"] = crypt
        result[bssid]["beacon interval"] = bint
        result[bssid]["connection mode"] = cmode
        result[bssid]["channel"] = chan
        result[bssid]["rxl"] = rxl
        result[bssid]["date"] = gdate
        result[bssid]["time"] = gtime

    sys.stderr.write("OK, %u entries added\n" % (len(result), ))

    return result


def remove_no_coords(w):
    """
    Remove entries without coordinates
    :param w: dictionary
    :return: dictionary
    """
    sys.stderr.write("Removing entries without coordinates ... ")
    # we can't modify the dict we are working on, so we remember the keys to remove and remove them afterwards
    bssid_remove = set()
    for bssid in w:
        if w[bssid]["lat"] == "NaN" or w[bssid]["lon"] == "NaN":
            bssid_remove.add(bssid)

    for bssid in bssid_remove:
        w.pop(bssid)

    sys.stderr.write("OK, %u entries removed\n" % (len(bssid_remove),))
    return w


def remove_empty_ssid(w):
    """
    Remove entries with empty SSID
    :param w: dict
    :return: dict
    """
    sys.stderr.write("Removing entries without SSID ... ")
    bssid_remove = set()
    for bssid in w:
        if w[bssid]["ssid"] == "":
            bssid_remove.add(bssid)

    for bssid in bssid_remove:
        w.pop(bssid)

    sys.stderr.write("OK, %u entries removed\n" % (len(bssid_remove), ))
    return w


if __name__ == "__main__":
    if len(sys.argv) != 2:
        usage()
        sys.exit(1)

    wlan = {}
    raw_wlan = read_gmon_csv(sys.argv[1])

    if raw_wlan is None:
        sys.exit(1)

    if len(raw_wlan) == 0:
        sys.exit(0)

    if raw_wlan[0].strip() == "BSSID;LAT;LON;SSID;Crypt;Beacon Interval;Connection Mode;Channel;RXL;Date;Time":
        has_header = True
    else:
        has_header = False

    wlan = parse_gmon_csv(raw_wlan, header=has_header)
    wlan = remove_no_coords(wlan)
    wlan = remove_empty_ssid(wlan)

    kml = kml_content(wlan)
    sys.stdout.write(kml)

    sys.exit(0)
