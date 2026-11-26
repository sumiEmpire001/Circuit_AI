from app.design import Design
from app.image_reference import at89c51_adc, at89c51_lcd

def controller_lcd():
    components=[dict(ref='U1',part='arduino_uno',value='Uno R3 / USB power'),dict(ref='LCD1',part='lcd1602',value='5 V HD44780-compatible'),dict(ref='V1',part='dc_source',value='5 V'),dict(ref='RV1',part='potentiometer',value='10 kohm'),dict(ref='R1',part='resistor',value='220 ohm')]
    nets=[dict(name='VCC',pins=['V1.+','U1.5V','LCD1.2','RV1.1','R1.1']),dict(name='GND',pins=['V1.-','U1.GND','LCD1.1','LCD1.5','LCD1.16','RV1.2']),dict(name='CONTRAST',pins=['RV1.W','LCD1.3']),dict(name='BACKLIGHT',pins=['R1.2','LCD1.15'])]
    for name,uno,lcd in [('RS','D12','4'),('ENABLE','D11','6'),('DATA4','D5','11'),('DATA5','D4','12'),('DATA6','D3','13'),('DATA7','D2','14')]:
        nets.append(dict(name=name,pins=[f'U1.{uno}',f'LCD1.{lcd}']))
    return Design(title='Arduino Uno + 16×2 LCD',components=components,nets=nets,notes=[
        '4-bit parallel wiring follows the Arduino LiquidCrystal example. https://docs.arduino.cc/learn/electronics/lcd-displays/',
        'V1 represents the Uno 5 V rail from USB; do not add a second external 5 V supply while USB powers the board.',
        '10 kohm contrast potentiometer and 220 ohm backlight resistor are example values; check your LCD backlight specification.',
        'LCD D0–D3 are unused in 4-bit mode. Firmware must match RS=12, E=11, D4=5, D5=4, D6=3, D7=2.'])

def led_bank(count=4):
    components=[dict(ref='V1',part='dc_source',value='5 V')];nets=[];power=['V1.+'];ground=['V1.-']
    for i in range(1,count+1):
        components.extend([dict(ref=f'R{i}',part='resistor',value='330 ohm'),dict(ref=f'D{i}',part='led',value='Red LED; check Vf')])
        power.append(f'R{i}.1');ground.append(f'D{i}.K');nets.append(dict(name=f'LED_{i}',pins=[f'R{i}.2',f'D{i}.A']))
    nets.extend([dict(name='VCC',pins=power),dict(name='GND',pins=ground)])
    return Design(title=f'{count}-channel LED bank',components=components,nets=nets,notes=['Each LED has its own current-limiting resistor. Verify forward voltage and resistor power.'])

def rc_ladder():
    return Design(title='Two-stage passive RC filter',components=[dict(ref='V1',part='dc_source',value='5 V'),dict(ref='R1',part='resistor',value='1 kohm'),dict(ref='R2',part='resistor',value='2.2 kohm'),dict(ref='C1',part='capacitor',value='100 nF'),dict(ref='C2',part='capacitor',value='100 nF')],nets=[dict(name='IN',pins=['V1.+','R1.1']),dict(name='MID',pins=['R1.2','R2.1','C1.1']),dict(name='OUT',pins=['R2.2','C2.1']),dict(name='GND',pins=['V1.-','C1.2','C2.2'])],notes=['The two stages load each other. No frequency-response simulation has been performed.'])
EXAMPLES={'controller_lcd':controller_lcd,'led_bank':led_bank,'rc_ladder':rc_ladder}

def mega_ldr():
    return Design(title='Arduino Mega light sensor draft',components=[
        dict(ref='U1',part='arduino_mega',value='Mega 2560'),
        dict(ref='V1',part='dc_source',value='5 V'),
        dict(ref='LDR1',part='ldr',value='Verify light resistance'),
        dict(ref='R1',part='resistor',value='10 kohm')],
        nets=[dict(name='VCC',pins=['V1.+','U1.5V','LDR1.1']),
              dict(name='SENSE',pins=['LDR1.2','R1.1','U1.A0']),
              dict(name='GND',pins=['V1.-','U1.GND','R1.2'])],
        notes=['V1 represents the board USB-derived 5 V rail, not an additional supply.',
               'Select divider resistance for the actual LDR and light range. Not physically verified.'])
EXAMPLES['mega_ldr']=mega_ldr

def mega_ldr_servo():
    d=mega_ldr().model_dump()
    d['title']='Mega LDR and separately powered RC servo'
    d['components'] += [dict(ref='V2',part='dc_source',value='5 V'),dict(ref='M1',part='servo_generic',value='5 V compatible servo; verify rating')]
    next(n for n in d['nets'] if n['name']=='GND')['pins'] += ['V2.-','M1.GND']
    d['nets'] += [dict(name='SERVO_PWR',pins=['V2.+','M1.VCC']),dict(name='SERVO_SIG',pins=['U1.D9','M1.SIG'])]
    d['notes'] += ['Use a separate regulated supply sized for servo stall current; verify servo accepts 5 V and Mega logic. Grounds are common; positive rails are separate. Firmware is not generated.']
    return Design.model_validate(d)
EXAMPLES['mega_ldr_servo']=mega_ldr_servo

def bridge_rectifier():
    # User reference 1: four diodes and output bypass capacitor.
    components=[dict(ref=ref,part='diode',value='1N4007',position={'x':x,'y':y}) for ref,x,y in [('D1',210,380),('D2',710,380),('D3',210,620),('D4',710,620)]]
    components += [dict(ref='J1',part='connector2',value='Isolated low-voltage AC input',position={'x':460,'y':130}),
                   dict(ref='C1',part='capacitor',value='100 nF',position={'x':460,'y':860}),
                   dict(ref='J2',part='connector2',value='DC output: 1 positive, 2 negative',position={'x':460,'y':1100})]
    return Design(title='Four-diode bridge rectifier',components=components,nets=[
        dict(name='AC1',pins=['J1.1','D1.K','D2.A']),
        dict(name='AC2',pins=['J1.2','D3.K','D4.A']),
        dict(name='DC_POS',pins=['D2.K','D4.K','C1.2','J2.1']),
        dict(name='DC_NEG',pins=['D1.A','D3.A','C1.1','J2.2'])],
        notes=['Topology transcribed from user reference image 1. Use isolated low-voltage AC only. Verify diode and capacitor ratings. 100 nF is a bypass capacitor, not necessarily adequate for bulk smoothing. No simulation or hardware verification.'])
EXAMPLES['bridge_rectifier']=bridge_rectifier

def temperature_motor():
    # New low-voltage design inspired by user image 9, not a literal copy.
    return Design(title='Arduino temperature-controlled motor draft',components=[
        dict(ref='U1',part='arduino_uno',value='Uno R3 / USB power'),
        dict(ref='U2',part='l293d',value='L293D motor driver'),
        dict(ref='S1',part='lm35',value='LM35 temperature sensor'),
        dict(ref='M1',part='dc_motor',value='6 V motor; verify stall current'),
        dict(ref='V1',part='dc_source',value='5 V'),
        dict(ref='V2',part='dc_source',value='6 V'),
        dict(ref='C1',part='capacitor',value='100 nF'),
        dict(ref='C2',part='capacitor',value='100 nF')],
        nets=[
            dict(name='LOGIC_5V',pins=['V1.+','U1.5V','U2.VCC1','S1.VS','C1.1']),
            dict(name='MOTOR_6V',pins=['V2.+','U2.VCC2','C2.1']),
            dict(name='GND',pins=['V1.-','V2.-','U1.GND','U2.GND1','U2.GND2','U2.GND3','U2.GND4','U2.EN34','U2.IN3','U2.IN4','S1.GND','C1.2','C2.2']),
            dict(name='TEMP',pins=['S1.VOUT','U1.A0']),
            dict(name='PWM',pins=['U1.D9','U2.EN12']),
            dict(name='DIR1',pins=['U1.D7','U2.IN1']),
            dict(name='DIR2',pins=['U1.D8','U2.IN2']),
            dict(name='MOTOR_A',pins=['U2.OUT1','M1.+']),
            dict(name='MOTOR_B',pins=['U2.OUT2','M1.-'])],
        notes=['Low-voltage draft inspired by the temperature-controlled fan reference; uses Arduino instead of AT89C51 and ADC0804.',
               'V1 represents USB-derived board power. Do not parallel a second 5 V supply with USB. V2 is an independent regulated motor supply; common ground.',
               'Verify motor stall current, driver voltage drop, thermal limits and bulk supply decoupling. L293D has internal clamp diodes; verify the exact device.',
               'Firmware must drive D9 PWM and D7/D8 direction. Not simulated or hardware verified.'])
EXAMPLES['temperature_motor']=temperature_motor

def schmitt_inverter():
    return Design(title='SN74HC14N Schmitt-trigger inverter', components=[
        dict(ref='J1',part='connector2',value='Logic input'),
        dict(ref='U1',part='sn74hc14n',value='SN74HC14N'),
        dict(ref='J2',part='connector2',value='Inverted output'),
        dict(ref='V1',part='dc_source',value='5 V'),
        dict(ref='C1',part='capacitor',value='100 nF'),
    ], nets=[
        dict(name='LOGIC_IN',pins=['J1.1','U1.1']),
        dict(name='LOGIC_OUT',pins=['U1.2','J2.1']),
        dict(name='VCC',pins=['V1.+','U1.14','C1.1']),
        dict(name='GND',pins=['V1.-','U1.7','C1.2','J1.2','J2.2','U1.3','U1.5','U1.9','U1.11','U1.13']),
    ], notes=[
        'Single gate with unused CMOS inputs tied low and unused outputs left open.',
        'Check input thresholds and output load for the actual supply. See https://www.ti.com/lit/ds/symlink/sn74hc14.pdf',
    ])

EXAMPLES['schmitt_inverter']=schmitt_inverter

EXAMPLES['at89c51_lcd']=at89c51_lcd


def ne555_astable():
    parts = [
        ('V1','dc_source','5 V'), ('U1','ne555p','NE555P'),
        ('R1','resistor','10 kohm'), ('R2','resistor','47 kohm'),
        ('C1','capacitor','100 nF'), ('C2','capacitor','10 nF'),
        ('C3','capacitor','100 nF'), ('J1','connector2','Output'),
    ]
    positions = {
        'V1': (680,125), 'U1': (680,450), 'R1': (210,450), 'R2': (210,650),
        'C1': (210,850), 'C2': (680,810), 'C3': (1260,165), 'J1': (1260,450),
    }
    nets = {
        'VCC': ['V1.+','U1.8','U1.4','R1.1','C3.1'],
        'GND': ['V1.-','U1.1','C1.2','C2.2','C3.2','J1.2'],
        'DISCHARGE': ['R1.2','R2.1','U1.7'],
        'TIMING': ['R2.2','C1.1','U1.2','U1.6'],
        'CONTROL': ['U1.5','C2.1'],
        'OUT': ['U1.3','J1.1'],
    }
    return Design(title='NE555P astable timer',
                  components=[dict(ref=ref,part=part,value=value,
                                   position=dict(zip(('x','y'),positions[ref])))
                              for ref,part,value in parts],
                  nets=[dict(name=name,pins=pins) for name,pins in nets.items()],
                  notes=['Astable connection follows TI NE555 Figure 6-5. Component values are example choices. Circuit has not been simulated.'])


EXAMPLES['ne555_astable'] = ne555_astable

EXAMPLES['at89c51_adc'] = at89c51_adc


def nand_gate():
    return Design(title='SN74HC00N two-input NAND gate', components=[
        dict(ref='J1', part='connector3', value='Logic inputs A and B'),
        dict(ref='U1', part='sn74hc00n'),
        dict(ref='J2', part='connector2', value='Logic output'),
        dict(ref='V1', part='dc_source', value='5 V'),
        dict(ref='C1', part='capacitor', value='100 nF'),
    ], nets=[
        dict(name='INPUT_A', pins=['J1.1', 'U1.1']),
        dict(name='INPUT_B', pins=['J1.2', 'U1.2']),
        dict(name='OUTPUT', pins=['U1.3', 'J2.1']),
        dict(name='VCC', pins=['V1.+', 'U1.14', 'C1.1']),
        dict(name='GND', pins=['V1.-', 'U1.7', 'C1.2', 'J1.3', 'J2.2',
                               'U1.4', 'U1.5', 'U1.9', 'U1.10', 'U1.12', 'U1.13']),
    ], notes=['Drive both inputs at valid CMOS logic levels. Tie unused inputs to ground and leave unused outputs open.'])


EXAMPLES['nand_gate'] = nand_gate
