# Backend processing of the client side logic
# Handles nearly everything with transmission

import Packet
import Transmission_Constants
import socket
import pickle
import time
import random


# Class to handle backend processing of transmission
class ClientBackend:

    def __init__(self, text_stream, filename, client_port, server_address, error_sim, percent_error):
        #text stream allows communication to the GUI
        self.text_stream = text_stream

        #Variables input by user
        self.filename = filename
        self.client_port = client_port
        self.server_address = server_address

        self.error_sim = error_sim
        self.percent_error = percent_error

        # Initialize socket
        self.socket_opened = False
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.open_socket()

        #Initialize state variables
        self.base = 0
        self.next_sequence_number = self.base
        self.window_size = 10
        self.window = []

        self.most_recent_ACK_time = time.time()
        self.transmission_complete = False

        self.forced_errors = 0
        self.packets_sent = 0

    # Function to establish socket
    def open_socket(self):
        if self.socket_opened:
            self.text_stream.write("ERROR --Socket Already Opened--")
            return
        self.text_stream.write("STATUS --Opening Socket--")
        self.text_stream.write(f"SIM ERROR --Error Sim: {self.error_sim} | Percent Error: {self.percent_error}--")
        self.client_socket.bind(("localhost", self.client_port))
        self.client_socket.settimeout(Transmission_Constants.SOCKET_TIMEOUT)

    # Function to send packet
    # Includes logice to produce simulated errors
    def send_packet(self, packet):
        # Ensures corrupted packets can get their data back after tranmission
        good_data = packet.data

        # 'Drops' Packets
        if self.error_sim == Transmission_Constants.PACKETLOSSSIM:
            failure = random.uniform(0, 100)
            if failure < self.percent_error:
                self.text_stream.write(f"SIM ERROR --Dropping Packet: {packet.ID}--")
                self.forced_errors = self.forced_errors + 1
                self.packets_sent = self.packets_sent + 1
                return

        # Corrupts packets
        if self.error_sim == Transmission_Constants.DATAERRORSIM:
            failure = random.uniform(0, 100)
            if failure < self.percent_error:
                self.text_stream.write(f"SIM ERROR --Corrupting Packet: {packet.ID}--")
                self.forced_errors = self.forced_errors + 1
                packet.data = b'\x74\x15\xE2\x03\x74\x15\xE2\x03\x74\x15\xE2\x03\x74\x15\xE2\x03'

        self.client_socket.sendto(pickle.dumps(packet), self.server_address)
        if packet.data:
            self.text_stream.write(f"TRANSMISSION --Sending Packet {packet.ID}--")
        self.packets_sent = self.packets_sent + 1

        # Ensures packet is restored if it was intentionally corrupted
        packet.data = good_data
        packet.generateChecksum()

    # Receive function
    def receive_packet(self):
        try:
            packet, server_address = self.client_socket.recvfrom(Transmission_Constants.PACKET_SIZE * 2)
            self.text_stream.write("RECEPTION --Received Packet--")
            received_packet = pickle.loads(packet)

            # Verify checksum
            checksum = received_packet.checksum
            received_packet.generateChecksum()

            if checksum == received_packet.checksum:
                self.text_stream.write(f"RECEPTION --Received ACK for {received_packet.ID}--")

                # Moves window if ACK was within window
                while received_packet.ID > self.base and self.window:
                    self.most_recent_ACK_time = time.time()
                    del self.window[0]
                    self.base = self.base + 1
                    self.text_stream.write(f"Current Base: {self.base}")

            else:
                self.text_stream.write(f"ERROR --ACK Checksum ERROR--")

        except:
            self.text_stream.write(f"ERROR --No ACK  Base: {self.window[0].ID}--")
            # Resends entire window in case of timeout
            if(time.time()-self.most_recent_ACK_time > 0.01):
                for packet in self.window:
                    self.send_packet(packet)

    # Function to transmit an entire file
    def transmit_file(self):
        # Open file for reading
        try:
            file = open(self.filename, 'rb')
        except IOError:
            self.text_stream.write("ERROR --Could not read file--")
            return -1

        # Assert state variables
        self.transmission_complete = False

        start_time = time.time()

        # Loop will run until there is no more data to transmit
        while not self.transmission_complete or self.window:

            # Sends next datum if it is within the window
            if((self.next_sequence_number < self.base + self.window_size) and not self.transmission_complete):
                data = file.read(Transmission_Constants.PACKET_SIZE)

                # If the data is empty, send a token to notify Server of EOF
                if not data:
                    data = Transmission_Constants.END_TRANSMISSION
                    self.transmission_complete = True

                # Package Data
                packet = Packet.Packet(data)
                packet.ID = self.next_sequence_number

                # Send data and update sequence number
                self.send_packet(packet)
                self.next_sequence_number = self.next_sequence_number + 1

                # Add packet to window
                self.window.append(packet)
            # Check for ACKs
            self.receive_packet()
        # Calculate runtime
        run_time = time.time() - start_time
        file.close()
        self.text_stream.write("STATUS --Transmission Complete--")
        self.text_stream.write(f"STATUS --Transmission Time {run_time}--")
        self.text_stream.write(f"SIM ERROR --Forced error percentage: {self.forced_errors / self.packets_sent}--")