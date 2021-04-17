# GUI for Client

from future.moves import tkinter as tk
import tkinter.filedialog as fd
import Client_Backend
import threading
import Transmission_Constants


ERRORLIST = ("No Errors", "Data Errors", "Data Packet Loss")

client = None


class TextStream:
    txt_output = None

    def __init__(self, txt_output):
        self.txt_output = txt_output

    def write(self, msg):
        txt_output.insert(tk.END, f"{msg} \n")
        txt_output.see("end")

# Parses Address Field
def parse_address_field():
    temp = server_address.get().split(":")
    return (temp[0], int(temp[1]))

# Parses Error Selection
def parse_error_field():
    ERRORSIM = -1
    print(ERRORSELECT.get())
    if ERRORSELECT.get() == ERRORLIST[Transmission_Constants.NOERRORSIM]:
        ERRORSIM = Transmission_Constants.NOERRORSIM
    elif ERRORSELECT.get() == ERRORLIST[Transmission_Constants.DATAERRORSIM]:
        ERRORSIM = Transmission_Constants.DATAERRORSIM
    else:
        ERRORSIM = Transmission_Constants.PACKETLOSSSIM
    return ERRORSIM

# Initializes Backend CLient
def init_client():
    global client
    text_stream = TextStream(txt_output)
    client = Client_Backend.ClientBackend(text_stream, filename.get(), int(client_port.get()), parse_address_field(), parse_error_field(), percent_error.get())
    print(type(client))

# Function needed to call transmit as a thread
def transmit():
    client.transmit_file()

# Open window to select a file
def fileSelect():
    global filename
    filename.set(fd.askopenfile(mode = 'rb').name)

# Only runs window setup once
if __name__ == "__main__":

    # Window Setup
    window = tk.Tk()
    client_port = tk.StringVar()
    client_port.set("1414")
    server_address = tk.StringVar()
    server_address.set("localhost:777")
    filename = tk.StringVar()
    filename.set("C:/Users/kylep/OneDrive/Desktop/School/2021 SP/NETDES/file_example_PNG_500kB.png")
    percent_error = tk.IntVar()

    window.title("Client RDT 3.0")

    window.rowconfigure([0, 1, 2, 3, 4, 5], minsize = 50, weight = 1)
    window.columnconfigure([0, 1], minsize = 50, weight = 1)

    ERRORSELECT = tk.StringVar(window)
    ERRORSELECT.set(ERRORLIST[0])
    om_ErrorSelection = tk.OptionMenu(window, ERRORSELECT, *ERRORLIST)
    om_ErrorSelection.grid(row = 0, column = 0, sticky = "nsew")

    scale_error = tk.Scale(window, label = "Percent Error", variable=percent_error, from_=0, to=100, tickinterval=5, orient=tk.HORIZONTAL)
    scale_error.grid(row=0, column=1, sticky="nsew")

    lbl_clientAddress = tk.Label(master = window, text = "Client Port: ")
    lbl_clientAddress.grid(row = 1, column = 0, sticky = "nsew")

    ent_clientAddress = tk.Entry(master = window, textvariable = client_port)
    ent_clientAddress.grid(row = 1, column = 1, sticky = "ew")

    lbl_serverAddress = tk.Label(master = window, text = "Server Address (xxx.xxx.x.x:xxxx) : ")
    lbl_serverAddress.grid(row = 2, column = 0, sticky = "nsew")

    ent_port = tk.Entry(master = window, textvariable = server_address)
    ent_port.grid(row = 2, column = 1, sticky = "ew")

    btn_file = tk.Button(master = window, text = "Select File", command = fileSelect)
    btn_file.grid(row = 3, column = 0, sticky = "nsew")

    ent_file = tk.Entry(master = window, textvariable = filename)
    ent_file.grid(row = 3, column = 1, sticky = "ew")

    lbl_output = tk.Label(master = window, text = "Output: ")
    lbl_output.grid(row = 4, column = 0, sticky = "nsew")

    txt_output = tk.Text(master = window)
    txt_output.grid(row = 4,column = 1, sticky = "nsew")
    txt_output.see(tk.END)

    btn_open = tk.Button(master = window, text = "Open Socket", command = init_client)
    btn_open.grid(row = 5, column = 0, sticky = "nsew")

    btn_send = tk.Button(master = window, text = "Send", command = threading.Thread(target = transmit).start)
    btn_send.grid(row = 5, column = 1, sticky = "nsew")

    window.mainloop()