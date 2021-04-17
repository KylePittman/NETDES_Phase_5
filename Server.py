# Server GUI

from future.moves import tkinter as tk
import tkinter.filedialog as fd
import Server_Backend
import threading
import Transmission_Constants

ERRORLIST = ("No Errors", "ACK Errors", "ACK Packet Loss")

server = None

class TextStream:
    txt_output = None

    def __init__(self, txt_output):
        self.txt_output = txt_output

    def write(self, msg):
        txt_output.insert(tk.END, f"{msg} \n")
        txt_output.see("end")


# Writes the data transmitted to a file of the same name in the same working directory of the program
def writeFile(file):
    global filename
    if filename.get() == "":
        filename.set("output")
    path = fd.askdirectory() + '\\' + filename.get()
    f = open(path, 'wb')
    f.write(file)
    f.close()
    filename = ''

# Parses error field
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

# Initalizes backend server
def open_server():
    global server
    text_stream = TextStream(txt_output)
    server = Server_Backend.ServerBackend(text_stream, int(server_port.get()), parse_error_field(), percent_error.get())
    file = server.receive()
    if file != -1:
        writeFile(file)

# Breaks while loop when x is pressed in window
def on_closing():
    global server
    if server is not None:
        server.terminate_session = True
    window.quit()
    window.destroy()




# Set up window
window = tk.Tk()
server_port = tk.StringVar()
server_port.set("777")
filename = tk.StringVar()
filename.set("output.png")
percent_error = tk.IntVar()

window.title("Server RDT 3.0")


window.rowconfigure([0, 1, 2, 3], minsize=50, weight=1)
window.columnconfigure([0, 1], minsize=50, weight=1)

ERRORSELECT = tk.StringVar(window)
ERRORSELECT.set(ERRORLIST[0])
om_ErrorSelection = tk.OptionMenu(window, ERRORSELECT, *ERRORLIST)
om_ErrorSelection.grid(row = 0, column = 0, sticky = "nsew")

scale_error = tk.Scale(window, label = "Percent Error", variable = percent_error, from_ = 0, to = 100, tickinterval = 5, orient = tk.HORIZONTAL)
scale_error.grid(row = 0, column = 1, sticky = "nsew")

lbl_serverPort = tk.Label(master=window, text="Server Port: ")
lbl_serverPort.grid(row=1, column=0, sticky="nsew")

ent_port = tk.Entry(master=window, textvariable=server_port)
ent_port.grid(row=1, column=1, sticky="ew")

lbl_filename = tk.Label(master=window, text="File Name: ")
lbl_filename.grid(row=2, column=0, sticky="nsew")

ent_filename = tk.Entry(master=window, textvariable=filename)
ent_filename.grid(row=2, column=1, sticky="ew")

lbl_output = tk.Label(master=window, text="Output: ")
lbl_output.grid(row=3, column=0, sticky="nsew")

txt_output = tk.Text(master=window)
txt_output.grid(row=3, column=1, sticky="nsew")

btn_open = tk.Button(master=window, text="Open Socket", command=threading.Thread(target=open_server).start)
btn_open.grid(row=4, column=1, sticky="nsew")

window.protocol("WM_DELETE_WINDOW", on_closing)
# Calls receive function on startup of tkinter's main function
window.mainloop()