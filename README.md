# LXF308-309-API-GUI
Article series for Linux Format taking data from an API and displaying in a GUI.

API and Server details can be entered into a file called haApiConfig.conf and takes the format of the file called haApiConfig.conf-SAMPLE. Place this configured file next to the haApiClient.py and qtHaGui.py files. If the file is omitted, you will be prompted to enter API details in either program.

* qtHaGui.py contains a QT6 GUI to display data
* haApiClient.py contains a command-line program to display data
* haApiClient.py contains the base classes to interact with the API, with the added client to read values regularly.