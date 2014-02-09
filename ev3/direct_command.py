"""A simple interface for executing bytecodes over a Bluetooth serial port.

From the lms2012 source code documentation:

Beside running user programs the VM is able to execute direct commands from
the Communication Module. In fact direct commands are small programs that
consist of regular byte codes and they are executed in parallel with a running
user program. Special care MUST be taken when writing direct commands because
the decision until now is NOT to restrict the use of "dangerous" codes and
constructions (loops in a direct command are allowed).

If a new direct command from the same source is going to be executed an actual
running direct command is terminated.

Because of a small header objects are limited to one VMTHREAD only - SUBCALLs
and BLOCKs are, of course, not possible. This header contains information about
the number of global variables (for response), number of local variables, and
command size.

Direct commands that have data responses can place the data in the global
variable space. The global variable space is equal to the communication
response buffer. The composition of the direct command defines at which
offset the result is placed (global variable 0 is placed at offset 0 in
the buffer).

Offsets in the response buffer (global variables) must be aligned (i.e. 32bit
variable offsets are divisible by 4, 16bit variable offsets are divisible by 2).

All multi-byte words are little endian.

Direct Command bytes:
------------------------------
Byte 0 - 1: Command size
Byte 2 - 3: Message counter
Byte 4:     CommandType
Byte 5 - 6: Number of global and local variables (compressed).
            Byte 6    Byte 5
            76543210  76543210
            --------  --------
            llllllgg  gggggggg
                  gg  gggggggg  Global variables [0..MAX_COMMAND_GLOBALS]
            llllll              Local variables  [0..MAX_COMMAND_LOCALS]
Byte 7 - n: Byte codes

Direct Command response Bytes:
------------------------------
Byte 0 - 1: Reply size
Byte 2 - 3: Message counter
Byte 4:     ReplyType
Byte 5 - n: Response buffer (global variable values)

"""


import ev3
import message


MAX_CMD_LEN = 1019          # The size of the brick's txBuf is 1024 bytes but
                            # the header requires 5 bytes.
MAX_STR_LEN = 255
MAX_VERSION_STR_LEN = 64
MAX_LOCAL_VARIABLE_BYTES = 0xFFFFFFFF

MAX_NAME_STR_LEN = 64

MOTOR_MIN_POWER = -100
MOTOR_MAX_POWER = 100

MOTOR_MIN_SPEED = -100
MOTOR_MAX_SPEED = 100

USB_CHAIN_LAYER_MASTER = 0
USB_CHAIN_LAYER_SLAVE = 1

MOTOR_MIN_RATIO = -200
MOTOR_MAX_RATIO = 200

MIN_VOLUME = 0
MAX_VOLUME = 100

LCD_HEIGHT_PIXELS = 128
LCD_WIDTH_PIXELS = 178


class DirectCommandError(Exception):
    """Subclass for reporting errors."""
    pass


class CommandType(object):
    """Every System Command must be one of these two types."""
    DIRECT_COMMAND_REPLY    = 0x00
    DIRECT_COMMAND_NO_REPLY = 0x80


class ReplyType(object):
    """Every reply to a System Command must be one of these two types."""
    DIRECT_REPLY            = 0x02
    DIRECT_REPLY_ERROR      = 0x04


class OutputPort(object):
    """These can be OR'd together to operate on multiple ports at once."""
    PORT_A   = 0x01
    PORT_B   = 0x02
    PORT_C   = 0x04
    PORT_D   = 0x08
    ALL      = (PORT_A | PORT_B | PORT_C | PORT_D)


class InputPort(object):
    """These can be OR'd together to operate on multiple ports at once."""
    PORT_1   = 0x00
    PORT_2   = 0x01
    PORT_3   = 0x02
    PORT_4   = 0x03
    PORT_A   = 0x10
    PORT_B   = 0x11
    PORT_C   = 0x12
    PORT_D   = 0x13


class StopType(object):
    """When an OutputPort is stopped it can be told to brake or coast."""
    COAST   = 0
    BRAKE   = 1


class PolarityType(object):
    """"""
    BACKWARD    = -1
    TOGGLE      = 0
    FORWARD     = 1


class TouchMode(object):
    """"""
    TOUCH   = 0
    BUMPS   = 1


class NXTLightMode(object):
    """"""
    REFLECT = 0
    AMBIENT = 1


class NXTSoundMode(object):
    """"""
    DECIBELS            = 0
    ADJUSTED_DECIBLES   = 1


class NXTColorMode(object):
    """"""
    REFLECTIVE  = 0
    AMBIENT     = 1
    COLOR       = 2
    GREEN       = 3
    BLUE        = 4
    RAW         = 5


class NXTUltrasonicMode(object):
    """"""
    CM      = 0
    INCHES  = 1


class NXTTemperatureMode(object):
    """"""
    CELSIUS     = 0
    FAHRENHEIT  = 1


class MotorMode(object):
    """"""
    DEGREES     = 0
    ROTATIONS   = 1
    PERCENT     = 2


class UltrasonicMode(object):
    """"""
    CM      = 0
    INCH    = 1
    LISTEN  = 2


class GyroMode(object):
    """"""
    ANGLE   = 0
    RATE    = 1
    FAS     = 2
    G_AND_A = 3


class IRMode(object):
    """"""
    PROXIMITY   = 0
    SEEK        = 1
    REMOTE      = 2
    REMOTE_A    = 3
    SALT        = 4
    CALIBRATION = 5


class ColorMode(object):
    """"""
    RELECTIVE   = 0
    AMBIENT     = 1
    COLOR       = 2


class ColorSensorColor(object):
    """These are the results that the EV3 color sensor can return when operating
    in ColorMode.COLOR.

    """
    NONE    = 0
    BLACK   = 1
    BLUE    = 2
    GREEN   = 3
    YELLOW  = 4
    RED     = 5
    WHITE   = 6
    BROWN   = 7


class LEDPattern(object):
    """The brick user interface has several status LEDs."""
    OFF                 = 0
    GREEN               = 1
    RED                 = 2
    ORANGE              = 3
    FLASHING_GREEN      = 4
    FLASHING_RED        = 5
    FLASHING_ORANGE     = 6
    GREEN_HEARTBEAT     = 7
    RED_HEARTBEAT       = 8
    ORANGE_HEARTBEAT    = 9


class DeviceType(object):
    """These are the known device types.

    NOTE:   These have only been partially confirmed.

    """
    NXT_TOUCH           = 0x01
    NXT_LIGHT           = 0x02
    NXT_SOUND           = 0x03
    NXT_COLOR           = 0x04
    NXT_ULTRASONIC      = 0x05
    NXT_TEMPERATURE     = 0x06
    TACHO               = 0x07  # TYPE_TACHO in lms2012.h
    MINI_TACHO          = 0x08  # TYPE_MINITACHO in lms2012.h
    NEW_TACHO           = 0x09  # TYPE_NEWTACHO in lms2012.h
    EV3_TOUCH           = 0x10
    EV3_COLOR           = 0x1D
    EV3_ULTRASONIC      = 0x1E
    EV3_GYROSCOPE       = 0x20
    EV3_INFRARED        = 0x21
    SENSOR_INITIALIZING = 0x7D
    PORT_EMPTY          = 0x7E
    ERROR_PORT          = 0x7F
    UNKNOWN             = 0xFF


class LCDColor(object):
    """The brick's LCD only displays two colors."""
    BACKGROUND = 0
    FOREGROUND = 1


class ButtonType(object):
    """The brick's user interface contains 6 buttons."""
    NO_BUTTON       = 0
    UP_BUTTON       = 1
    ENTER_BUTTON    = 2
    DOWN_BUTTON     = 3
    RIGHT_BUTTON    = 4
    LEFT_BUTTON     = 5
    BACK_BUTTON     = 6
    ANY_BUTTON      = 7


class MathType(object):
    """"""
    EXP       = 1     # e^x            r = expf(x)
    MOD       = 2     # Modulo         r = fmod(x,y)
    FLOOR     = 3     # Floor          r = floor(x)
    CEIL      = 4     # Ceiling        r = ceil(x)
    ROUND     = 5     # Round          r = round(x)
    ABS       = 6     # Absolute       r = fabs(x)
    NEGATE    = 7     # Negate         r = 0.0 - x
    SQRT      = 8     # Squareroot     r = sqrt(x)
    LOG       = 9     # Log            r = log10(x)
    LN        = 10    # Ln             r = log(x)
    SIN       = 11
    COS       = 12
    TAN       = 13
    ASIN      = 14
    ACOS      = 15
    ATAN      = 16
    MOD8      = 17    # Modulo DATA8   r = x % y
    MOD16     = 18    # Modulo DATA16  r = x % y
    MOD32     = 19    # Modulo DATA32  r = x % y
    POW       = 20    # Exponent       r = powf(x,y)
    TRUNC     = 21    # Truncate       r = (float)((int)(x * pow(y))) / pow(y)


class BrowserType(object):
    """"""
    BROWSE_FOLDERS      = 0 # Browser for folders
    BROWSE_FOLDS_FILES  = 1 # Browser for folders and files
    BROWSE_CACHE        = 2 # Browser for cached / recent files
    BROWSE_FILES        = 3 # Browser for files


class Icon(object):
    """The icons on the brick are enumerated by value."""
    ICON_NONE           = -1
    ICON_RUN            = 0
    ICON_FOLDER         = 1
    ICON_FOLDER2        = 2
    ICON_USB            = 3
    ICON_SD             = 4
    ICON_SOUND          = 5
    ICON_IMAGE          = 6
    ICON_SETTINGS       = 7
    ICON_ONOFF          = 8
    ICON_SEARCH         = 9
    ICON_WIFI           = 10
    ICON_CONNECTIONS    = 11
    ICON_ADD_HIDDEN     = 12
    ICON_TRASHBIN       = 13
    ICON_VISIBILITY     = 14
    ICON_KEY            = 15
    ICON_CONNECT        = 16
    ICON_DISCONNECT     = 17
    ICON_UP             = 18
    ICON_DOWN           = 19
    ICON_WAIT1          = 20
    ICON_WAIT2          = 21
    ICON_BLUETOOTH      = 22
    ICON_INFO           = 23
    ICON_TEXT           = 24
    ICON_QUESTIONMARK   = 27
    ICON_INFO_FILE      = 28
    ICON_DISC           = 29
    ICON_CONNECTED      = 30
    ICON_OBP            = 31
    ICON_OBD            = 32
    ICON_OPENFOLDER     = 33
    ICON_BRICK1         = 34


class FontType(object):
    """"""
    NORMAL_FONT = 0
    SMALL_FONT  = 1
    LARGE_FONT  = 2
    TINY_FONT   = 3


class DataFormat(object):
    """Data formats that are used by the VM."""
    DATA8       = 0x00
    DATA16      = 0x01
    DATA32      = 0x02
    DATA_F      = 0x03  # 32bit floating point value (single precision)
    DATA_S      = 0x04  # Zero terminated string
    DATA_A      = 0x05  # Array handle
    DATA_V      = 0x07  # Variable type
    DATA_PCT    = 0x10  # Percent (used in INPUT_READEXT)
    DATA_RAW    = 0x12  # Raw     (used in INPUT_READEXT)
    DATA_SI     = 0x13  # SI unit (used in INPUT_READEXT)
    # Values used by this Python module only:
    HND         = 0xFF  # For compatibility with ParamTypes.
    BOOL        = 0xFE  # For converting to Python values


class ParamType(object):
    """Parameter types that are used by the VM."""
    PRIMPAR_LABEL   = 0x20
    HND             = 0x10  # 8bit handle index (i.e. pointer to a string)
    ADR             = 0x08  # 3bit address
    LCS             = 0x84  # Null terminated string
    LAB1            = 0xA0
    LC0             = 0x00  # 6bit immediate
    LC1             = 0x81  # 8bit immediate
    LC2             = 0x82  # 16bit immediate
    LC4             = 0x83  # 32bit immediate
    LCA             = 0x81  # 8bit pointer to local array
    LV1             = 0xC1  # 8bit pointer to local value
    LV2             = 0xC2  # 16bit pointer to local value
    LV4             = 0xC3  # 32bit pointer to local value
    LVA             = 0xC1  # 8bit pointer to local array
    GV0             = 0x60  # 5bit pointer to global value
    GV1             = 0xE1  # 8bit pointer to global value
    GV2             = 0xE2  # 16bit pointer to global value
    GV4             = 0xE3  # 32bit pointer to global value
    GVA             = 0xE1  # 8bit pointer to global array
    # Values used by this Python module only:
    FLOAT           = 0xFF  # 32bit floating point value (single precision)


# Defines the number of bytes required to represent each DataFormat.
PARAM_TYPE_LENS = { ParamType.PRIMPAR_LABEL:    None,
                    ParamType.HND:              1,
                    ParamType.ADR:              1,
                    ParamType.LCS:              None,
                    ParamType.LAB1:             1,
                    ParamType.LC0:              0,
                    ParamType.LC1:              1,
                    ParamType.LC2:              2,
                    ParamType.LC4:              4,
                    ParamType.LCA:              1,
                    ParamType.LV1:              1,
                    ParamType.LV2:              2,
                    ParamType.LV4:              4,
                    ParamType.LVA:              1,
                    ParamType.GV0:              0,
                    ParamType.GV1:              1,
                    ParamType.GV2:              2,
                    ParamType.GV4:              4,
                    ParamType.GVA:              1,
                    ParamType.FLOAT:            4 }


DATA_FORMAT_LENS = {    DataFormat.DATA8:       1,
                        DataFormat.DATA16:      2,
                        DataFormat.DATA32:      4,
                        DataFormat.DATA_F:      4,
                        DataFormat.DATA_S:      None,
                        DataFormat.DATA_A:      None,
                        DataFormat.DATA_V:      None,
                        DataFormat.DATA_PCT:    1,
                        DataFormat.DATA_RAW:    4,
                        DataFormat.DATA_SI:     4,
                        DataFormat.HND:         1,
                        DataFormat.BOOL:        1 }


# There are two ways to specify an output in the c_output module. The first is
# as a bit mask and the second is by index.
OUTPUT_CHANNEL_TO_INDEX =   {   OutputPort.PORT_A: 0,
                                OutputPort.PORT_B: 1,
                                OutputPort.PORT_C: 2,
                                OutputPort.PORT_D: 3 }


class UIReadSubcode(object):
    """"""
    GET_VBATT     = 1
    GET_IBATT     = 2
    GET_OS_VERS   = 3
    GET_EVENT     = 4
    GET_TBATT     = 5
    GET_IINT      = 6
    GET_IMOTOR    = 7
    GET_STRING    = 8
    GET_HW_VERS   = 9
    GET_FW_VERS   = 10
    GET_FW_BUILD  = 11
    GET_OS_BUILD  = 12
    GET_ADDRESS   = 13
    GET_CODE      = 14
    KEY           = 15
    GET_SHUTDOWN  = 16
    GET_WARNING   = 17
    GET_LBATT     = 18
    TEXTBOX_READ  = 21
    GET_VERSION   = 26
    GET_IP        = 27
    GET_POWER     = 29
    GET_SDCARD    = 30
    GET_USBSTICK  = 31


class UIWriteSubcode(object):
    """"""
    WRITE_FLUSH     = 1
    FLOATVALUE      = 2
    STAMP           = 3
    PUT_STRING      = 8
    VALUE8          = 9
    VALUE16         = 10
    VALUE32         = 11
    VALUEF          = 12
    ADDRESS         = 13
    CODE            = 14
    DOWNLOAD_END    = 15
    SCREEN_BLOCK    = 16
    TEXTBOX_APPEND  = 21
    SET_BUSY        = 22
    SET_TESTPIN     = 24
    INIT_RUN        = 25
    UPDATE_RUN      = 26
    LED             = 27
    POWER           = 29
    GRAPH_SAMPLE    = 30
    TERMINAL        = 31


class UIButtonSubcode(object):
    """"""
    SHORTPRESS      = 1
    LONGPRESS       = 2
    WAIT_FOR_PRESS  = 3
    FLUSH           = 4
    PRESS           = 5
    RELEASE         = 6
    GET_HORZ        = 7
    GET_VERT        = 8
    PRESSED         = 9
    SET_BACK_BLOCK  = 10
    GET_BACK_BLOCK  = 11
    TESTSHORTPRESS  = 12
    TESTLONGPRESS   = 13
    GET_BUMBED      = 14
    GET_CLICK       = 15


class COMGetSubcodes(object):
    """"""
    GET_ON_OFF      = 1     # Set, Get
    GET_VISIBLE     = 2     # Set, Get
    GET_RESULT      = 4     # Get
    GET_PIN         = 5     # Set, Get
    SEARCH_ITEMS    = 8     # Get
    SEARCH_ITEM     = 9     # Get
    FAVOUR_ITEMS    = 10    # Get
    FAVOUR_ITEM     = 11    # Get
    GET_ID          = 12
    GET_BRICKNAME   = 13
    GET_NETWORK     = 14
    GET_PRESENT     = 15
    GET_ENCRYPT     = 16
    CONNEC_ITEMS    = 17
    CONNEC_ITEM     = 18
    GET_INCOMING    = 19
    GET_MODE2       = 20


class COMSetSubcode(object):
    """"""
    SET_ON_OFF      = 1     # Set, Get
    SET_VISIBLE     = 2     # Set, Get
    SET_SEARCH      = 3     # Set
    SET_PIN         = 5     # Set, Get
    SET_PASSKEY     = 6     # Set
    SET_CONNECTION  = 7     # Set
    SET_BRICKNAME   = 8
    SET_MOVEUP      = 9
    SET_MOVEDOWN    = 10
    SET_ENCRYPT     = 11
    SET_SSID        = 12
    SET_MODE2       = 13


class InputDeviceSubcode(object):
    """"""
    GET_FORMAT      = 2
    CAL_MINMAX      = 3
    CAL_DEFAULT     = 4
    GET_TYPEMODE    = 5
    GET_SYMBOL      = 6
    CAL_MIN         = 7
    CAL_MAX         = 8
    SETUP           = 9     # Probably only for internal use.
    CLR_ALL         = 10    # Resets counters, angle, etc.
    GET_RAW         = 11
    GET_CONNECTION  = 12
    STOP_ALL        = 13    # Stops any attached motors?
    GET_NAME        = 21
    GET_MODENAME    = 22
    SET_RAW         = 23
    GET_FIGURES     = 24
    GET_CHANGES     = 25
    CLR_CHANGES     = 26
    READY_PCT       = 27
    READY_RAW       = 28
    READY_SI        = 29
    GET_MINMAX      = 30
    GET_BUMPS       = 31


class ProgramInfoSubcode(object):
    """"""
    OBJ_STOP        = 0
    OBJ_START       = 4
    GET_STATUS      = 22
    GET_SPEED       = 23
    GET_PRGRESULT   = 24
    SET_INSTR       = 25


class UIDrawSubcode(object):
    """"""
    UPDATE          = 0
    CLEAN           = 1
    PIXEL           = 2
    LINE            = 3
    CIRCLE          = 4
    TEXT            = 5
    ICON            = 6
    PICTURE         = 7
    VALUE           = 8
    FILLRECT        = 9
    RECT            = 10
    NOTIFICATION    = 11
    QUESTION        = 12
    KEYBOARD        = 13
    BROWSE          = 14
    VERTBAR         = 15
    INVERSERECT     = 16
    SELECT_FONT     = 17
    TOPLINE         = 18
    FILLWINDOW      = 19
    SCROLL          = 20
    DOTLINE         = 21
    VIEW_VALUE      = 22
    VIEW_UNIT       = 23
    FILLCIRCLE      = 24
    STORE           = 25
    RESTORE         = 26
    ICON_QUESTION   = 27
    BMPFILE         = 28
    POPUP           = 29
    GRAPH_SETUP     = 30
    GRAPH_DRAW      = 31
    TEXTBOX         = 32


class FileSubcode(object):
    """"""
    OPEN_APPEND         = 0
    OPEN_READ           = 1
    OPEN_WRITE          = 2
    READ_VALUE          = 3
    WRITE_VALUE         = 4
    READ_TEXT           = 5
    WRITE_TEXT          = 6
    CLOSE               = 7
    LOAD_IMAGE          = 8
    GET_HANDLE          = 9
    MAKE_FOLDER         = 10
    GET_POOL            = 11
    SET_LOG_SYNC_TIME   = 12
    GET_FOLDERS         = 13
    GET_LOG_SYNC_TIME   = 14
    GET_SUBFOLDER_NAME  = 15
    WRITE_LOG           = 16
    CLOSE_LOG           = 17
    GET_IMAGE           = 18
    GET_ITEM            = 19
    GET_CACHE_FILES     = 20
    PUT_CACHE_FILE      = 21
    GET_CACHE_FILE      = 22
    DEL_CACHE_FILE      = 23
    DEL_SUBFOLDER       = 24
    GET_LOG_NAME        = 25
    OPEN_LOG            = 27
    READ_BYTES          = 28
    WRITE_BYTES         = 29
    REMOVE              = 30
    MOVE                = 31


class ArraySubcode(object):
    """"""
    DELETE          = 0
    CREATE8         = 1
    CREATE16        = 2
    CREATE32        = 3
    CREATEF         = 4
    RESIZE          = 5
    FILL            = 6
    COPY            = 7
    INIT8           = 8
    INIT16          = 9
    INIT32          = 10
    INITF           = 11
    SIZE            = 12
    READ_CONTENT    = 13
    WRITE_CONTENT   = 14
    READ_SIZE       = 15


class FilenameSubcode(object):
    """"""
    EXIST           = 16    # MUST BE GREATER OR EQUAL TO "ARRAY_SUBCODES"
    TOTALSIZE       = 17
    SPLIT           = 18
    MERGE           = 19
    CHECK           = 20
    PACK            = 21
    UNPACK          = 22
    GET_FOLDERNAME  = 23


class InfoSubcode(object):
    """"""
    SET_ERROR   = 1
    GET_ERROR   = 2
    ERRORTEXT   = 3
    GET_VOLUME  = 4
    SET_VOLUME  = 5
    GET_MINUTES = 6
    SET_MINUTES = 7


class SoundSubcode(object):
    """"""
    BREAK   = 0
    TONE    = 1
    PLAY    = 2
    REPEAT  = 3
    SERVICE = 4


class StringSubcode(object):
    """"""
    GET_SIZE            = 1     # Get string size
    ADD                 = 2     # Add two strings
    COMPARE             = 3     # Compare two strings
    DUPLICATE           = 5     # Duplicate one string to another
    VALUE_TO_STRING     = 6
    STRING_TO_VALUE     = 7
    STRIP               = 8
    NUMBER_TO_STRING    = 9
    SUB                 = 10
    VALUE_FORMATTED     = 11
    NUMBER_FORMATTED    = 12


class TstSubcode(object):
    """"""
    TST_OPEN            = 10    # Must >= "INFO_SUBCODES"
    TST_CLOSE           = 11
    TST_READ_PINS       = 12
    TST_WRITE_PINS      = 13
    TST_READ_ADC        = 14
    TST_WRITE_UART      = 15
    TST_READ_UART       = 16
    TST_ENABLE_UART     = 17
    TST_DISABLE_UART    = 18
    TST_ACCU_SWITCH     = 19
    TST_BOOT_MODE2      = 20
    TST_POLL_MODE2      = 21
    TST_CLOSE_MODE2     = 22
    TST_RAM_CHECK       = 23


class Opcode(object):
    """All of the opcodes that are used by the VM."""
    ERROR               = 0x00
    NOP                 = 0x01
    PROGRAM_STOP        = 0x02
    PROGRAM_START       = 0x03
    OBJECT_STOP         = 0x04
    OBJECT_START        = 0x05
    OBJECT_TRIG         = 0x06
    OBJECT_WAIT         = 0x07
    RETURN              = 0x08
    CALL                = 0x09
    OBJECT_END          = 0x0A
    SLEEP               = 0x0B
    PROGRAM_INFO        = 0x0C
    LABEL               = 0x0D
    PROBE               = 0x0E
    DO                  = 0x0F
    # MATH
    ADD8                = 0x10
    ADD16               = 0x11
    ADD32               = 0x12
    ADDF                = 0x13
    SUB8                = 0x14
    SUB16               = 0x15
    SUB32               = 0x16
    SUBF                = 0x17
    MUL8                = 0x18
    MUL16               = 0x19
    MUL32               = 0x1A
    MULF                = 0x1B
    DIV8                = 0x1C
    DIV16               = 0x1D
    DIV32               = 0x1E
    DIVF                = 0x1F
    # LOGIC
    OR8                 = 0x20
    OR16                = 0x21
    OR32                = 0x22
    AND8                = 0x24
    AND16               = 0x25
    AND32               = 0x26
    XOR8                = 0x28
    XOR16               = 0x29
    XOR32               = 0x2A
    RL8                 = 0x2C
    RL16                = 0x2D
    RL32                = 0x2E
    # MOVE
    INIT_BYTES          = 0x2F
    MOVE8_8             = 0x30
    MOVE8_16            = 0x31
    MOVE8_32            = 0x32
    MOVE8_F             = 0x33
    MOVE16_8            = 0x34
    MOVE16_16           = 0x35
    MOVE16_32           = 0x36
    MOVE16_F            = 0x37
    MOVE32_8            = 0x38
    MOVE32_16           = 0x39
    MOVE32_32           = 0x3A
    MOVE32_F            = 0x3B
    MOVEF_8             = 0x3C
    MOVEF_16            = 0x3D
    MOVEF_32            = 0x3E
    MOVEF_F             = 0x3F
    # BRANCH
    JR                  = 0x40
    JR_FALSE            = 0x41
    JR_TRUE             = 0x42
    JR_NAN              = 0x43
    # COMPARE
    CP_LT8              = 0x44
    CP_LT16             = 0x45
    CP_LT32             = 0x46
    CP_LTF              = 0x47
    CP_GT8              = 0x48
    CP_GT16             = 0x49
    CP_GT32             = 0x4A
    CP_GTF              = 0x4B
    CP_EQ8              = 0x4C
    CP_EQ16             = 0x4D
    CP_EQ32             = 0x4E
    CP_EQF              = 0x4F
    CP_NEQ8             = 0x50
    CP_NEQ16            = 0x51
    CP_NEQ32            = 0x52
    CP_NEQF             = 0x53
    CP_LTEQ8            = 0x54
    CP_LTEQ16           = 0x55
    CP_LTEQ32           = 0x56
    CP_LTEQF            = 0x57
    CP_GTEQ8            = 0x58
    CP_GTEQ16           = 0x59
    CP_GTEQ32           = 0x5A
    CP_GTEQF            = 0x5B
    # SELECT
    SELECT8             = 0x5C
    SELECT16            = 0x5D
    SELECT32            = 0x5E
    SELECTF             = 0x5F
    SYSTEM              = 0x60
    PORT_CNV_OUTPUT     = 0x61
    PORT_CNV_INPUT      = 0x62
    NOTE_TO_FREQ        = 0x63
    # BRANCH
    JR_LT8              = 0x64
    JR_LT16             = 0x65
    JR_LT32             = 0x66
    JR_LTF              = 0x67
    JR_GT8              = 0x68
    JR_GT16             = 0x69
    JR_GT32             = 0x6A
    JR_GTF              = 0x6B
    JR_EQ8              = 0x6C
    JR_EQ16             = 0x6D
    JR_EQ32             = 0x6E
    JR_EQF              = 0x6F
    JR_NEQ8             = 0x70
    JR_NEQ16            = 0x71
    JR_NEQ32            = 0x72
    JR_NEQF             = 0x73
    JR_LTEQ8            = 0x74
    JR_LTEQ16           = 0x75
    JR_LTEQ32           = 0x76
    JR_LTEQF            = 0x77
    JR_GTEQ8            = 0x78
    JR_GTEQ16           = 0x79
    JR_GTEQ32           = 0x7A
    JR_GTEQF            = 0x7B
    # VM
    INFO                = 0x7C
    STRINGS             = 0x7D
    MEMORY_WRITE        = 0x7E
    MEMORY_READ         = 0x7F
    # UI
    UI_FLUSH            = 0x80
    UI_READ             = 0x81
    UI_WRITE            = 0x82
    UI_BUTTON           = 0x83
    UI_DRAW             = 0x84
    # TIMER
    TIMER_WAIT          = 0x85
    TIMER_READY         = 0x86
    TIMER_READ          = 0x87
    # BREAKPOINT
    BP0                 = 0x88
    BP1                 = 0x89
    BP2                 = 0x8A
    BP3                 = 0x8B
    BP_SET              = 0x8C
    MATH                = 0x8D
    RANDOM              = 0x8E
    # TIMER
    TIMER_READ_US       = 0x8F
    # UI
    KEEP_ALIVE          = 0x90
    # COM
    COM_READ            = 0x91
    COM_WRITE           = 0x92
    # SOUND
    SOUND               = 0x94
    SOUND_TEST          = 0x95
    SOUND_READY         = 0x96
    # INPUT
    INPUT_SAMPLE        = 0x97
    INPUT_DEVICE_LIST   = 0x98
    INPUT_DEVICE        = 0x99
    INPUT_READ          = 0x9A
    INPUT_TEST          = 0x9B
    INPUT_READY         = 0x9C
    INPUT_READSI        = 0x9D
    INPUT_READEXT       = 0x9E
    INPUT_WRITE         = 0x9F
    # OUTPUT
    OUTPUT_GET_TYPE     = 0xA0
    OUTPUT_SET_TYPE     = 0xA1
    OUTPUT_RESET        = 0xA2
    OUTPUT_STOP         = 0xA3
    OUTPUT_POWER        = 0xA4
    OUTPUT_SPEED        = 0xA5
    OUTPUT_START        = 0xA6
    OUTPUT_POLARITY     = 0xA7
    OUTPUT_READ         = 0xA8
    OUTPUT_TEST         = 0xA9
    OUTPUT_READY        = 0xAA
    OUTPUT_POSITION     = 0xAB
    OUTPUT_STEP_POWER   = 0xAC
    OUTPUT_TIME_POWER   = 0xAD
    OUTPUT_STEP_SPEED   = 0xAE
    OUTPUT_TIME_SPEED   = 0xAF
    OUTPUT_STEP_SYNC    = 0xB0
    OUTPUT_TIME_SYNC    = 0xB1
    OUTPUT_CLR_COUNT    = 0xB2
    OUTPUT_GET_COUNT    = 0xB3
    OUTPUT_PRG_STOP     = 0xB4
    # MEMORY
    FILE                = 0xC0
    ARRAY               = 0xC1
    ARRAY_WRITE         = 0xC2
    ARRAY_READ          = 0xC3
    ARRAY_APPEND        = 0xC4
    MEMORY_USAGE        = 0xC5
    FILENAME            = 0xC6
    # READ
    READ8               = 0xC8
    READ16              = 0xC9
    READ32              = 0xCA
    READF               = 0xCB
    # WRITE
    WRITE8              = 0xCC
    WRITE16             = 0xCD
    WRITE32             = 0xCE
    WRITEF              = 0xCF
    # COM
    COM_READY           = 0xD0
    COM_READDATA        = 0xD1
    COM_WRITEDATA       = 0xD2
    COM_GET             = 0xD3
    COM_SET             = 0xD4
    COM_TEST            = 0xD5
    COM_REMOVE          = 0xD6
    COM_WRITEFILE       = 0xD7
    MAILBOX_OPEN        = 0xD8
    MAILBOX_WRITE       = 0xD9
    MAILBOX_READ        = 0xDA
    MAILBOX_TEST        = 0xDB
    MAILBOX_READY       = 0xDC
    MAILBOX_CLOSE       = 0xDD
    # SPARE
    TST                 = 0xFF


class DirectCommand(object):
    """Handles variable allocation and parameters for commands that can consist
    of arbitrary bytecodes.

    TODO:   Better param verification?

    """


    # These are inserted into the _global_params_types list so that commands
    # that return mulitple values can have their values bundled together into
    # tuples before they are returned.
    _REPLY_TUPLE_OPEN_TOKEN = '_('
    _REPLY_TUPLE_CLOSE_TOKEN = ')_'


    def __init__(self):
        """Constructs a new, empty object."""
        self._global_params_types = []

        self._local_params_byte_count = 0
        self._global_params_byte_count = 0

        # Allocate space for the CommandType.
        self._msg = [0x00]

        # Allocate space for global and local param lengths.
        self._msg.append(0x00)
        self._msg.append(0x00)


    def send(self, ev3_object):
        """Sends the message and parses the reply."""
        if (2 == len(self._msg)):
            raise DirectCommandError('Attempt to send an empty DirectCommand.')

        self._msg[1] = (self._global_params_byte_count & 0xFF)
        self._msg[2] = ((self._local_params_byte_count << 2) |
                                ((self._global_params_byte_count >> 8) & 0x03))

        if (self._global_params_byte_count):
            self._msg[0] = CommandType.DIRECT_COMMAND_REPLY
            reply = ev3_object.send_message_for_reply(self._msg)

            return self._parse_reply(reply)
        else:
            self._msg[0] = CommandType.DIRECT_COMMAND_NO_REPLY
            ev3_object.send_message(self._msg)


    def safe_add(fn):
        """A wrapper for adding commands in a safe manner."""
        def checked_add(*args):
            # Wrappers aren't bound methods so they can't reference 'self'
            # directly. However, 'self' will be provided as the first parameter
            # when the wrapped method is called.
            _self = args[0]

            msg_len = len(_self._msg)

            global_params_types_len = len(_self._global_params_types)

            local_params_byte_count = _self._local_params_byte_count
            global_params_byte_count = _self._global_params_byte_count

            fn(*args)

            if ((MAX_CMD_LEN < len(_self._msg)) or
                  (MAX_CMD_LEN < _self._global_params_byte_count) or
                  (MAX_LOCAL_VARIABLE_BYTES < _self._local_params_byte_count)):
                del (_self._msg[msg_len:])

                del (_self._global_params_types[global_params_types_len:])

                _self._local_params_byte_count = local_params_byte_count
                _self._global_params_byte_count = global_params_byte_count

                raise DirectCommandError('Not enough space to add the ' +
                                                                'given func.')

        return checked_add


    @safe_add
    def add_timer_wait(self, milliseconds):
        """Causes the thread to sleep for the specified number of milliseconds.

        """
        local_var_tuple = self._allocate_local_param(DataFormat.DATA32)

        self._msg.append(Opcode.TIMER_WAIT)
        self._append_local_constant(milliseconds)
        self._append_param(*local_var_tuple)

        self._msg.append(Opcode.TIMER_READY)
        self._append_param(*local_var_tuple)


    @safe_add
    def add_ui_draw_update(self):
        """Updates the screen (applies whatever drawing commands have been
        issued since the last update).

        """
        self._msg.append(Opcode.UI_DRAW)
        self._msg.append(UIDrawSubcode.UPDATE)


    @safe_add
    def add_ui_draw_clean(self):
        """Fills the screen with LCDColor.BACKGROUND."""
        self._msg.append(Opcode.UI_DRAW)
        self._msg.append(UIDrawSubcode.CLEAN)


    @safe_add
    def add_ui_draw_fillwindow(self, lcd_color, start_y, count):
        """Fills the window with count rows of the given LCDColor starting at
        row start_y.

        NOTE:   Starting at 0 with a size of 0 will clear the window. This seems
                to be the way the CLEAN command is implemented.

        """
        self._msg.append(Opcode.UI_DRAW)
        self._msg.append(UIDrawSubcode.FILLWINDOW)
        self._append_param(lcd_color)
        self._append_param(start_y, ParamType.LC2)
        self._append_param(count, ParamType.LC2)


    @safe_add
    def add_ui_draw_pixel(self, lcd_color, xy):
        """Draws a pixel at the given (x, y)."""
        self._msg.append(Opcode.UI_DRAW)
        self._msg.append(UIDrawSubcode.PIXEL)
        self._append_param(lcd_color)
        self._append_param(xy[0], ParamType.LC2)
        self._append_param(xy[1], ParamType.LC2)


    @safe_add
    def add_ui_draw_line(self, lcd_color, start_xy, end_xy):
        """Draws a line from the start (x, y) to the end (x, y)."""
        self._msg.append(Opcode.UI_DRAW)
        self._msg.append(UIDrawSubcode.LINE)
        self._append_param(lcd_color)
        self._append_param(start_xy[0], ParamType.LC2)
        self._append_param(start_xy[1], ParamType.LC2)
        self._append_param(end_xy[0], ParamType.LC2)
        self._append_param(end_xy[1], ParamType.LC2)


    @safe_add
    def add_ui_draw_dotline(self, lcd_color,
                                    start_xy,
                                    end_xy,
                                    on_pixels,
                                    off_pixels):
        """Draws a line from the start (x, y) to the end (x, y). The line will
        be composed of a repeating pattern consisting of on_pixels followed by
        off_pixels.

        """
        self._msg.append(Opcode.UI_DRAW)
        self._msg.append(UIDrawSubcode.DOTLINE)
        self._append_param(lcd_color)
        self._append_param(start_xy[0], ParamType.LC2)
        self._append_param(start_xy[1], ParamType.LC2)
        self._append_param(end_xy[0], ParamType.LC2)
        self._append_param(end_xy[1], ParamType.LC2)
        self._append_param(on_pixels, ParamType.LC2)
        self._append_param(off_pixels, ParamType.LC2)


    @safe_add
    def add_ui_draw_rect(self, lcd_color, xy, width, height):
        """Draws a rectangle with (x, y) as the top-left corner and with width
        and height dimensions.

        """
        self._msg.append(Opcode.UI_DRAW)
        self._msg.append(UIDrawSubcode.RECT)
        self._append_param(lcd_color)
        self._append_param(xy[0], ParamType.LC2)
        self._append_param(xy[1], ParamType.LC2)
        self._append_param(width, ParamType.LC2)
        self._append_param(height, ParamType.LC2)


    @safe_add
    def add_ui_draw_fillrect(self, lcd_color, xy, width, height):
        """Draws a filled rectangle with (x, y) as the top-left corner and
        with width and height dimensions.

        """
        self._msg.append(Opcode.UI_DRAW)
        self._msg.append(UIDrawSubcode.FILLRECT)
        self._append_param(lcd_color)
        self._append_param(xy[0], ParamType.LC2)
        self._append_param(xy[1], ParamType.LC2)
        self._append_param(width, ParamType.LC2)
        self._append_param(height, ParamType.LC2)


    @safe_add
    def add_ui_draw_inverserect(self, xy, width, height):
        """Draws a rectangle with (x, y) as the top-left corner and with width
        and height dimensions. Any pixel that this rectangle overlaps will have
        its color flipped.

        """
        self._msg.append(Opcode.UI_DRAW)
        self._msg.append(UIDrawSubcode.INVERSERECT)
        self._append_param(xy[0], ParamType.LC2)
        self._append_param(xy[1], ParamType.LC2)
        self._append_param(width, ParamType.LC2)
        self._append_param(height, ParamType.LC2)


    @safe_add
    def add_ui_draw_circle(self, lcd_color, xy, radius):
        """Draws a circle centered at (x, y) with the specified radius."""
        self._msg.append(Opcode.UI_DRAW)
        self._msg.append(UIDrawSubcode.CIRCLE)
        self._append_param(lcd_color)
        self._append_param(xy[0], ParamType.LC2)
        self._append_param(xy[1], ParamType.LC2)
        self._append_param(radius, ParamType.LC2)


    @safe_add
    def add_ui_draw_fillcircle(self, lcd_color, xy, radius):
        """Draws a filled circle centered at (x, y) with the specified radius.

        """
        self._msg.append(Opcode.UI_DRAW)
        self._msg.append(UIDrawSubcode.FILLCIRCLE)
        self._append_param(lcd_color)
        self._append_param(xy[0], ParamType.LC2)
        self._append_param(xy[1], ParamType.LC2)
        self._append_param(radius, ParamType.LC2)


    @safe_add
    def add_ui_draw_selectfont(self, font_type):
        """Selects the FontType that will be used by following calls to
        add_ui_draw_text.

        """
        self._msg.append(Opcode.UI_DRAW)
        self._msg.append(UIDrawSubcode.SELECT_FONT)
        self._append_param(font_type)


    @safe_add
    def add_ui_draw_text(self, lcd_color, xy, text_str):
        """Draws the given text with (x, y) as the top-left corner of the
        bounding box. Use add_ui_draw_selectfont to select the font.

        """
        self._msg.append(Opcode.UI_DRAW)
        self._msg.append(UIDrawSubcode.TEXT)
        self._append_param(lcd_color)
        self._append_param(xy[0], ParamType.LC2)
        self._append_param(xy[1], ParamType.LC2)
        self._append_param(text_str, ParamType.LCS)


    @safe_add
    def add_ui_draw_topline(self, topline_enabled):
        """Enables or disables the display of the menu bar at the top of the
        screen that normally displays status icons such as the battery
        indicator.

        """
        self._msg.append(Opcode.UI_DRAW)
        self._msg.append(UIDrawSubcode.TOPLINE)
        self._append_param(int(topline_enabled))


    @safe_add
    def add_ui_draw_store(self, ui_level_no=0):
        """If ui_level_no is zero then this function saves the current screen
        content so that it be restored later using add_ui_draw_restore.

        """
        self._msg.append(Opcode.UI_DRAW)
        self._msg.append(UIDrawSubcode.STORE)
        self._append_param(ui_level_no)


    @safe_add
    def add_ui_draw_restore(self, ui_level_no=0):
        """Restores the screen content that was previously saved using
        add_ui_draw_store.

        """
        self._msg.append(Opcode.UI_DRAW)
        self._msg.append(UIDrawSubcode.RESTORE)
        self._append_param(ui_level_no)


    @safe_add
    def add_ui_button_pressed(self, button_type):
        """Returns True if the specified ButtonType button is being pressed."""
        self._msg.append(Opcode.UI_BUTTON)
        self._msg.append(UIButtonSubcode.PRESSED)
        self._append_param(button_type)
        self._append_reply_param(DataFormat.BOOL)


    @safe_add
    def add_keep_alive(self):
        """Resets the sleep timer and returns the sleep timer's new value in
        minutes.

        """
        self._msg.append(Opcode.KEEP_ALIVE)
        self._append_reply_param(DataFormat.DATA8)


    @safe_add
    def add_input_device_get_typemode(self, input_port,
                                            layer=USB_CHAIN_LAYER_MASTER):
        """Returns the DeviceType and mode for the given input_port. The mode
        value depends on the type of the device.

        """
        self._msg.append(Opcode.INPUT_DEVICE)
        self._msg.append(InputDeviceSubcode.GET_TYPEMODE)
        self._append_param(layer)
        self._append_param(input_port)
        self._global_params_types.append(self._REPLY_TUPLE_OPEN_TOKEN)
        self._append_reply_param(DataFormat.DATA8)
        self._append_reply_param(DataFormat.DATA8)
        self._global_params_types.append(self._REPLY_TUPLE_CLOSE_TOKEN)


    @safe_add
    def add_input_device_get_name(self, input_port,
                                            layer=USB_CHAIN_LAYER_MASTER):
        """Returns a string describing the device that is located at the
        specified port i.e. 'NONE' or 'US-DIST-CM'.

        """
        self._msg.append(Opcode.INPUT_DEVICE)
        self._msg.append(InputDeviceSubcode.GET_NAME)
        self._append_param(layer)
        self._append_param(input_port)
        self._append_param(MAX_NAME_STR_LEN, ParamType.LC2)
        self._append_reply_param((DataFormat.DATA_S, MAX_NAME_STR_LEN))


    @safe_add
    def add_input_device_get_modename(self, input_port,
                                            mode,
                                            layer=USB_CHAIN_LAYER_MASTER):
        """Returns a string describing the specified mode of the device that is
        located at the given port. For example, for an ultrasonic sensor mode
        0 will return 'US-DIST-CM' and mode 1 will return 'US-DIST-IN'.

        NOTE:   Reading invalid modes can corrupt the reply buffer.

        """
        self._msg.append(Opcode.INPUT_DEVICE)
        self._msg.append(InputDeviceSubcode.GET_MODENAME)
        self._append_param(layer)
        self._append_param(input_port)
        self._append_param(mode)
        self._append_param(MAX_NAME_STR_LEN, ParamType.LC2)
        self._append_reply_param((DataFormat.DATA_S, MAX_NAME_STR_LEN))


    @safe_add
    def add_input_device_get_minmax(self, input_port,
                                            layer=USB_CHAIN_LAYER_MASTER):
        """"""
        self._msg.append(Opcode.INPUT_DEVICE)
        self._msg.append(InputDeviceSubcode.GET_MINMAX)
        self._append_param(layer)
        self._append_param(input_port)
        self._global_params_types.append(self._REPLY_TUPLE_OPEN_TOKEN)
        self._append_reply_param(DataFormat.DATA_F)
        self._append_reply_param(DataFormat.DATA_F)
        self._global_params_types.append(self._REPLY_TUPLE_CLOSE_TOKEN)


    @safe_add
    def add_input_device_get_changes(self, input_port,
                                            layer=USB_CHAIN_LAYER_MASTER):
        """Returns the number of positive changes since the last time
        CLR_CHANGES was called (i.e. the number of times that a touch sensor
        has been pressed).

        """
        self._msg.append(Opcode.INPUT_DEVICE)
        self._msg.append(InputDeviceSubcode.GET_CHANGES)
        self._append_param(layer)
        self._append_param(input_port)
        self._append_reply_param(DataFormat.DATA_F)


    @safe_add
    def add_input_device_get_bumps(self, input_port,
                                            layer=USB_CHAIN_LAYER_MASTER):
        """Returns the number of negative changes since the last time
        CLR_CHANGES was called (i.e. the number of times that a touch sensor
        has been released).

        """
        self._msg.append(Opcode.INPUT_DEVICE)
        self._msg.append(InputDeviceSubcode.GET_BUMPS)
        self._append_param(layer)
        self._append_param(input_port)
        self._append_reply_param(DataFormat.DATA_F)


    @safe_add
    def add_input_device_clr_changes(self, input_port,
                                            layer=USB_CHAIN_LAYER_MASTER):
        """Returns the number of negative changes since the last time
        CLR_CHANGES was called (i.e. the number of times that a touch sensor
        has been released).

        NOTE:   Does not clear the accumulated angle measurement for the EV3
                gyro sensor.

        """
        self._msg.append(Opcode.INPUT_DEVICE)
        self._msg.append(InputDeviceSubcode.CLR_CHANGES)
        self._append_param(layer)
        self._append_param(input_port)


    @safe_add
    def add_input_device_clr_all(self, layer=USB_CHAIN_LAYER_MASTER):
        """Clears all of the input device values."""
        self._msg.append(Opcode.INPUT_DEVICE)
        self._msg.append(InputDeviceSubcode.CLR_ALL)
        self._append_param(layer)


    @safe_add
    def add_input_device_ready_si(self, input_port,
                                            mode=-1,
                                            device_type=0,
                                            layer=USB_CHAIN_LAYER_MASTER):
        """Waits until the device on the specified InputPort is ready and then
        returns its value as a standard unit.

        """
        self._msg.append(Opcode.INPUT_DEVICE)
        self._msg.append(InputDeviceSubcode.READY_SI)
        self._append_param(layer)
        self._append_param(input_port)
        self._append_param(device_type)
        self._append_param(mode)
        self._append_param(1) # Number of values
        self._append_reply_param(DataFormat.DATA_F)


    @safe_add
    def add_input_device_ready_raw(self, input_port,
                                            mode=-1,
                                            device_type=0,
                                            layer=USB_CHAIN_LAYER_MASTER):
        """Waits until the device on the specified InputPort is ready and then
        returns its value as a raw value.

        """
        self._msg.append(Opcode.INPUT_DEVICE)
        self._msg.append(InputDeviceSubcode.READY_RAW)
        self._append_param(layer)
        self._append_param(input_port)
        self._append_param(device_type)
        self._append_param(mode)
        self._append_param(1) # Number of values
        self._append_reply_param(DataFormat.DATA32)


    @safe_add
    def add_input_device_ready_percent(self, input_port,
                                            mode=-1,
                                            device_type=0,
                                            layer=USB_CHAIN_LAYER_MASTER):
        """Waits until the device on the specified InputPort is ready and then
        returns its value as a percentage.

        """
        self._msg.append(Opcode.INPUT_DEVICE)
        self._msg.append(InputDeviceSubcode.READY_PCT)
        self._append_param(layer)
        self._append_param(input_port)
        self._append_param(device_type)
        self._append_param(mode)
        self._append_param(1) # Number of values?
        self._append_reply_param(DataFormat.DATA8)


    @safe_add
    def add_sound_tone(self, volume,
                                frequency_hz,
                                duration_ms,
                                layer=USB_CHAIN_LAYER_MASTER):
        """Plays the tone at the given volume and frequency for the given
        duration_ms milliseconds.

        """
        self._msg.append(Opcode.SOUND)
        self._msg.append(SoundSubcode.TONE)
        self._append_param(volume)
        self._append_param(frequency_hz, ParamType.LC2)
        self._append_param(duration_ms, ParamType.LC2)


    @safe_add
    def add_sound_play(self, volume, filename):
        """Plays the sound file with the given name at the specified volume.
        The default sound files are located in the '/home/root/lms2012/sys/ui/'
        directory and include Startup.rsf, PowerDown.rsf, OverpowerAlert.rsf,
        GeneralAlarm.rsf, DownloadSucces.rsf, and Click.rsf.

        NOTE:   Do not include the '.rsf' extension in the filename.

        """
        self._msg.append(Opcode.SOUND)
        self._msg.append(SoundSubcode.PLAY)
        self._append_param(volume)
        self._append_param(filename, ParamType.LCS)


    @safe_add
    def add_ui_read_get_fw_vers(self):
        """Returns the FW version as a string in the form 'VX.XXX'."""
        self._msg.append(Opcode.UI_READ)
        self._msg.append(UIReadSubcode.GET_FW_VERS)
        self._append_param(MAX_VERSION_STR_LEN, ParamType.LC2)
        self._append_reply_param((DataFormat.DATA_S, MAX_NAME_STR_LEN))


    @safe_add
    def add_ui_read_get_hw_vers(self):
        """Returns the HW version as a string in the form 'VX.XXX'."""
        self._msg.append(Opcode.UI_READ)
        self._msg.append(UIReadSubcode.GET_HW_VERS)
        self._append_param(MAX_VERSION_STR_LEN, ParamType.LC2)
        self._append_reply_param((DataFormat.DATA_S, MAX_NAME_STR_LEN))


    @safe_add
    def add_ui_read_get_fw_build(self):
        """Returns the firmware build as a string in the form 'XXXXXXXXXX'."""
        self._msg.append(Opcode.UI_READ)
        self._msg.append(UIReadSubcode.GET_FW_BUILD)
        self._append_param(MAX_VERSION_STR_LEN, ParamType.LC2)
        self._append_reply_param((DataFormat.DATA_S, MAX_NAME_STR_LEN))


    @safe_add
    def add_ui_read_get_os_vers(self):
        """Returns the OS version as a string in the form 'Linux X.X.XX'."""
        self._msg.append(Opcode.UI_READ)
        self._msg.append(UIReadSubcode.GET_OS_VERS)
        self._append_param(MAX_VERSION_STR_LEN, ParamType.LC2)
        self._append_reply_param((DataFormat.DATA_S, MAX_NAME_STR_LEN))


    @safe_add
    def add_ui_read_get_os_build(self):
        """Returns the OS build as a string in the form 'XXXXXXXXXX'."""
        self._msg.append(Opcode.UI_READ)
        self._msg.append(UIReadSubcode.GET_OS_BUILD)
        self._append_param(MAX_VERSION_STR_LEN, ParamType.LC2)
        self._append_reply_param((DataFormat.DATA_S, MAX_NAME_STR_LEN))


    @safe_add
    def add_ui_read_get_version(self):
        """Returns the Lego Mindstorms version as a string in the form
        'LMS2012 VX.XXX(<TIMESTAMP>)'.

        """
        self._msg.append(Opcode.UI_READ)
        self._msg.append(UIReadSubcode.GET_VERSION)
        self._append_param(MAX_VERSION_STR_LEN, ParamType.LC2)
        self._append_reply_param((DataFormat.DATA_S, MAX_NAME_STR_LEN))


    @safe_add
    def add_ui_read_get_ip(self):
        """Returns the IP address as a string."""
        self._msg.append(Opcode.UI_READ)
        self._msg.append(UIReadSubcode.GET_IP)
        self._append_param(MAX_VERSION_STR_LEN, ParamType.LC2)
        self._append_reply_param((DataFormat.DATA_S, MAX_NAME_STR_LEN))


    @safe_add
    def add_ui_read_get_vbatt(self):
        """Gets the current battery voltage. According to the constants that are
        defined in 'lms2012.h', the rechargeable battery should be in the range
        of [6.0, 7.1] and normal batteries should be in the range of [4.5, 6.2].

        """
        self._msg.append(Opcode.UI_READ)
        self._msg.append(UIReadSubcode.GET_VBATT)
        self._append_reply_param(DataFormat.DATA_F)


    @safe_add
    def add_ui_read_get_lbatt(self):
        """Gets the current battery level as a percentage."""
        self._msg.append(Opcode.UI_READ)
        self._msg.append(UIReadSubcode.GET_LBATT)
        self._append_reply_param(DataFormat.DATA_PCT)


    @safe_add
    def add_ui_read_get_ibatt(self):
        """Gets the current battery discharge amperage."""
        self._msg.append(Opcode.UI_READ)
        self._msg.append(UIReadSubcode.GET_IBATT)
        self._append_reply_param(DataFormat.DATA_F)


    @safe_add
    def add_ui_read_get_tbatt(self):
        """Gets the current battery temperature rise."""
        self._msg.append(Opcode.UI_READ)
        self._msg.append(UIReadSubcode.GET_TBATT)
        self._append_reply_param(DataFormat.DATA_F)


    @safe_add
    def add_ui_read_get_imotor(self):
        """Gets the amount of current that the motors are using."""
        self._msg.append(Opcode.UI_READ)
        self._msg.append(UIReadSubcode.GET_IMOTOR)
        self._append_reply_param(DataFormat.DATA_F)


    @safe_add
    def add_ui_read_get_sdcard(self):
        """Returns the following information about the SD card:
        (<SD_CARD_OK>, <TOTAL_KBYTES>, <FREE_KBYTES>). The SD_CARD_OK value is
        a boolean.

        """
        self._msg.append(Opcode.UI_READ)
        self._msg.append(UIReadSubcode.GET_SDCARD)
        self._global_params_types.append(self._REPLY_TUPLE_OPEN_TOKEN)
        self._append_reply_param(DataFormat.BOOL)
        self._append_reply_param(DataFormat.DATA32)
        self._append_reply_param(DataFormat.DATA32)
        self._global_params_types.append(self._REPLY_TUPLE_CLOSE_TOKEN)


    @safe_add
    def add_ui_read_get_usbstick(self):
        """Returns the following information about the USB stick:
        (<USB_STICK_OK>, <TOTAL_KBYTES>, <FREE_KBYTES>). The USB_STICK_OK value
        is a boolean.

        """
        self._msg.append(Opcode.UI_READ)
        self._msg.append(UIReadSubcode.GET_SDCARD)
        self._global_params_types.append(self._REPLY_TUPLE_OPEN_TOKEN)
        self._append_reply_param(DataFormat.BOOL)
        self._append_reply_param(DataFormat.DATA32)
        self._append_reply_param(DataFormat.DATA32)
        self._global_params_types.append(self._REPLY_TUPLE_CLOSE_TOKEN)


    @safe_add
    def add_output_get_type(self, output_port, layer=USB_CHAIN_LAYER_MASTER):
        """Returns the DeviceType of the device that is connected to the
        specified OutputPort.

        """
        self._msg.append(Opcode.OUTPUT_GET_TYPE)
        self._append_param(layer)
        self._append_param(OUTPUT_CHANNEL_TO_INDEX[output_port])
        self._append_reply_param(DataFormat.DATA8)


    @safe_add
    def add_output_set_type(self, output_port,
                                            output_type,
                                            layer=USB_CHAIN_LAYER_MASTER):
        """Sets the DeviceType of the device that is connected to the
        specified OutputPort.

        TODO:   d_pwm.c says this only works with type TACHO or MINI_TACHO.
        TODO:   Debug this. Not sure how to verify that this works.
                It seems to be implemented in d_pwm.c

        """
        self._msg.append(Opcode.OUTPUT_SET_TYPE)
        self._append_param(layer)
        self._append_param(output_type)


    @safe_add
    def add_output_reset(self, output_port_mask,
                                            layer=USB_CHAIN_LAYER_MASTER):
        """Resets the tacho count and timer of the motor(s) described by the
        output_port_mask parameter. Should be called when initializing a
        motor?

        """
        self._msg.append(Opcode.OUTPUT_RESET)
        self._append_param(layer)
        self._append_param(output_port_mask)


    @safe_add
    def add_output_stop(self, output_port_mask,
                                            stop_type,
                                            layer=USB_CHAIN_LAYER_MASTER):
        """Stops the motor(s) described by the output_port_mask parameter.
        The stop_byte parameter defines whether the motor will BRAKE or COAST.

        """
        self._msg.append(Opcode.OUTPUT_STOP)
        self._append_param(layer)
        self._append_param(output_port_mask)
        self._append_param(stop_type)


    @safe_add
    def add_output_power(self, output_port_mask,
                                            power,
                                            layer=USB_CHAIN_LAYER_MASTER):
        """Sets the power for the motor(s) described by the output_port_mask
        parameter. Power values should be in the range [-100, 100]. Note that
        add_output_start needs to be called before the motor will start moving.

        """
        self._msg.append(Opcode.OUTPUT_POWER)
        self._append_param(layer)
        self._append_param(output_port_mask)
        self._append_param(power)


    @safe_add
    def add_output_speed(self, output_port_mask,
                                            speed,
                                            layer=USB_CHAIN_LAYER_MASTER):
        """Sets the speed for the motor(s) described by the output_port_mask
        parameter. Speed values should be in the range [-100, 100]. Note that
        add_output_start needs to be called before the motor will start moving.

        """
        self._msg.append(Opcode.OUTPUT_SPEED);
        self._append_param(layer)
        self._append_param(output_port_mask)
        self._append_param(speed)


    @safe_add
    def add_output_start(self, output_port_mask,
                                            layer=USB_CHAIN_LAYER_MASTER):
        """Starts the motor(s) described by the output_port_mask
        parameter.

        """
        self._msg.append(Opcode.OUTPUT_START)
        self._append_param(layer)
        self._append_param(output_port_mask)


    @safe_add
    def add_output_polarity(self, output_port_mask,
                                            polarity_type,
                                            layer=USB_CHAIN_LAYER_MASTER):
        """Sets the polarity for the motor(s) described by the
        output_port_mask parameter.

        """
        self._msg.append(Opcode.OUTPUT_POLARITY)
        self._append_param(layer)
        self._append_param(output_port_mask)
        self._append_param(polarity_type)


    @safe_add
    def add_output_read(self, output_port, layer=USB_CHAIN_LAYER_MASTER):
        """Reads the speed and tacho pulses for the given output_port and
        returns them as a tuple in the form (SPEED, TACHO_PULSES).

        """
        self._msg.append(Opcode.OUTPUT_READ)
        self._append_param(layer)
        self._append_param(OUTPUT_CHANNEL_TO_INDEX[output_port])
        self._global_params_types.append(self._REPLY_TUPLE_OPEN_TOKEN)
        self._append_reply_param(DataFormat.DATA8)
        self._append_reply_param(DataFormat.DATA32)
        self._global_params_types.append(self._REPLY_TUPLE_CLOSE_TOKEN)


    @safe_add
    def add_output_ready(self, output_port_mask,
                                            layer=USB_CHAIN_LAYER_MASTER):
        """Waits for the outputs in the output_port_mask to report that
        they are ready before executing the next opcode. For example, if two
        consecutive motor commands are used with the same OutputPort putting
        this opcode between them ensures that the first command finishes
        before the second one is started.

        """
        self._msg.append(Opcode.OUTPUT_READY)
        self._append_param(layer)
        self._append_param(output_port_mask)


    @safe_add
    def add_output_position(self, output_port_mask,
                                            position,
                                            layer=USB_CHAIN_LAYER_MASTER):
        """Sets the position of the specied OutputPort(s)."""
        self._msg.append(Opcode.OUTPUT_POSITION)
        self._append_param(layer)
        self._append_param(output_port_mask)
        self._append_param(position, ParamType.LC4)


    @safe_add
    def add_output_step_power(self, output_port_mask,
                                            power,
                                            ramp_up_steps,
                                            steps,
                                            ramp_down_steps,
                                            stop_type,
                                            layer=USB_CHAIN_LAYER_MASTER):
        """Ramps up the power for the motor(s) described by the
        output_port_mask, holds for steps, and then ramps down. It is not
        necessary to call add_output_start in addition to this opcode.

        NOTE:   The EV3 will NOT wait for this operation to complete before
                executing the next opcode unless add_output_ready is used.

        """
        self._msg.append(Opcode.OUTPUT_STEP_POWER);
        self._append_param(layer)
        self._append_param(output_port_mask)
        self._append_param(power)
        self._append_param(ramp_up_steps, ParamType.LC4)
        self._append_param(steps, ParamType.LC4)
        self._append_param(ramp_down_steps, ParamType.LC4)
        self._append_param(stop_type)


    @safe_add
    def add_output_time_power(self, output_port_mask,
                                            power,
                                            ramp_up_ms,
                                            time_ms,
                                            ramp_down_ms,
                                            stop_type,
                                            layer=USB_CHAIN_LAYER_MASTER):
        """Ramps up the power for the motor(s) described by the
        output_port_mask, holds for time_ms, and then ramps down. It is not
        necessary to call add_output_start in addition to this opcode.

        NOTE:   The EV3 will NOT wait for this operation to complete before
                executing the next opcode unless add_output_ready is used.

        """
        self._msg.append(Opcode.OUTPUT_TIME_POWER);
        self._append_param(layer)
        self._append_param(output_port_mask)
        self._append_param(power)
        self._append_param(ramp_up_ms, ParamType.LC4)
        self._append_param(time_ms, ParamType.LC4)
        self._append_param(ramp_down_ms, ParamType.LC4)
        self._append_param(stop_type)


    @safe_add
    def add_output_step_speed(self, output_port_mask,
                                            speed,
                                            ramp_up_steps,
                                            steps,
                                            ramp_down_steps,
                                            stop_type,
                                            layer=USB_CHAIN_LAYER_MASTER):
        """Ramps up the power for the motor(s) described by the
        output_port_mask, holds for steps, and then ramps down. It is not
        necessary to call add_output_start in addition to this opcode.

        NOTE:   The EV3 will NOT wait for this operation to complete before
                executing the next opcode unless add_output_ready is used.

        """
        self._msg.append(Opcode.OUTPUT_STEP_SPEED);
        self._append_param(layer)
        self._append_param(output_port_mask)
        self._append_param(speed)
        self._append_param(ramp_up_steps, ParamType.LC4)
        self._append_param(steps, ParamType.LC4)
        self._append_param(ramp_down_steps, ParamType.LC4)
        self._append_param(stop_type)


    @safe_add
    def add_output_time_speed(self, output_port_mask,
                                            speed,
                                            ramp_up_ms,
                                            time_ms,
                                            ramp_down_ms,
                                            stop_type,
                                            layer=USB_CHAIN_LAYER_MASTER):
        """Ramps up the power for the motor(s) described by the
        output_port_mask, holds for time_ms, and then ramps down. It is not
        necessary to call add_output_start in addition to this opcode.

        NOTE:   The EV3 will NOT wait for this operation to complete before
                executing the next opcode unless add_output_ready is used.

        """
        self._msg.append(Opcode.OUTPUT_TIME_SPEED);
        self._append_param(layer)
        self._append_param(output_port_mask)
        self._append_param(speed)
        self._append_param(ramp_up_ms, ParamType.LC4)
        self._append_param(time_ms, ParamType.LC4)
        self._append_param(ramp_down_ms, ParamType.LC4)
        self._append_param(stop_type)


    @safe_add
    def add_output_step_sync(self, output_port_mask,
                                            speed,
                                            turn_ratio,
                                            step,
                                            stop_type,
                                            layer=USB_CHAIN_LAYER_MASTER):
        """Sets the speed for the two given motors in the following fashion:
                [-200, -101]:   Turn right with right motor running in reverse
                [-100,   -1]:   Turn right with right motor slowed
                           0:   Both motors in sync in the same direction
                [1,     100]:   Turn left with left motor slowed
                [101,   200]:   Turn left with left motor running in reverse

        It is not necessary to call add_output_start in addition to this opcode.

        NOTE:   The EV3 will NOT wait for this operation to complete before
                executing the next opcode unless add_output_ready is used.

        """
        self._msg.append(Opcode.OUTPUT_STEP_SYNC);
        self._append_param(layer)
        self._append_param(output_port_mask)
        self._append_param(speed)
        self._append_param(turn_ratio, ParamType.LC2)
        self._append_param(step, ParamType.LC4)
        self._append_param(stop_type)


    @safe_add
    def add_output_time_sync(self, output_port_mask,
                                            speed,
                                            turn_ratio,
                                            time,
                                            stop_type,
                                            layer=USB_CHAIN_LAYER_MASTER):
        """Sets the speed for the two given motors in the following fashion:
                [-200, -101]:   Turn right with right motor running in reverse
                [-100,   -1]:   Turn right with right motor slowed
                           0:   Both motors in sync in the same direction
                [1,     100]:   Turn left with left motor slowed
                [101,   200]:   Turn left with left motor running in reverse

        It is not necessary to call add_output_start in addition to this opcode.

        NOTE:   The EV3 will NOT wait for this operation to complete before
                executing the next opcode unless add_output_ready is used.

        """
        self._msg.append(Opcode.OUTPUT_TIME_SYNC);
        self._append_param(layer)
        self._append_param(output_port_mask)
        self._append_param(speed)
        self._append_param(turn_ratio, ParamType.LC2)
        self._append_param(time, ParamType.LC4)
        self._append_param(stop_type)


    @safe_add
    def add_output_clr_count(self, output_port_mask,
                                            layer=USB_CHAIN_LAYER_MASTER):
        """Clears the tacho count for the given OutputPort(s) when in sensor
        mode.

        """
        self._msg.append(Opcode.OUTPUT_CLR_COUNT);
        self._append_param(layer)
        self._append_param(output_port_mask)


    @safe_add
    def add_output_get_count(self, output_port,
                                            layer=USB_CHAIN_LAYER_MASTER):
        """Returns the tacho count for the given OutputPort when in sensor
        mode.

        """
        self._msg.append(Opcode.OUTPUT_GET_COUNT);
        self._append_param(layer)
        self._append_param(OUTPUT_CHANNEL_TO_INDEX[output_port])
        self._append_reply_param(DataFormat.DATA32)


    @safe_add
    def add_set_leds(self, led_pattern):
        """Sets the LEDs on the front of the brick to the specified item in
        the LEDPattern enumeration.

        """
        self._msg.append(Opcode.UI_WRITE)
        self._msg.append(UIWriteSubcode.LED)
        self._append_param(led_pattern)


    def _parse_reply(self, buf):
        result = []
        index = 0

        if (ReplyType.DIRECT_REPLY_ERROR == buf[0]):
            raise DirectCommandError('The DirectCommand failed.')

        if (self._global_params_byte_count != (len(buf) - 1)):
            raise DirectCommandError('The data returned by the ' +
                                        'command was smaller than expected.')

        # The items in the reply are grouped into tuples. Each tuple represents
        # the reply to a command that returns multiple values.
        sub_tuple = None
        for item in self._global_params_types:
            value = None
            length = 0

            if (self._REPLY_TUPLE_OPEN_TOKEN == item):
                sub_tuple = []
                continue
            elif (self._REPLY_TUPLE_CLOSE_TOKEN == item):
                result.append(tuple(sub_tuple))
                sub_tuple = None
                continue

            if (isinstance(item, tuple)):
                value, length = self._parse_param(buf, (index + 1), *item)
            else:
                # Ensure that the alignment is correct.
                data_len = DATA_FORMAT_LENS[item]

                pad = (index % data_len)
                if (0 != pad):
                    pad = (data_len - pad)
                    index += pad

                value, length = self._parse_param(buf, (index + 1), item)

            if (sub_tuple is not None):
                sub_tuple.append(value)
            else:
                result.append(value)

            index += length

        return tuple(result)


    def _parse_param(self, buf, index, data_format, data_len=None):
        value = None
        length = 1

        if (DataFormat.DATA_S == data_format):
            value = message.parse_null_terminated_str(buf, index, data_len)
            length = data_len
        elif (DataFormat.HND == data_format):
            value = (buf[index] & ~ParamType.HND)
        elif (DataFormat.DATA_F == data_format):
            value = message.parse_float(buf, index)
            length = DATA_FORMAT_LENS[DataFormat.DATA_F]
        elif (DataFormat.BOOL == data_format):
            value = bool(buf[index])
            length = 1
        else:
            length = DATA_FORMAT_LENS[data_format]

            if (1 == length):
                value = buf[index]
            elif (2 == length):
                value = message.parse_u16(buf, index)
            elif (4 == length):
                value = message.parse_u32(buf, index)
            else:
                raise DirectCommandError('Unexpected ParamType: %d' %
                                                                    param_type)

        return (value, length)


    def _append_reply_param(self, reply_format):
        """Global parameters are stored in the tx buffer on the brick so
        their values are returned in the message reply.

        """
        data_len = None

        if (not isinstance(reply_format, tuple)):
            # Ensure that the alignment is correct.
            data_len = DATA_FORMAT_LENS[reply_format]

            pad = (self._global_params_byte_count % data_len)
            if (pad):
                pad = (data_len - pad)
                self._global_params_byte_count += pad
        else:
            data_len = reply_format[1]

        # Use as few bits as possible to save space in message buffer.
        param_type = ParamType.GV1
        if (0xFFFF < self._global_params_byte_count):
            param_type = ParamType.GV4
        elif (0xFF < self._global_params_byte_count):
            param_type = ParamType.GV2

        self._append_param(self._global_params_byte_count, param_type)
        self._global_params_types.append(reply_format)
        self._global_params_byte_count += data_len


    def _allocate_local_param(self, data_format):
        """Local parameters are essentially stack variables so they are NOT
        included in the reply from the brick. This function returns an index
        that can be used to access a new local variable of the given DataFormat.

        """
        # Ensure that the alignment is correct.
        data_len = DATA_FORMAT_LENS[data_format]

        pad = (self._local_params_byte_count % data_len)
        if (pad):
            pad = (data_len - pad)
            self._local_params_byte_count += pad

        # Use as few bits as possible to save space in message buffer.
        param_type = ParamType.LV1
        if (0xFFFF < self._local_params_byte_count):
            param_type = ParamType.LV4
        elif (0xFF < self._local_params_byte_count):
            param_type = ParamType.LV2

        index = self._local_params_byte_count

        self._local_params_byte_count += data_len

        return (index, param_type)


    def _append_local_constant(self, val):
        """"Appends an immediate value as a local constant."""
        param_type = None

        if (isinstance(val, int)):
            num_bits = int.bit_length(val)
            if (num_bits > 16):
                param_type = ParamType.LC4
            elif (num_bits > 8):
                param_type = ParamType.LC2
            elif (num_bits > 6):
                param_type = ParamType.LC1
            else:
                param_type = ParamType.LC0
        elif (isinstance(val, float)):
            param_type = ParamType.FLOAT
        elif (isinstance(val, str)):
            param_type = ParamType.LCS
        else:
            raise NotImplementedError('Unknown local constant type.')

        self._append_param(val, param_type)


    def _append_param(self, val, param_type=ParamType.LC1):
        """All parameters need to be prefixed with their type so the VM knows
        how to interpret the following data. The reply_format parameter is
        used when a reply is expected.

        """
        if (ParamType.PRIMPAR_LABEL == param_type):
            raise NotImplementedError('ParamType.PRIMPAR_LABEL')
        elif (ParamType.LCS == param_type):
            self._msg.append(param_type)
            message.append_str(self._msg, val)
        elif (ParamType.LC0 == param_type):
            self._msg.append(ParamType.LC0 |  (0x3F & val))
        elif (ParamType.HND == param_type):
            self._msg.append(ParamType.HND | val)
        elif (ParamType.ADR == param_type):
            self._msg.append(ParamType.ADR | val)
        elif (ParamType.GV0 == param_type):
            self._msg.append(ParamType.GV0 | (0x1F & val))
        elif (ParamType.FLOAT == param_type):
            self._msg.append(ParamType.LC4)
            message.append_float(self._msg, val)
        else:
            length = PARAM_TYPE_LENS[param_type]

            self._msg.append(param_type)

            if (1 == length):
                message.append_u8(self._msg, val)
            elif (2 == length):
                message.append_u16(self._msg, val)
            elif (4 == length):
                message.append_u32(self._msg, val)
            else:
                raise DirectCommandError('Unexpected ParamType:' +
                                                            ' %d' % param_type)
