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

#define RST_PIN		9		//
#define SS_PIN		10		//

char inData[20]; // Allocate some space for the string
char inChar=-1; // Where to store the character read
byte index = 0; // Index into array; where to store the character

MFRC522 mfrc522(SS_PIN, RST_PIN);	// Create MFRC522 instance

void setup() {
    Serial.begin(115200);		// Initialize serial communications with the PC
    while (!Serial);		// Do nothing if no serial port is opened (added for Arduinos based on ATMEGA32U4)
    SPI.begin();			// Init SPI bus
    mfrc522.PCD_Init();		// Init MFRC522
}

char Comp(char* This) {
    while (Serial.available() > 0) // Don't read unless
                            // there you know there is data
    {
        if(index < 19) // One less than the size of the array
        {
            inChar = Serial.read(); // Read a character
            inData[index] = inChar; // Store it
            index++; // Increment where to write next
            inData[index] = '\0'; // Null terminate the string
        }
    }

    if (strcmp(inData,This)  == 0) {
        for (int i=0;i<19;i++) {
            inData[i]=0;
        }
        index=0;
        return(0);
    }
    else {

        return(1);
    }
}


void loop() {
    if(Serial.available() > 0){
        if (Comp("RFIDSDetect")==0) {
            Serial.println("GOOD");
        }
    }

    // Look for new cards
    if ( ! mfrc522.PICC_IsNewCardPresent()) {
        return;
    }

    // Select one of the cards
    if ( ! mfrc522.PICC_ReadCardSerial()) {
        return;
    }

    mfrc522.PICC_UIDToSerial(&(mfrc522.uid));
    // mfrc522.PICC_DumpToSerial(&(mfrc522.uid));

    if(Serial.available() > 0){
        if(Serial.readString() == "kek")
        {
            for (int i = 0; i < 10; i++){
                Serial.println("GOOD");
                delay(1000);
            }
        }
    }

}
