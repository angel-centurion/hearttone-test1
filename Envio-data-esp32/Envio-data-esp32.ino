#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ==================== CONFIGURACIÓN ====================
// 🔧 CAMBIA ESTOS VALORES
const char* ssid = "A26 de Angel";           // Nombre de tu WiFi
const char* password = "13082005";   // Contraseña de tu WiFi
const char* serverUrl = "http://hearttone.duckdns.org/admin/api/sensor-data";
const char* deviceCode = "HR-SENSOR-A1B2-C3D4";

// ==================== CONFIGURACIÓN UART ====================
// Pines UART para recibir datos del sensor
#define RXD2 16  // GPIO16 - Conectar al TX del sensor
#define TXD2 17  // GPIO17 - Conectar al RX del sensor (opcional)

// ==================== VARIABLES GLOBALES ====================
unsigned long sendInterval = 3000;  // Enviar cada 3 segundos
unsigned long lastSendTime = 0;
unsigned long lastBPMReceived = 0;
const unsigned long BPM_TIMEOUT = 10000;  // Timeout de 10 segundos sin datos

int currentBPM = 0;
bool bpmDataValid = false;
String uartBuffer = "";

// ==================== SETUP ====================
void setup() {
  // Serial para debug (USB)
  Serial.begin(115200);
  delay(1000);
  
  // UART2 para recibir datos del sensor BPM
  Serial2.begin(9600, SERIAL_8N1, RXD2, TXD2);
  
  Serial.println("\n\n");
  Serial.println("========================================");
  Serial.println("   ESP32 - RECEPTOR BPM POR UART");
  Serial.println("========================================\n");
  
  Serial.println("📡 Configuración UART:");
  Serial.printf("   RX Pin: GPIO%d\n", RXD2);
  Serial.printf("   TX Pin: GPIO%d\n", TXD2);
  Serial.println("   Baudrate: 9600");
  Serial.println("   Formato esperado: 'BPM:75' o '75'");
  Serial.println("========================================\n");
  
  // Conectar a WiFi
  connectWiFi();
  
  Serial.println("\n✅ Sistema listo - Esperando datos BPM...\n");
}

// ==================== LOOP PRINCIPAL ====================
void loop() {
  // 🔍 DEBUG: Mostrar estado cada 5 segundos
  static unsigned long lastDebug = 0;
  if (millis() - lastDebug > 5000) {
    lastDebug = millis();
    Serial.print("🔍 UART disponible: ");
    Serial.print(Serial2.available());
    Serial.print(" bytes | BPM válido: ");
    Serial.println(bpmDataValid ? "SI" : "NO");
  }
  
  // Leer datos del UART
  readBPMFromUART();
  
  // Verificar timeout de datos
  checkBPMTimeout();
  
  // Enviar datos cada intervalo
  if (millis() - lastSendTime >= sendInterval) {
    lastSendTime = millis();
    
    if (bpmDataValid) {
      // Mostrar en Serial
      displayBPMInfo();
      
      // Enviar al servidor
      if (WiFi.status() == WL_CONNECTED) {
        sendBPMData(currentBPM);
      } else {
        Serial.println("❌ WiFi desconectado - Reconectando...");
        connectWiFi();
      }
    } else {
      Serial.println("⚠️  No hay datos BPM válidos del sensor");
    }
  }
}

// ==================== LEER BPM DESDE UART ====================
void readBPMFromUART() {
  while (Serial2.available() > 0) {
    char inChar = (char)Serial2.read();
    
    // 🔍 DEBUG: Mostrar cada carácter recibido
    Serial.print("📥 Byte recibido: ");
    Serial.print((int)inChar);
    Serial.print(" (");
    if (inChar >= 32 && inChar <= 126) {
      Serial.print(inChar);
    } else if (inChar == '\n') {
      Serial.print("\\n");
    } else if (inChar == '\r') {
      Serial.print("\\r");
    } else {
      Serial.print("?");
    }
    Serial.println(")");
    
    // Acumular caracteres hasta encontrar nueva línea
    if (inChar == '\n' || inChar == '\r') {
      if (uartBuffer.length() > 0) {
        Serial.print("🔍 Procesando buffer: [");
        Serial.print(uartBuffer);
        Serial.println("]");
        parseBPMData(uartBuffer);
        uartBuffer = "";
      }
    } else {
      uartBuffer += inChar;
      
      // Evitar buffer overflow
      if (uartBuffer.length() > 50) {
        Serial.println("⚠️  Buffer overflow, limpiando...");
        uartBuffer = "";
      }
    }
  }
}

// ==================== PARSEAR DATOS BPM ====================
void parseBPMData(String data) {
  data.trim();  // Eliminar espacios en blanco
  
  int bpm = 0;
  bool validData = false;
  
  // Formato 1: "BPM:75" o "bpm:75"
  if (data.startsWith("BPM:") || data.startsWith("bpm:")) {
    String bpmStr = data.substring(4);
    bpm = bpmStr.toInt();
    validData = true;
  }
  // Formato 2: "HEARTRATE:75" o "HR:75"
  else if (data.startsWith("HEARTRATE:") || data.startsWith("heartrate:")) {
    String bpmStr = data.substring(10);
    bpm = bpmStr.toInt();
    validData = true;
  }
  else if (data.startsWith("HR:") || data.startsWith("hr:")) {
    String bpmStr = data.substring(3);
    bpm = bpmStr.toInt();
    validData = true;
  }
  // Formato 3: Solo número "75"
  else if (data.length() > 0 && isDigit(data.charAt(0))) {
    bpm = data.toInt();
    validData = true;
  }
  // Formato 4: JSON simple {"bpm":75}
  else if (data.startsWith("{")) {
    StaticJsonDocument<128> doc;
    DeserializationError error = deserializeJson(doc, data);
    if (!error && doc.containsKey("bpm")) {
      bpm = doc["bpm"];
      validData = true;
    }
  }
  
  // Validar rango de BPM (30-220)
  if (validData && bpm >= 30 && bpm <= 220) {
    currentBPM = bpm;
    bpmDataValid = true;
    lastBPMReceived = millis();
    
    Serial.print("📩 BPM recibido: ");
    Serial.print(currentBPM);
    Serial.println(" ✓");
  } else if (validData) {
    Serial.print("⚠️  BPM fuera de rango: ");
    Serial.println(bpm);
  } else {
    Serial.print("❌ Formato inválido: ");
    Serial.println(data);
  }
}

// ==================== VERIFICAR TIMEOUT ====================
void checkBPMTimeout() {
  if (bpmDataValid && (millis() - lastBPMReceived > BPM_TIMEOUT)) {
    bpmDataValid = false;
    Serial.println("⚠️  TIMEOUT: No se reciben datos del sensor");
  }
}

// ==================== CONECTAR WIFI ====================
void connectWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("🔌 Conectando a WiFi");
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi conectado");
    Serial.print("📍 IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n❌ No se pudo conectar a WiFi");
    Serial.println("⚠️  Verifica SSID y contraseña");
  }
}

// ==================== MOSTRAR INFO EN SERIAL ====================
void displayBPMInfo() {
  Serial.println("\n─────────────────────────────────────");
  Serial.print("⏰ Tiempo: ");
  Serial.print(millis() / 1000);
  Serial.println(" seg");
  
  Serial.print("💓 BPM Actual: ");
  Serial.print(currentBPM);
  
  // Indicador visual
  if (currentBPM < 60) {
    Serial.println(" 🔵 (Bajo)");
  } else if (currentBPM > 100) {
    Serial.println(" 🔴 (Alto)");
  } else {
    Serial.println(" 🟢 (Normal)");
  }
  
  Serial.print("📡 Última recepción: ");
  Serial.print((millis() - lastBPMReceived) / 1000);
  Serial.println(" seg atrás");
}

// ==================== ENVIAR DATOS AL SERVIDOR ====================
void sendBPMData(int bpm) {
  HTTPClient http;
  
  Serial.println("📤 Enviando al servidor...");
  
  // Iniciar conexión
  http.begin(serverUrl);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(5000);  // Timeout de 5 segundos
  
  // Crear JSON
  StaticJsonDocument<256> doc;
  doc["device_code"] = deviceCode;
  doc["bpm"] = bpm;
  
  String jsonData;
  serializeJson(doc, jsonData);
  
  Serial.print("   JSON: ");
  Serial.println(jsonData);
  
  // Enviar POST
  int httpResponseCode = http.POST(jsonData);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    
    Serial.print("✅ Respuesta del servidor [");
    Serial.print(httpResponseCode);
    Serial.println("]:");
    
    // Parsear respuesta
    StaticJsonDocument<512> responseDoc;
    DeserializationError error = deserializeJson(responseDoc, response);
    
    if (!error) {
      Serial.print("   Usuario: ");
      Serial.println(responseDoc["user"].as<String>());
      
      Serial.print("   BPM: ");
      Serial.println(responseDoc["bpm"].as<int>());
      
      Serial.print("   Límites: ");
      Serial.println(responseDoc["limits"].as<String>());
      
      if (responseDoc["is_alert"]) {
        Serial.println("\n🚨🚨🚨 ALERTA DETECTADA 🚨🚨🚨");
        Serial.print("   Mensaje: ");
        Serial.println(responseDoc["alert_message"].as<String>());
        Serial.println("🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨");
      } else {
        Serial.println("   ✓ Lectura normal");
      }
    } else {
      Serial.println("   Respuesta: " + response);
    }
  } else {
    Serial.print("❌ Error HTTP: ");
    Serial.println(httpResponseCode);
    
    if (httpResponseCode == -1) {
      Serial.println("   Posibles causas:");
      Serial.println("   - Servidor Flask no está corriendo");
      Serial.println("   - IP incorrecta");
      Serial.println("   - Puerto incorrecto");
    }
  }
  
  http.end();
}