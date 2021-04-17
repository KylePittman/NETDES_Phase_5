# Backend processing of the server side logic
# Handles nearly everything with reception of files

import Packet
import Transmission_Constants
import socket
import pickle
import time
import random


# Class to handle processing of reception
class ServerBackend:

    def __init__(self, text_stream, server_port, error_sim, percent_error):
        # Text stream allows communication to GUI
        self.text_stream = text_stream

        self.file = b""
        # User input variables
        self.server_port = server_port
        self.error_sim = error_sim
        self.percent_error = percent_error

        # Initialize socket
        self.socket_opened = False
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.open_socket()

        # Establish State Variables
        self.terminate_session = False

        self.expected_sequence_number = 0
        self.ACK = self.expected_sequence_number
        self.start_time = -1
        self.run_time = -1
        self.forced_errors = 0
        self.end_of_file = False

    # Function to initalize socket
    def open_socket(self):
        # Return if already opened
        if self.socket_opened:
            self.text_stream.write("ERROR --Socket Already Opened--")
            return
        self.text_stream.write("STATUS --Opening Socket--")
        self.text_stream.write(f"SIM ERROR --Error Sim: {self.error_sim} | Percent Error: {self.percent_error}--")
        self.server_socket.bind(("localhost", self.server_port))
        self.server_socket.settimeout(Transmission_Constants.SOCKET_TIMEOUT)

    # Sends ACK token, includes logic to simulate bad connection
    def send_ACK(self, client_address):
        # Creates ACK packet
        packet = Packet.Packet(Transmission_Constants.ACK)
        packet.ID = self.expected_sequence_number

        if not self.end_of_file:
            # Logic to 'drop' packets
            if self.error_sim == Transmission_Constants.PACKETLOSSSIM:
                failure = random.uniform(0, 100)
                if failure < self.percent_error:
                    self.text_stream.write(f"SIM ERROR --Dropping Packet: {packet.ID}--")
                    self.forced_errors = self.forced_errors + 1
                    return
            # Logic to corrupt packets
            if self.error_sim == Transmission_Constants.DATAERRORSIM:
                failure = random.uniform(0, 100)
                if failure < self.percent_error:
                    self.text_stream.write(f"SIM ERROR --Corrupting Packet: {packet.ID}--")
                    self.forced_errors = self.forced_errors + 1
                    packet.data = b'\x74\x15\xE2\03\x74\x15\xE2\03\x74\x15\xE2\03\x74\x15\xE2\03'

        # Transmit packet
        self.server_socket.sendto(pickle.dumps(packet), client_address)
        self.text_stream.write(f"TRANSMISSION --Sending ACK Packet {packet.ID}--")

    # Handles reception of data
    def receive(self):
        # Asserts State Variables
        self.end_of_file = False
        self.expected_sequence_number = 0
        self.ACK = self.expected_sequence_number
        self.start_time = -1
        self.run_time = -1

        self.expected_sequence_number = 0
        self.ACK = self.expected_sequence_number

        # Allows window to terminate while loop
        while not self.terminate_session:
            # Will attempt to retrieve any sent data before timeout
            try:
                packet, client_address = self.server_socket.recvfrom(Transmission_Constants.PACKET_SIZE * 2)
                received_packet = pickle.loads(packet)

                # Checksum verification
                checksum = received_packet.checksum
                received_packet.generateChecksum()

                if checksum == received_packet.checksum:
                    # Verifies correct packet arrived
                    if received_packet.ID == self.expected_sequence_number:
                        if received_packet.ID == 0:
                            self.start_time = time.time()

                        self.text_stream.write(f"RECEPTION --Recieved packet {received_packet.ID} in order--")
                        self.text_stream.write(f"RECEPTION --Recieved from: {client_address}--")

                        # Checks for EOF, adds data to file if not
                        if received_packet.data != Transmission_Constants.END_TRANSMISSION:
                            self.file = self.file + received_packet.data
                        else:
                            self.end_of_file = True
                        # Increases sequence number
                        self.expected_sequence_number = self.expected_sequence_number + 1

                        self.text_stream.write("STATUS --Sending New ACK--")
                        self.send_ACK(client_address)
                    # Resends ACK if the correct packet wasnt sent
                    else:
                        self.text_stream.write("ERROR --Resending ACK--")
                        self.text_stream.write(f"Expected {self.expected_sequence_number} | Received {received_packet.ID}")
                        self.send_ACK(client_address)
                # Catches bad checksum
                else:
                    self.text_stream.write("ERROR --Bad Checksum--")
            # Timeout exception
            except:
                # Breaks while loop on completion
                if self.end_of_file:
                    self.run_time = time.time() - self.start_time
                    break

        # Ensures complete file transfer occured
        if not self.terminate_session:
            self.text_stream.write(f"STATUS --Transmission Time: {self.run_time}--")
            self.text_stream.write(f"SIM ERRORS --Generated {self.forced_errors} errors--")
            return self.file
        else:
            return -1
