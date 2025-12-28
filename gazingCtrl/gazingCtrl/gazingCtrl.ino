#include "Arduino_LED_Matrix.h"
#define NOUT 3

int out[] = {6, 7, 8};  // 1st for openephys, 2nd for laser, 3rd for shocker

String message;
char inchar;
char inchar_prev;

int t_ref;
int t_laser_on;

int nOutByte = ceil(NOUT / 8.0);
ArduinoLEDMatrix matrix;


uint32_t led[] = {
  0x00000000,
  0x00000000,
  0x00000000
};

const uint32_t happy[] = {

    0x19819,

    0x80000001,

    0x81f8000

};

void setup() {
  // put your setup code here, to run once:
  for (int ipin = 0; ipin < NOUT ; ipin++) {
    pinMode(out[ipin], OUTPUT);
    digitalWrite(out[ipin], LOW);
  }

  message = "";
  inchar = '\n';
  inchar_prev = '\r';

  Serial.begin(115200);
  Serial.flush();
  matrix.begin();
  t_ref = millis();
}

void setLED() {
  led[2] = 0x00000000;
  for (int ibyte = 0; ibyte < nOutByte; ibyte++) {
    int nbit = min((NOUT - (ibyte * 8)), 8);
    for (int ibit = 0; ibit < nbit; ibit++) {
      led[2] |= digitalRead(out[ibit + ibyte * 8]) << (ibit + ibyte * 8);  
    }
  }
  matrix.loadFrame(led);
  // matrix.loadFrame(happy);  
  // delay(500);
}

void setOut(const char* bits) {
  unsigned int num;
  bits++;  // skip header ('o')

  for (int ibyte = 0; ibyte < nOutByte; ibyte++) {
    num = *bits++;
    int nbit = min((NOUT - (ibyte * 8)), 8);
    for (int ibit = 0; ibit < nbit; ibit++) {
      if (num & 1) {
        digitalWrite(out[ibit + ibyte * 8], HIGH);
        if (ibit == 1) {  // for 
            t_laser_on = millis() - t_ref;
            Serial.print('l');
            Serial.println(t_laser_on);
        }
      }
      else digitalWrite(out[ibit + ibyte * 8], LOW);
      num >>= 1;
    }
  }
  setLED();
}

void setOn(const char* bits) {
  unsigned int num;
  bits++;

  for (int ibyte = 0; ibyte < nOutByte; ibyte++) {
    num = *bits++;
    int nbit = min((NOUT - (ibyte * 8)), 8);
    for (int ibit = 0; ibit < nbit; ibit++) {
      if (num & 1) {
        digitalWrite(out[ibit + ibyte * 8], HIGH);
        if (ibit == 1) {  // for 
            t_laser_on = millis() - t_ref;
            Serial.print('l');
            Serial.println(t_laser_on);
        }
      }
      num >>= 1;
    }
  }
  setLED();
}

void setOff(const char* bits) {
  unsigned int num;
  bits++;

  for (int ibyte = 0; ibyte < nOutByte; ibyte++) {
    num = *bits++;
    int nbit = min((NOUT - (ibyte * 8)), 8);
    for (int ibit = 0; ibit < nbit; ibit++) {
      if (!(num & 1)) digitalWrite(out[ibit + ibyte * 8], LOW);
      num >>= 1;
    }
  }
  setLED();
}

void check_msg(String &m) {
  if ((m.charAt(0) == 'o') && (m.length() == nOutByte + 1)) {
    setOut(m.c_str());
  } else if ((m.charAt(0) == '+')  && (m.length() == nOutByte + 1)) {
    setOn(m.c_str());
  } else if ((m.charAt(0) == '-') && (m.length() == nOutByte + 1)) {
    setOff(m.c_str());
  } else if ((m.charAt(0) == 't') && (m.length() == 1)) {
    t_ref = millis();
  } else {
    Serial.print("Wrong msg: ");
    Serial.println(m);
  }
}

void loop() {
  // put your main code here, to run repeatedly:
  while (Serial.available() > 0) {
    inchar = Serial.read();
    
    if ((inchar == '\n') && (inchar_prev == '\r')) {
      check_msg(message);
      message = "";
      break;
    } else {
      if ((inchar_prev != '\r') || (message.length())) {
        message += inchar_prev;
      }
      inchar_prev = inchar;
    }
  }
}
