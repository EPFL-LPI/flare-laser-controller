
# coding: utf-8

# # Interface for Flare laser
# Use this to remotely control the Flaser laser.
# 
# ## API
# First create an instance of the controller providing the serial port the laser is connected to. The controller will automatically connect to the port upon creation, but can be manually connected and disconnnected as well.
# ~~~
# lc = LaserController( "COM4" )
# ~~~
# 
# Connect to the port manually using the `connect()` method, and disconnect using the `disconnect()` method.
# ~~~
# lc.disconnect()
# lc.connect()
# ~~~
# Be wary when using these commands right after eachother, as the network may need some time to reset. 
# 
# 
# ## Commands
# The LaserController supports 5 basic laser commands:
# 
# **status()**: Returns the status of the laser in the **id** field. **1** is enabled, **0** is disabled.
# 
# **enable()**: Enables the laser.
# 
# **disable()**: Disables the laser.
# 
# **pulse( interval )**: Eanbles the laser for the time interval, given in milliseconds.
# 
# **oscillate( up, down, count )**: Oscillates the enable/disable state of the laser. `up` indicates the enable time, and `down` indicates the disabled time, in milliseconds. `count` defines how many oscillations should occur before disabling the laser.
# 
# **diagnostics()**: Gets the diagnostics read out from the laser.
# 
# **run( command )**: Sends `command` to the controller. 
#     
# **cancel( id )**: Cancels the timer event with the given id.
#     
# ## Response:
# To initiate communication, `init` can be sent to the controller, which responds with `init`. For any other string a JSON response with keys `status`, `command`, `id`, and `response` is provided. The included keys may vary depending on the command sent, however `status` and `command` are always included. 
# 
# `status` can be either 'success' or 'error'.
# 
# `command` is an echo of the command the response is responding to.
# 
# `id` is the timer id of the command, which can be used to cancel it.
# 
# `response` is the response of the command.
# 
# ## Closing the Controller
# After use be sure to close the serial connection to the laser. This can be done temporarily using the `disconnect()` function, and is also done automatically upon destruction.
# ~~~
# lc.disconnect()
# del lc
# ~~~
# 

# In[4]:


import sys
import traceback
import re
import serial
import json
import time


# In[6]:


class _Communicator:
    """
    A parent class for the Caller and Listener
    """
    #--- static variables ---
    CONNECTED = 1
    DISCONNECTED = 0
    
    #--- constructor ---
    def __init__( self, port, size = 100 ):
        self.port = port
        self.__port = None
        self.status = _Communicator.DISCONNECTED
        
        self.connect()
        
    #--- destructor ---
    def __del__( self ):
        """
        Closes the port if open
        """
        self.disconnect()
        
    #--- private methods ---
    
    def __readline( self ):
        return self.__port.readline().decode( 'utf-8' )
        
    
    def __writeline( self, message ):
        # check for new line (\n), add if absent
        if message[ -1: ] != '\n':
            message += '\n'
        
        self.__port.write( message.encode( 'utf-8' ) )
    
        
    #--- public methods ---
    
    def connect( self ):
        """
        Connects to the port with the given name
        """
        # already connected
        if self.status == _Communicator.CONNECTED:
            return
        
        try:
            self.__port = serial.Serial( self.port, 9600, timeout = 10 )
            
            while not self.read():
                # wait for communication
                self.write( 'init' )
                
            # clear buffers
            self.__port.reset_output_buffer()
            self.__port.reset_input_buffer()

            self.status = _Communicator.CONNECTED
            
        except Exception as e:
            self.__port = None
            print( e )
            traceback.print_exc()
            
            
    def disconnect( self ):
        """
        Closes the port if open
        """
        if self.__port is not None:
            self.__port.close()
            self.status = self.DISCONNECTED
            
            
    def isConnected( self ):
        return ( self.status == _Communicator.CONNECTED )
    
    
    def read( self  ):
        """
        Gets the oldest item from the buffer if it exists
        """
        return self.__readline()
    
    def write( self, message ):
        # only place message if buffer is not full
        self.__writeline( message )
            


# In[7]:


class LaserController:
    """ Represents the laser controller for the Flare laser """
    
    #--- constructor ---
    
    def __init__( self, port ):      
        self.__port = None
        self.__com = _Communicator( port )
        self.__callbacks = {}
        
    
    #--- destructor ---
    
    def __del__( self ):
        """
        Closes the speaker and listener
        """
        self.disconnect()
        del self.__com
    
    #--- private methods --- 
                                      
    def __parseResponse( self, resp, cmd = None ):
        """
        Gets the response associated with command.
        If cmd is provided, only consider responses whose command match cmd.
        """
        # { status, command, [id], [response] }
        try:
            respObj = json.loads( resp )
            
            # command error
            if respObj[ 'status' ] == 'error':
                raise AttributeError( 'Invalid command: ' + respObj[ 'command'] )
            
            # successful run 
            if 'response' in respObj and 'id' in respObj:
                return { 
                    'id': respObj[ 'id' ], 
                    'response': respObj[ 'response' ] 
                }
            
            elif 'response' in respObj:
                return respObj[ 'response' ]
            
            elif 'id' in respObj:
                return respObj[ 'id' ]
            
            else:
                return True
        
        except json.JSONDecodeError as err:
            print( '[FlaserLaserControl] Invalid response: ', resp )
            raise err
        
        
    def __getResponse( self, cmd = None ):
        """
        Waits for response from command returning the commands status.
        
        :param cmd: The command filter
        :returns: Upon successful execution, returns the timer id if one was provided, or True if not.
                    Returns False on error.
        """
       
        try:
            return self.__parseResponse( self.__com.read(), cmd )
        except json.JSONDecodeError as err:
            raise err        
            
            
    def __execute( self, cmd ):
        """
        Executes the given command and returns the response.
        
        :param cmd: The command to run.
        """
        try:
            self.__com.write( cmd );
            return self.__getResponse( cmd )
        
        except json.JSONDecodeError as err:
            raise err
            
    
    #--- public methods ---
    
    @property
    def port( self ):
        """
        Returns the port for connection
        """
        return self.__com.port
    
    
    def isConnected( self ):
        """
        Returns true if communication is available, false otherwise
        """
        return self.__com.isConnected()
    
    
    def connect( self ):
        """
        Connects to the port with the given name
        """
        try:
            self.__com.connect()
            
        except Exception as e:
            self.__port = None
            print( e )
            traceback.print_exc()
        
        
    def disconnect( self ):
        """
        Closes the port if open
        """
        self.__com.disconnect()
        
    
    def run( self, cmd ):
        """
        Runs the given command
        
        :param cmd: The command to run.
        :returns: Returns the status of the command.
        """
        return self.__execute( cmd )
    
    
    def status( self ):
        """
        Return the status of the laser. 1 for enabled, 0 for disabled.
        """
        return self.__execute( "run[ status ]" )
        
                    
    def enable( self ):
        """
        Enable the laser.
        """
        return self.__execute( "run[ enable ]" )
    
        
    def disable( self ):
        """
        Disable the laser.
        """
        return self.__execute( "run[ disable ]" )
    
        
    def pulse( self, interval ):
        """
        Enable the laser for a time <interval>.
        
        :param interval: The enable time in milliseconds.
        """
        cmd = "run[ pulse, {} ]".format( interval )
        return self.__execute( cmd )
    
        
    def oscillate( self, up, down = False, count = -1 ):
        """
        Oscillates the enable/disable state of the laser.
        
        :param up: The enable time in milliseconds.
        :param down: The disable time in milliseconds. [Defaults to up time]
        :param count: The number of oscillations to execute. [Defaults to infinity]
        """
        if not down: 
            down = up
        
        cmd = "run[ oscillate, {}, {}, {} ]".format( up, down, count )
        return self.__execute( cmd )
    
        
    def cancel( self, id ):
        """
        Cancels a timer event by id.
        
        :param id: The id of the timer event to cancel.
        """
        cmd = "run[ cancel, {} ]".format( id )
        return self.__execute( cmd )


# ## Main Function
# Used for CLI

# In[ ]:


def printHelp():
    print( """
Flare Laser Controller CLI
    
Use:
python flare_lasercontroller.py <function> [arguments]
<function> is the laser function to be run
[arguments] is a space separated list of arguments passed to the function

API:
+ status(): Returns the status of the laser in the id field. 1 is enabled, 0 is disabled.
+ enable(): Enables the laser.
+ disable(): Disables the laser.
+ pulse( interval ): Eanbles the laser for the time interval, given in milliseconds.
+ oscillate( up, down, count ): Oscillates the enable/disable state of the laser. up indicates the enable time, and down indicates the disabled time, in milliseconds. count defines how many oscillations should occur before disabling the laser.
+ diagnostics(): Gets the diagnostics read out from the laser.
+ run( command ): Sends command to the controller.
+ cancel( id ): Cancels the timer event with the given id.

Response:
A JSON string with keys 'status', 'command', 'id', and 'response'. 
The included keys may vary depending on the command sent, however 'status' and 'command' are always included.

+ 'status' can be either 'success' or 'error'.
+ 'command' is an echo of the command the response is responding to.
+ 'id' is the timer id of the command, which can be used to cancel it.
+ 'response' is the response of the command.
    """ )


# In[9]:


if __name__ == '__main__':
    import getopt
    
    # defaults
    port = "COM4"
    
    # parse options
    try:
        opts, args = getopt.getopt( 
            sys.argv[ 1: ], 
            "hp:", 
            ["help", "port="] 
        )
    
    except getopt.GetoptError:
        printHelp()
        sys.exit( 2 )
        
    for opt, val in opts:
        if opt in ( "-h", "--help" ):
            printHelp()
            sys.exit()
                                   
        elif opt in ( "-p", "--port" ):
            port = val
    
    if len( sys.argv ) == 1:
        # no arguments passed
        printHelp()
        sys.exit( 2 )
      
    # run function
    fcn = args[ 0 ]
    fargs = args[ 1: ]
    
    lc = LaserController( port )
    
    try:
        func = getattr( lc, fcn )
        resp = func( *fargs )
        print( resp )
        del lc
    
    except AttributeError:
        print( "Invalid command. Use -h or --help options for use." )
    
    sys.exit()


# ## Events (deprecated)
# Upon connection the LaserController will emit a `ready` event, indicating serial communication is possible. To register calls with the LaserController use the `on()` method.
# ~~~
# lc.on( 'ready', <callback>, [arg list] )
# ~~~
# 
# To trigger events on the LaserController use the `trigger()` method.
# ~~~
# lc.trigger( 'custom-event' )
# ~~~
# 
# ## Events Code
# ~~~
#  def on( self, event, callback, *args ):
#     """
#     Register events with the object
# 
#     :param event: The name of the event
#     :param callback: The callback function
#     """
#     # add event callback if doesn't exist
#     if event not in self.__callbacks:
#         self.__callbacks[ event ] = []
# 
#     # add callback to event
#     self.__callbacks[ event ].append( [ callback, args ] )
#         
#         
# def trigger( self, event ):
#     """
#     Triggers registered events
# 
#     :param event: The event to trigger
#     """
#     if event in self.__callbacks:
#         for callback in self.__callbacks[ event ]:
#             fcn = callback[ 0 ]
#             args = callback[ 1 ]
# 
#             if len( args ):
#                 # arguments passed
#                 fcn( *args )
#             else:
#                 fcn()
# ~~~
