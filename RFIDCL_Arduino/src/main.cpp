/* Typical pin layout used:
* -----------------------------------------------------------------------------------------
*             MFRC522      Arduino       Arduino   Arduino    Arduino          Arduino
*             Reader/PCD   Uno           Mega      Nano v3    Leonardo/Micro   Pro Micro
* Signal      Pin          Pin           Pin       Pin        Pin              Pin
* -----------------------------------------------------------------------------------------
* RST/Reset   RST          9             5         D9         RESET/ICSP-5     RST
* SPI SS      SDA(SS)      10            53        D10        10               10
* SPI MOSI    MOSI         11 / ICSP-4   51        D11        ICSP-4           16
* SPI MISO    MISO         12 / ICSP-1   50        D12        ICSP-1           14
* SPI SCK     SCK          13 / ICSP-3   52        D13        ICSP-3           15
*/


#include <Arduino.h>
#include <SPI.h>
#include <MFRC522.h>

#define RST_PIN		9
#define SS_PIN		10

MFRC522 mfrc522(SS_PIN, RST_PIN);
String UID;

void setup() {
    Serial.begin(115200);
    SPI.begin();
    mfrc522.PCD_Init();
}

void loop() {
    if(Serial.available() > 0){
      int data = Serial.parseInt();
      if (data == 3) {
        Serial.println("GOOD");
      }else if(data == 1){
        tone(4, 1000);
        digitalWrite(2, HIGH);
        delay(100);
        noTone(4);
        digitalWrite(2, LOW);
        delay(50);
        tone(4, 1000);
        digitalWrite(2, HIGH);
        delay(100);
        noTone(4);
        digitalWrite(2, LOW);
      }else if(data == 2){
        tone(4, 300);
        digitalWrite(3, HIGH);
        delay(1000);
        noTone(4);
        digitalWrite(3, LOW);
      }
    }

    if ( ! mfrc522.PICC_IsNewCardPresent()) {
      return;
    }

    if ( ! mfrc522.PICC_ReadCardSerial()) {
      return;
    }


    UID = "";
    for (byte i = 0; i < mfrc522.uid.size; i++){
      UID += String(mfrc522.uid.uidByte[i], HEX);
    }
    Serial.println(UID);
    mfrc522.PICC_HaltA();

}
