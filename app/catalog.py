"""Versioned logical pin catalog. Generic symbols do not claim package pinouts."""
def part(name, symbol, pins, required=(), voltage=None, source=None):
    return dict(name=name, symbol=symbol, pins=pins, required=list(required), voltage=voltage, source=source)
CATALOG = {
 'resistor': part('Resistor', 'resistor', {'1':'passive','2':'passive'}, ('1','2')),
 'capacitor': part('Capacitor (non-polarized)', 'capacitor', {'1':'passive','2':'passive'}, ('1','2')),
 'led': part('LED', 'led', {'A':'passive','K':'passive'}, ('A','K')),
 'diode': part('Diode', 'diode', {'A':'passive','K':'passive'}, ('A','K')),
 'inductor': part('Inductor', 'inductor', {'1':'passive','2':'passive'}, ('1','2')),
 'potentiometer': part('Potentiometer', 'pot', {'1':'passive','W':'passive','2':'passive'}, ('1','W','2')),
 'switch': part('Normally-open switch', 'switch', {'1':'passive','2':'passive'}, ('1','2')),
 'dc_source': part('DC supply', 'source', {'+':'power_out','-':'ground'}, ('+','-')),
 'npn': part('Generic NPN transistor', 'npn', {'B':'input','C':'passive','E':'passive'}, ('B','C','E')),
 'nmos': part('Generic N-channel MOSFET', 'nmos', {'G':'input','D':'passive','S':'passive'}, ('G','D','S')),
 'connector2': part('Two-pin connector', 'connector', {'1':'passive','2':'passive'}),
 'arduino_uno': part('Arduino Uno R3 (logical headers)', 'controller',
     {'5V':'power_in','GND':'ground', **{f'D{i}':'bidirectional' for i in range(14)}, **{f'A{i}':'input' for i in range(6)}},
     ('5V','GND'), 5.0, 'https://docs.arduino.cc/hardware/uno-rev3/'),
 'lcd1602': part('HD44780-compatible 16×2 LCD (4-bit)', 'lcd',
     {'1':'ground','2':'power_in','3':'input','4':'input','5':'input','6':'input',
      **{str(i):'bidirectional' for i in range(7,15)},'15':'power_in','16':'ground'},
     tuple(str(i) for i in [1,2,3,4,5,6,11,12,13,14]), 5.0,
     'https://docs.arduino.cc/learn/electronics/lcd-displays/'),
}
LCD_LABELS = dict(zip(map(str,range(1,17)), ['VSS','VDD','VO','RS','RW','E','D0','D1','D2','D3','D4','D5','D6','D7','A','K']))

# Additional logical interfaces; package-specific ratings require datasheet review.
CATALOG.update({
 'ldr': part('Photoresistor (LDR)', 'ldr', {'1':'passive','2':'passive'}, ('1','2')),
 'thermistor': part('Generic thermistor', 'thermistor', {'1':'passive','2':'passive'}, ('1','2')),
 'connector3': part('Three-pin connector', 'connector', {'1':'passive','2':'passive','3':'passive'}),
 'connector4': part('Four-pin connector', 'connector', {str(i):'passive' for i in range(1,5)}),
 'arduino_mega': part('Arduino Mega 2560 Rev3 (logical headers)', 'controller',
     {'5V':'power_in','GND':'ground', **{f'D{i}':'bidirectional' for i in range(54)}, **{f'A{i}':'bidirectional' for i in range(16)}},
     ('5V','GND'), 5.0, 'https://docs.arduino.cc/hardware/mega-2560/'),
 'servo_generic': part('Generic RC servo (verify model voltage and current)', 'custom',
     {'VCC':'power_in','GND':'ground','SIG':'input'}, ('VCC','GND','SIG')),
})

# Logical module interfaces, not physical connector order.
CATALOG.update({
 'lcd1602_i2c_5v': part('16x2 LCD with 5 V I2C backpack', 'custom',
     {'VCC':'power_in','GND':'ground','SDA':'bidirectional','SCL':'bidirectional'}, ('VCC','GND','SDA','SCL'),5.0),
 'ssd1306_i2c_3v3': part('SSD1306 I2C OLED (3.3 V interface)', 'custom',
     {'VCC':'power_in','GND':'ground','SDA':'bidirectional','SCL':'bidirectional'}, ('VCC','GND','SDA','SCL'),3.3),
 'pushbutton': part('Momentary normally-open pushbutton','switch',{'1':'passive','2':'passive'},('1','2')),
 'piezo_passive': part('Passive piezo transducer','custom',{'1':'passive','2':'passive'},('1','2')),
 'capacitor_polarized': part('Polarized capacitor','capacitor',{'+':'passive','-':'passive'},('+','-')),
 'pnp': part('Generic PNP transistor','custom',{'B':'input','C':'passive','E':'passive'},('B','C','E')),
 'pmos': part('Generic P-channel MOSFET','custom',{'G':'input','D':'passive','S':'passive'},('G','D','S')),
 'relay_spdt': part('Generic SPDT relay (coil rating required)','custom',{'COIL1':'passive','COIL2':'passive','COM':'passive','NO':'passive','NC':'passive'},('COIL1','COIL2','COM')),
 'dc_motor': part('Brushed DC motor (rating required)','motor',{'+':'passive','-':'passive'},('+','-')),
 'fuse': part('Fuse (rating required)','custom',{'1':'passive','2':'passive'},('1','2')),
})

# Manufacturer-documented logical interfaces. Physical package mapping is separate.
CATALOG.update({
 'uln2003a': part('ULN2003A seven-channel sink driver','custom',
     {**{f'IN{i}':'input' for i in range(1,8)},'E':'ground',**{f'OUT{i}':'passive' for i in range(1,8)},'COM':'passive'},('E',),source='https://www.ti.com/product/ULN2003A'),
 'l293d': part('L293D quadruple half-H driver','custom',
     {'EN12':'input','IN1':'input','OUT1':'output','GND1':'ground','GND2':'ground','OUT2':'output','IN2':'input','VCC2':'power_in','EN34':'input','IN3':'input','OUT3':'output','GND3':'ground','GND4':'ground','OUT4':'output','IN4':'input','VCC1':'power_in'},('EN12','EN34','GND1','GND2','GND3','GND4','VCC1','VCC2'),source='https://www.ti.com/product/L293D'),
 'lm35': part('LM35 analog temperature sensor','custom',
     {'VS':'power_in','VOUT':'output','GND':'ground'},('VS','VOUT','GND'),source='https://www.ti.com/product/LM35'),
})

# Texas Instruments PDIP pin numbers, with logical pin names displayed.
CATALOG.update({
    'sn74hc14n': dict(part(
        'SN74HC14N Schmitt-trigger inverter (PDIP-14)', 'custom',
        {str(i): role for i, role in enumerate((
            'input','output','input','output','input','output','ground',
            'output','input','output','input','output','input','power_in',
        ), 1)}, ('7','14'), source='https://www.ti.com/lit/ds/symlink/sn74hc14.pdf'),
        pin_labels=dict(zip(map(str, range(1,15)),
            ('1A','1Y','2A','2Y','3A','3Y','GND','4Y','4A','5Y','5A','6Y','6A','VCC')))),
    'lm358n': dict(part(
        'LM358N dual operational amplifier (PDIP-8)', 'custom',
        {'1':'output','2':'input','3':'input','4':'passive',
         '5':'input','6':'input','7':'output','8':'power_in'}, ('4','8'),
        source='https://www.ti.com/lit/ds/symlink/lm358-n.pdf'),
        pin_labels=dict(zip(map(str, range(1,9)),
            ('OUT1','IN1-','IN1+','V-','IN2+','IN2-','OUT2','V+')))),
})

# AT89C51 and the original 14-terminal LM016L display.
CATALOG.update({
    'at89c51_pdip40': dict(part(
        'AT89C51 (PDIP-40)', 'controller',
        {**{str(i): 'bidirectional' for i in (*range(1,9), *range(10,18), *range(21,29), *range(32,40))},
         '9':'input', '18':'output', '19':'input', '20':'ground',
         '29':'output', '30':'output', '31':'input', '40':'power_in'},
        ('9','18','19','20','31','40'), 5.0,
        'https://ww1.microchip.com/downloads/en/DeviceDoc/doc0265.pdf'),
        pin_labels={**{str(i+1):f'P1.{i}' for i in range(8)},
                    **{str(i+10):f'P3.{i}' for i in range(8)},
                    **{str(i+21):f'P2.{i}' for i in range(8)},
                    **{str(39-i):f'P0.{i}' for i in range(8)},
                    '9':'RST', '18':'XTAL2', '19':'XTAL1', '20':'GND',
                    '29':'PSEN', '30':'ALE', '31':'EA', '40':'VCC'}),
    'lm016l': dict(part(
        'Hitachi LM016L 16×2 LCD (8-bit)', 'lcd',
        {'1':'ground','2':'power_in',**{str(i):'input' for i in range(3,15)}},
        tuple(map(str,range(1,15))), 5.0,
        'https://www.bitsavers.org/components/hitachi/_dataBooks/1987_Hitachi_Liquid_Crystal_Display_Modules.pdf'),
        pin_labels={str(i):LCD_LABELS[str(i)] for i in range(1,15)}),
    'crystal': part('Quartz crystal', 'crystal', {'1':'passive','2':'passive'}, ('1','2')),
})
