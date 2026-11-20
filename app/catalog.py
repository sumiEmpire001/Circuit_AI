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
