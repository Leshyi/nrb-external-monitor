
import socket
import struct
from datetime import datetime, timezone

TARGET = "103.231.179.50"
PORT = 123
TIMEOUT = 5


def check_ntp():
    print("NRB External NTP Monitor")
    print("Time:", datetime.now(timezone.utc).isoformat())
    print(f"Target: {TARGET}:{PORT}/UDP")

    # NTP request: LI=0, VN=4, Mode=3 (client)
    request = bytearray(48)
    request[0] = 0x23

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(TIMEOUT)
            sock.sendto(request, (TARGET, PORT))

            response, address = sock.recvfrom(512)

        if len(response) < 48:
            print("NTP: INVALID RESPONSE")
            print("Received bytes:", len(response))
            return

        first_byte = response[0]
        leap = (first_byte >> 6) & 0x03
        version = (first_byte >> 3) & 0x07
        mode = first_byte & 0x07
        stratum = response[1]

        print("Response from:", address[0])
        print("Packet length:", len(response))
        print("NTP version:", version)
        print("Mode:", mode)
        print("Stratum:", stratum)
        print("Leap indicator:", leap)

        if mode != 4:
            print("NTP: INVALID SERVER MODE")
            return

        if stratum == 0:
            print("NTP: RATE LIMITED OR DENIED (Kiss-o'-Death)")
            return

        if stratum > 15:
            print("NTP: INVALID STRATUM")
            return

        print("NTP: OK - valid server response")

    except socket.timeout:
        print("NTP: NO RESPONSE - UDP timeout")

    except OSError as error:
        print("NTP: NETWORK ERROR:", error)


if __name__ == "__main__":
    check_ntp()

