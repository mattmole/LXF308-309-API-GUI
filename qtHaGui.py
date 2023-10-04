import sys
import requests
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QHBoxLayout, QVBoxLayout, QWidget, QLabel, QLineEdit, QTableWidget, QMenu, QTableWidgetItem, QHeaderView, QMessageBox
from PyQt6.QtGui import QFont
from PyQt6.QtCore import QTimer
from haApiClient import HaEntityStatus
from rich import print
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plot
import os
import configparser

# Create a font object that we will use for all widgets
defaultFont = QFont('Arial', 14)

#Create some custom classes that set default font details accordingly

# Message box custom class
class CustomQMessageBox(QMessageBox):
    def __init__(self, title, text, font=defaultFont):
        super().__init__()
        self.setFont(font)
        self.setWindowTitle(title)
        self.setText(text)
        self.exec()

# Text box custom class
class CustomQLineEdit(QLineEdit):
    def __init__(self, text, font = defaultFont):
        super().__init__(text)
        self.setFont(font)

# Label custom class
class CustomQLabel(QLabel):
    def __init__(self, text, font = defaultFont):
        super().__init__(text)
        self.setFont(font)

# Push button custom class
class CustomQPushButton(QPushButton):
    def __init__(self, text, font = defaultFont):
        super().__init__(text)
        self.setFont(font)

# Table widget custom class
class CustomQTableWidget(QTableWidget):
    def __init__(self, font = defaultFont):
        super().__init__()
        self.setFont(font)

# Menu custom class
class CustomQMenu(QMenu):
    def __init__(self, text, font=defaultFont):
        super().__init__()
        self.setFont = font


# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    def __init__(self, windowWidth = 800, windowHeight = 500, font=defaultFont):
        super().__init__()

        self.setWindowTitle("Home Assistant API Client")
        self.setMinimumWidth(windowWidth)
        self.setMinimumHeight(windowHeight)

        # Instance variables to store useful information
        self.entityIdDict = {}
        self.trendValDict = {}
        self.plotList = []

        # Set a 5 second timer
        self.checkThreadTimer = QTimer(self)
        self.checkThreadTimer.setInterval(5000) #5 seconds
        self.checkThreadTimer.timeout.connect(self.updateTableValues)
        self.checkThreadTimer.start()

        # Set the menu bar up 
        menuBar = self.menuBar()
        menuBar.setFont(font)
        configureMenu = menuBar.addMenu("&Configure")
        configureMenu.setFont(font)
        configApiMenuAction = configureMenu.addAction("Configure API")
        selectEntitiesMenuAction = configureMenu.addAction("Select Entities")

        #Connect signals to slots to show the other windows when the menu options are clicked
        configApiMenuAction.triggered.connect(self.showConfigWindow)
        selectEntitiesMenuAction.triggered.connect(self.showSelectEntitiesWindow)

        # Create the widgets and layouts and display on the screen
        windowLabel = CustomQLabel("Selected Entities and Values")
        self.entityTable = CustomQTableWidget()

        # Set the table up on the table on the main window
        numColumns = 4
        self.entityTable.setColumnCount(numColumns)
        header = self.entityTable.horizontalHeader()
        for i in range(0, numColumns-1):     
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        header.resizeSection(3,200)
        self.entityTable.setHorizontalHeaderLabels(["EntityId", "Value", "Trend", "Trend Line"])
        
        # Add items to a layout that can be displayed
        verticalLayout = QVBoxLayout()
        verticalLayout.addWidget(menuBar)
        verticalLayout.addWidget(windowLabel)
        verticalLayout.addWidget(self.entityTable)
 
        # Set this layout as the main contents of the window
        widget = QWidget()
        widget.setLayout(verticalLayout)
        self.setCentralWidget(widget)

    # Function to run when the close button is pressed on the main window
    def closeEvent(self, event):
        if configWindow.isVisible():
            configWindow.close()
        if entityWindow.isVisible():
            entityWindow.close()

    # Show the config window when the function is called
    def showConfigWindow(self):
        configWindow.show()

    # Show the entity type selection window when the function is called
    def showSelectEntitiesWindow(self):
        entityWindow.show()

    # Update the contents of the table when the function is called
    def updateTableValues(self):

        # List of entity types that can be plotted
        domainPlotTypes = ["input_number", "input_text", "number", "sensor"]

        # For any previously drawn plots, close them as they are created new each time the table is updated
        for figure in self.plotList:
            plot.close(figure)

        # If entities have been selected, update the table
        if len(self.entityIdDict) > 0:
            # Set the number of rows in the table
            self.entityTable.setRowCount(len(self.entityIdDict))
            counter = 0
            # For each entity, pull the latest value and use it
            for entityId in self.entityIdDict:
                entityObj = self.entityIdDict[entityId]
                entityObj["oldValue"] = entityObj["rowValue"]
                entityValue = entityObj["apiCallObj"].readEntity()
                if entityValue['responseCode'] == 200 or entityValue['responseCode'] == 201:
                    entityObj["rowValue"] = entityValue['responseJson']['state']
                else:
                    messageBox = CustomQMessageBox("Connection Error", f"Connection Error: {entityValue['responseCode']}. Check API details and try again.")
                    print(entityValue["responseCode"])
                
                # Work out the integer value (all are returned as strings from the API)
                # Set the trend value if possible and this can be displayed
                if entityId.split(".")[0] in domainPlotTypes:
                    trend = None
                    trendVal=""
                    try:
                        oldValueInt = float(entityObj["oldValue"])
                        newValueInt = float(entityObj["rowValue"])
                        trendVal = newValueInt
                        if oldValueInt < newValueInt:
                            trend = "↗"
                        elif newValueInt < oldValueInt:
                            trend = "↘"
                        else:
                            trend = "="
                    except:
                        trend = ""
                        trendVal = "NaN"
                    entityObj["trend"] = trend

                    # If no trend values are available for an entity, create a new list within the dict
                    if trendVal != "" and entityId not in self.trendValDict:
                        self.trendValDict[entityId] = []
                    
                    # Append to the list if the calculated value is not a blank string
                    if trendVal != "":
                        self.trendValDict[entityId].append(trendVal)

                    # Create a plot based on the previously returned data
                    figure = plot.figure()
                    canvas = FigureCanvasQTAgg(figure)
                    axes = figure.add_subplot(111)
                    axes.set_axis_off()
                    axes.set_alpha(0)
                    axes.plot(self.trendValDict[entityId])
                    
                    self.plotList.append(figure)

                # Update the table accordingly
                self.entityTable.setItem(counter, 0, QTableWidgetItem(entityId))
                try:
                    self.entityTable.setItem(counter, 1, QTableWidgetItem(f"{float(entityObj['rowValue']):.2f}"))
                except:
                    self.entityTable.setItem(counter, 1, QTableWidgetItem(f"{entityObj['rowValue']}"))
                if "trend" in entityObj:
                    self.entityTable.setItem(counter, 2, QTableWidgetItem(f"{entityObj['trend']}"))
                else:
                    self.entityTable.setItem(counter, 2, QTableWidgetItem(""))
                if entityId.split(".")[0] in domainPlotTypes and len(self.trendValDict[entityId]) > 0:
                    self.entityTable.setCellWidget(counter, 3, canvas)
                else:
                    self.entityTable.setCellWidget(counter, 3, QWidget())
                counter += 1

# Subclass QMainWindow to customize your application's entity selection window
class EntityWindow(QMainWindow):
    def __init__(self, mainWindow, windowWidth = 600):
        super().__init__()

        #Set the window's title
        self.setWindowTitle("Select Entities to be tracked")
        self.setMinimumWidth(windowWidth)

        #Create the widgets to display and add them to a layout
        self.numEntitiesLabel = CustomQLabel("Number of Entities: ")
        self.entitiesTable = CustomQTableWidget()

        self.mainWindow = mainWindow

        # Create our layout to store the widgets
        verticalLayout = QVBoxLayout()
        verticalLayout.addWidget(self.numEntitiesLabel)
        verticalLayout.addWidget(self.entitiesTable)

        # Set the windows content
        widget = QWidget()
        widget.setLayout(verticalLayout)
        self.setCentralWidget(widget)

        # Link widgets to function calls
        self.entitiesTable.itemClicked.connect(self.selectEntities)
        self.entitiesTable.itemClicked.connect(self.mainWindow.updateTableValues)

    # Function to return the entity IDs that are selected from the table and update the entityIdDict accoridngly with objects that allow the value to be called simply
    def selectEntities(self):
        localEntityIdList = []
        selectedCells = self.entitiesTable.selectedRanges()

        for selectedCell in selectedCells:
            topRow = selectedCell.topRow()
            bottomRow = selectedCell.bottomRow()

            for i in range(topRow, bottomRow+1):
                entityId = self.entitiesTable.item(i, 0).text()
                if entityId not in mainWindow.entityIdDict:
                    mainWindow.entityIdDict[entityId] = {"rowLabel":QTableWidgetItem(entityId), "rowValue":None, "rowTrend":None, "apiCallObj":None, "oldValue": None}
                    entityValueObj = HaEntityStatus(configWindow.haServerAddressText.text(), configWindow.haApiKeyText.text(),entityId)
                    mainWindow.entityIdDict[entityId]["apiCallObj"] = entityValueObj
                    
                    try:
                        readEntityIdValue = mainWindow.entityIdDict[entityId]["apiCallObj"].readEntity()
                        if readEntityIdValue['responseCode'] == 200 or readEntityIdValue['responseCode'] == 201:
                            mainWindow.entityIdDict[entityId]["rowValue"] = readEntityIdValue['responseJson']['state']
                        else:
                            errorBox = CustomQMessageBox("Connection Error",f"Could not connect. Connection error: {readEntityIdValue['responseCode']}. Check the API details and try again.")
                    except (requests.exceptions.InvalidURL, requests.exceptions.ConnectionError):
                        errorBox = CustomQMessageBox("Connection Error","Invalid URL. Please check the details.")
                
                # Append the entityId if it is not already in the list
                if entityId not in localEntityIdList:
                    localEntityIdList.append(entityId)

        #Now check to see if the dict has items that have not been selected and remove them
        entitiesToRemove = []
        for entityId in mainWindow.entityIdDict:
            if entityId not in localEntityIdList:
                entitiesToRemove.append(entityId)

        #Remove any entityIds from the overall list that we have 
        for entityToRemove in entitiesToRemove:
            mainWindow.entityIdDict.pop(entityToRemove)
            if entityToRemove in mainWindow.trendValDict:
                mainWindow.trendValDict.pop(entityToRemove)

# Subclass QMainWindow to customize your application's config window
class ConfigWindow(QMainWindow):
    def __init__(self, entityWindow, uri, apiKey, windowWidth = 600, windowHeight = 500):
        super().__init__()
        self.entityWindow = entityWindow
        self.uri = uri
        self.apiKey = apiKey

        #Set the window's title
        self.setWindowTitle("Configure Home Assistant Viewer")
        self.setMinimumWidth(windowWidth)
        self.setMinimumHeight(windowHeight)

        self.entityWindow = entityWindow

        whiteSpace = QLabel("")

        #Create the widgets to get server details and add them to horizontal layouts
        haServerDetailsLabel = CustomQLabel("Add Server Details:")
        haServerAddressLabel = CustomQLabel("Server IP / FQDN")

        haApiKeyLabel = CustomQLabel("Server API Key")

        self.haServerAddressText = CustomQLineEdit(self.uri)
        self.haApiKeyText = CustomQLineEdit(self.apiKey)
        self.haApiKeyText.setEchoMode(QLineEdit.EchoMode.Password)
        haServerHLayout = QHBoxLayout()
        haApiKeyHLayout = QHBoxLayout()
        haServerHLayout.addWidget(haServerAddressLabel)
        haServerHLayout.addWidget(self.haServerAddressText)
        haApiKeyHLayout.addWidget(haApiKeyLabel)
        haApiKeyHLayout.addWidget(self.haApiKeyText)

        connectApiButton = CustomQPushButton("Connect To Home Assistant")

        # Create the widgets to display the list of entity types
        entityTypeLabel = CustomQLabel("Select the type of entities to select from:")
        self.entityTypeTable = CustomQTableWidget()

        # Add widgets to a layout
        verticalLayout = QVBoxLayout()

        verticalLayout.addWidget(haServerDetailsLabel)
        verticalLayout.addLayout(haServerHLayout)
        verticalLayout.addLayout(haApiKeyHLayout)
        verticalLayout.addWidget(connectApiButton)
        verticalLayout.addWidget(whiteSpace)
        verticalLayout.addWidget(entityTypeLabel)
        verticalLayout.addWidget(self.entityTypeTable)

        # Display the widgets on the window
        widget = QWidget()
        widget.setLayout(verticalLayout)
        self.setCentralWidget(widget)

        # Connect the two buttons to the functions
        connectApiButton.clicked.connect(self.connectToApi)
        self.entityTypeTable.itemClicked.connect(self.selectEntityTypes)

    # When the Connect to API button is selected, read the entities from the API and update the list of domains from this list
    def connectToApi(self):
        print("Connecting to API")

        uriEntered = self.haServerAddressText.text()
        apiEntered = self.haApiKeyText.text()
        print("Connecting to the API...")
        allEntities = HaEntityStatus(uriEntered, apiEntered)
        print("Reading entities...")
        try:
            allEntities.readAllEntities()

        # If possible to connect to the API create a list of entity domains and populate the entity domain table
            if allEntities.responseCode >= 200 and allEntities.responseCode <= 400:

                global entitiesJson 
                entitiesJson = allEntities.entities

                # Sorted the list of entity_ids
                entitiesJson = sorted(entitiesJson, key=lambda x:x['entity_id'])
                entityDomains = []

                for entity in entitiesJson:
                    if "." in entity["entity_id"]:
                        entityDomain = entity["entity_id"].split('.')[0]
                        if entityDomain not in entityDomains:
                            entityDomains.append(entityDomain)
                
                # Set the size of the table and configure the table
                self.entityTypeTable.setRowCount(len(entityDomains))
                self.entityTypeTable.setColumnCount(1)
                self.entityTypeTable.verticalHeader().setVisible(False)
                self.entityTypeTable.horizontalHeader().setVisible(False)

                header = self.entityTypeTable.horizontalHeader()       
                header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

                # Populate the entity domain table
                for i in range(len(entityDomains)):
                    self.entityTypeTable.setItem(i, 0, QTableWidgetItem(entityDomains[i]))
            
            else:
                print ("Could not connect to the API")
                errorBox = CustomQMessageBox("API Connection Error","Could not connect to the API. Please check the credentials.")

        except (requests.exceptions.InvalidURL, requests.exceptions.ConnectionError):
            errorBox = CustomQMessageBox("Connection Error","Invalid URL. Please check the details.")
        
    # Function to return the entity types that have been selected in the config window and add to a set
    def selectEntityTypes(self):
        entityWindow.show()

        selectedDomains = set()
        # Selected domains
        for selected in configWindow.entityTypeTable.selectedRanges():
            for i in range(selected.topRow(), selected.bottomRow()+1):
                selectedDomains.add(configWindow.entityTypeTable.item(i,0).text())


        # Now we need to populate the entities table, which we will do by creating a dictionary that stores the necessary details
        relevantEntitiesList = []
        counter = 0
        for entity in entitiesJson:
            for domain in selectedDomains:
                if entity["entity_id"].startswith(domain):
                    relevantEntitiesList.append(entity["entity_id"])
                    counter += 1
        self.entityWindow.entitiesTable.setRowCount(counter)
        self.entityWindow.entitiesTable.setColumnCount(1)

        # Set the size of the table and configure the table
        self.entityWindow.entitiesTable.verticalHeader().setVisible(False)
        self.entityWindow.entitiesTable.horizontalHeader().setVisible(False)
        header = self.entityWindow.entitiesTable.horizontalHeader()       
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        # Update the label on the entities window
        self.entityWindow.numEntitiesLabel.setText("Number of Entities: " + str(len(relevantEntitiesList)))

        for i in range(0, len(relevantEntitiesList)):
            self.entityWindow.entitiesTable.setItem(i, 0, QTableWidgetItem(relevantEntitiesList[i]))

if __name__ == "__main__":

    uri = ""
    apiKey = ""

    # Load in details from the config file, if it exists
    configFile = "haApiConfig.conf"
    configFilePath = os.path.join(os.path.dirname(__file__), configFile)
    config = configparser.ConfigParser()

    if os.path.exists(configFilePath):
        config.read(configFilePath)
        if "Server" in config and "Address" in config["Server"]:
            uri = config["Server"]["Address"]
        if "Server" in config and "ApiKey" in config["Server"]:
            apiKey = config["Server"]["ApiKey"]
    else:
        print("Config file does not exist or is incorrectly formatted! You will be asked to enter details next...")

    # Create a new application and windows
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    entityWindow = EntityWindow(mainWindow = mainWindow)    
    configWindow = ConfigWindow(entityWindow = entityWindow, uri = uri, apiKey = apiKey)

    # Open the main window when the program runs and execute the app
    mainWindow.show()
    app.exec()