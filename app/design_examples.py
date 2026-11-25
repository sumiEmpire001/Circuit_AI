from app.design import Design

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
