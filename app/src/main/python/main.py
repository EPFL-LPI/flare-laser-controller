import os
import sys
import glob
import re
import serial.tools.list_ports

from fbs_runtime.application_context import ApplicationContext

# PyQt
from PyQt5 import QtGui

from PyQt5.QtCore import (
    Qt,
    QTimer,
    QThread
)

from PyQt5.QtWidgets import ( 
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout, 
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit
)

# FLC
import flare_laser_control as flc

# App

class FlcInterface( QWidget ):
    
    #--- window close ---
    def closeEvent( self, event ):
        self.__deleteController()  
        event.accept()
    
    #--- destructor ---
    def __del__( self ):
        self.__deleteController()
    
    
    #--- initializer ---
    
    def __init__( self, resources ):
        super().__init__()
        
        #--- instance variables ---
        image_folder = resources + '/images/'
        self.img_redLight = QtGui.QPixmap( image_folder + 'red-light.png' ).scaledToHeight( 32 )        
        self.img_greenLight = QtGui.QPixmap( image_folder + 'green-light.png' ).scaledToHeight( 32 )
        self.img_yellowLight = QtGui.QPixmap( image_folder + 'yellow-light.png' ).scaledToHeight( 32 )
        
        self.ports = self.__getComPorts()
        self.port  = None
        self.flc   = None
        
        #--- timers ---
        
        # update status timer
        self.statusTimer = QTimer()
        self.statusTimer.timeout.connect( self.updateStatus )
        self.statusTimer.start( 1000 )
        
        # update ports timer
        self.portsTimer = QTimer()
        self.portsTimer.timeout.connect( self.updatePorts )
        self.portsTimer.start( 30* 1000 )
        
        #--- init UI ---
        
        self.__init_ui()
        self.__register_connections()
        
        #--- init variables ---
        
        self.__updatePort()
        
        
    def __init_ui( self ):
        #--- main window ---
        self.setGeometry( 100, 100, 700, 150 )
        self.setWindowTitle( 'Flare Laser Controller' )
        
        lo_mainLayout = QVBoxLayout()
        lo_mainLayout.addLayout( self.__ui_mainToolbar() )
        # lo_mainLayout.addLayout( self.__ui_commands()    )
        # lo_mainLayout.addLayout( self.__ui_diagnostics() )
        
        self.setLayout( lo_mainLayout )
        
        self.show()
        
        
    def __ui_mainToolbar( self ):
        #--- main toolbar ---
        lo_mainToolbar = QHBoxLayout()
        
        self.__mainToolbar_comPorts( lo_mainToolbar )
        self.__mainToolbar_connect(  lo_mainToolbar )
        self.__mainToolbar_enable(   lo_mainToolbar )
        
        return lo_mainToolbar
        
        
    def __ui_commands( self ):
        #--- commands ---
        lo_commands = QHBoxLayout()
        
        self.__commands_pulse( lo_commands )
        self.__commands_oscillate( lo_commands )
        
        return lo_commands
    
    
    def __ui_diagnostics( self ):
        pass
        
    #--- components ---
    
    def __mainToolbar_comPorts( self, parent ):
        # com ports
        self.cmb_comPort = QComboBox()
        self.__updatePortsUI()
        
        lo_ComPort = QFormLayout()
        lo_ComPort.addRow( 'COM Port', self.cmb_comPort )
        
        parent.addLayout( lo_ComPort )
        
    def __mainToolbar_connect( self, parent ):
        # connect / disconnect
        self.lbl_statusLight = QLabel()
        self.lbl_statusLight.setAlignment( Qt.AlignCenter )
        self.lbl_statusLight.setPixmap( self.img_redLight )
        
        self.lbl_status = QLabel( 'Disconnected' )
        self.btn_connect = QPushButton( 'Connect' )
    
        lo_statusView = QVBoxLayout()
        lo_statusView.addWidget( self.lbl_statusLight )
        lo_statusView.addWidget( self.lbl_status )
        lo_statusView.setAlignment( Qt.AlignHCenter )
        
        lo_status = QHBoxLayout()
        lo_status.addLayout( lo_statusView )
        lo_status.addWidget( self.btn_connect )
        lo_status.setAlignment( Qt.AlignLeft )
        
        parent.addLayout( lo_status )
        
        
    def __mainToolbar_enable( self, parent ):
        # enable / disable
        self.lbl_enabledLight = QLabel()
        self.lbl_enabledLight.setAlignment( Qt.AlignCenter )
        self.lbl_enabledLight.setPixmap( self.img_redLight )
        
        self.lbl_enabled = QLabel( 'Disabled' )
        self.btn_enable = QPushButton( 'Enable' )
        
        lo_enabledView = QVBoxLayout()
        lo_enabledView.addWidget( self.lbl_enabledLight )
        lo_enabledView.addWidget( self.lbl_enabled )
        lo_enabledView.setAlignment( Qt.AlignHCenter )
        
        lo_enable = QHBoxLayout()
        lo_enable.addLayout( lo_enabledView )
        lo_enable.addWidget( self.btn_enable )
        lo_enable.setAlignment( Qt.AlignLeft )
        
        parent.addLayout( lo_enable )
        
        
    def __commands_pulse( self, parent ):
        # title
        lbl_title = QLabel( 'Pulse' )
        
        # input
        self.le_pulseTime = QLineEdit()
        lbl_timeUnit = QLabel( 'ms' )
        
        lo_input = QHBoxLayout()
        lo_input.addWidget( self.le_pulseTime )
        lo_input.addWidget( lbl_timeUnit )
        
        # run
        self.btn_pulse = QPushButton( 'Pulse' )
        
        # layout
        lo_pulse = QVBoxLayout()
        lo_pulse.addWidget( lbl_title )
        lo_pulse.addLayout( lo_input )
        lo_pulse.addWidget( self.btn_pulse )
        
        parent.addLayout( lo_pulse )
        
    def __commands_oscillate( self, parent ):
        # title
        lbl_title = QLabel( 'Oscillate' )
        
        # input
        self.le_oscillateOn     = QLineEdit()
        self.le_oscillateOff    = QLineEdit()
        self.le_oscillateCycles = QLineEdit()
        
        lbl_timeUnitOn = QLabel( 'ms' )
        lbl_timeUnitOff = QLabel( 'ms' )
        
        lo_oscillateOn = QHBoxLayout()
        lo_oscillateOn.addWidget( self.le_oscillateOn )
        lo_oscillateOn.addWidget( lbl_timeUnitOn )
        
        lo_oscillateOff = QHBoxLayout()
        lo_oscillateOff.addWidget( self.le_oscillateOff )
        lo_oscillateOff.addWidget( lbl_timeUnitOff )
        
        lo_input = QFormLayout()
        lo_input.addRow( 'On',     lo_oscillateOn     )
        lo_input.addRow( 'Off',    lo_oscillateOff    )
        lo_input.addRow( 'Cycles', self.le_oscillateCycles )
        
        # run
        self.btn_oscillate       = QPushButton( 'Oscillate' )
        self.btn_oscillateCancel = QPushButton( 'Cancel' )
        
        lo_run = QVBoxLayout()
        lo_run.addWidget( self.btn_oscillate )
        lo_run.addWidget( self.btn_oscillateCancel )
        
        # layout
        lo_oscillate = QVBoxLayout()
        lo_oscillate.addWidget( lbl_title )
        lo_oscillate.addLayout( lo_input  )
        lo_oscillate.addLayout( lo_run    )
        
        parent.addLayout( lo_oscillate )
    
    #--- ui functionality ---
        
    def __register_connections( self ):
        self.cmb_comPort.currentTextChanged.connect( self.changePort )
        self.btn_connect.clicked.connect( self.toggleConnect )
        self.btn_enable.clicked.connect( self.toggleEnable )
        
            
    def __getComPorts( self ):
        """ (from https://stackoverflow.com/a/14224477/2961550)
        Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
        """
        if sys.platform.startswith( 'win' ):
            ports = [ 'COM%s' % (i + 1) for i in range( 256 ) ]
        elif sys.platform.startswith( 'linux' ) or sys.platform.startswith( 'cygwin' ):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob( '/dev/tty[A-Za-z]*' )
        elif sys.platform.startswith( 'darwin' ):
            ports = glob.glob( '/dev/tty.*' )
        else:
            raise EnvironmentError( 'Unsupported platform' )

        result = []
        for port in ports:
            try:
                s = serial.Serial( port )
                s.close()
                result.append( port )
            except ( OSError, serial.SerialException ):
                pass
            
        return result
        
    
    #--- slot functions ---
    
    def changePort( self ):
        """
        Changes port and disconnects from current port if required
        """
        # disconnect and delete controller
        self.__deleteController()
          
        # update port
        self.__updatePort()
        
    
    
    def toggleConnect( self ):
        """
        Toggles connection between selected com port
        """
        # show waiting for communication
        self.lbl_status.setText( 'Waiting...' )
        self.lbl_statusLight.setPixmap( self.img_yellowLight )
        self.repaint()
        
        # create laser controller if doesn't already exist, connect
        if self.flc == None:
            self.flc = flc.LaserController( self.port )
        
        else:
            # connect / disconnect
            connected = self.flc.isConnected()
            if connected == True:
                # already connected, disconnect
                self.flc.disconnect()

            elif connected == False:
                # disconnected, connect to port 
                self.flc.connect()

            else:
                # error
                pass
        
        # update ui
        self.__updateConnectedUI( self.flc.isConnected() )
        
        
    def toggleEnable( self ):
        """
        Toggles connection between selected com port
        """
        # show waiting
        self.lbl_enabled.setText( 'Waiting...' )
        self.lbl_enabledLight.setPixmap( self.img_yellowLight )
        self.repaint()
        
        # enable / disable
        if self.flc.status() == 'enabled':
            # already enables, disable
            self.flc.disable()
            
        else:
            # already disabled, enable
            self.flc.enable()   
        
        # update ui
        if self.flc:
            status = self.flc.status()
            
        else:
            status = 'Communication lost'
        
        
        self.__updateEnabledUI( status )
        
    
    def updatePorts( self ):
        """
        Check available COMs, and update UI list
        """
        self.ports = self.__getComPorts()
        self.__updatePortsUI()

        
    def updateStatus( self ):
        """
        Check the connection status of the laser, and update UI
        """
        # get connection state
        if self.flc is not None:
            # try to get connected state
            try:
                connected = self.flc.isConnected()
                
                if connected:
                    status = self.flc.status()
                    
                else:
                    status = 'No Communication'   
            
            except serial.SerialException:
                # not connected
                self.__deleteController()
                connected = False
                status = 'No Communication'
                
            except:
                print( "Unexpected Error: ", sys.exc_info()[ 0 ] )
                raise
        
        else:
            connected = False
            status = 'No Communication'
            
        # update ui
        self.__updateConnectedUI( connected )
        self.__updateEnabledUI( status )
                
            
    #--- helper functions ---
    
    def __parseComPort( self, name ):
        pattern = "(\w+)\s*(\(\s*\w*\s*\))?"
        matches = re.match( pattern, name )
        if matches:
            name = matches.group( 1 )
            if name == 'No COM ports available...':
                return None
            else:
                return name
        else:
            return None
        
        
    def __deleteController( self ):
        if self.flc is not None:
            if self.flc.isConnected():
                self.flc.disconnect()
            
            del self.flc
            self.flc = None
       
    
    def __updatePort( self ):
        self.port = self.cmb_comPort.currentText()
        
        
    def __updatePortsUI( self ):
        self.cmb_comPort.clear()
        
        if len( self.ports ):
            self.cmb_comPort.addItems( self.ports )
        else:
            self.cmb_comPort.addItem( 'No COM ports available...' )
        
        
    def __updateConnectedUI( self, connected ):
        if connected == True:
            statusText = 'Connected'
            statusLight = self.img_greenLight
            btnText = 'Disconnect'
            
        elif connected == False:
            statusText = 'Disconnected'
            statusLight = self.img_redLight
            btnText = 'Connect'
            
        else:
            statusText = 'Error'
            statusLight = self.img_yellowLight
            btnText = 'Connect'
        
        self.lbl_status.setText( statusText )
        self.lbl_statusLight.setPixmap( statusLight )
        self.btn_connect.setText( btnText )
        
    
    def __updateEnabledUI( self, status, light = None, btn = None ):
        if status == 'enabled':
            statusText = 'Enabled'
            statusLight = self.img_greenLight
            btnText = 'Disable'
            
        elif status == 'disabled':
            statusText = 'Disabled'
            statusLight = self.img_redLight
            btnText = 'Enable'
            
        else:
            # error
            statusText = status
            statusLight = light or self.lbl_enabledLight.pixmap()
            btnText = btn or self.btn_enable.text()
            
        
        self.lbl_enabled.setText( statusText )
        self.lbl_enabledLight.setPixmap( statusLight )
        self.btn_enable.setText( btnText )
    

class AppContext( ApplicationContext ):           # 1. Subclass ApplicationContext
    def run( self ):                              # 2. Implement run()
        window = FlcInterface( self.get_resource() )
        window.show()
        return self.app.exec_()                 # 3. End run() with this line

if __name__ == '__main__':
    appctxt = AppContext()                      # 4. Instantiate the subclass
    exit_code = appctxt.run()                   # 5. Invoke run()
    sys.exit( exit_code )