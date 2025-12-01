#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ==================== CONFIGURACIÓN ====================
// 🔧 CAMBIA ESTOS VALORES
const char* ssid = "A26 de Angel";           // Nombre de tu WiFi
const char* password = "13082005";   // Contraseña de tu WiFi
const char* serverUrl = "http://hearttone.duckdns.org/admin/api/sensor-data";  // IP de tu servidor Flask
const char* deviceCode = "HR-SENSOR-A1B2-C3D4";  // Código del dispositivo

// ==================== CONFIGURACIÓN DE SIMULACIÓN ====================
int baseBPM = 75;              // BPM base (en reposo)
int bpmVariation = 15;         // Variación normal (+/- BPM)
unsigned long sendInterval = 3000;  // Enviar cada 3 segundos

// Variables de simulación
int currentBPM = baseBPM;
unsigned long lastSendTime = 0;
int simulationMode = 0;  // 0=Normal, 1=Ejercicio, 2=Alerta Alta, 3=Alerta Baja

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n\n");
  Serial.println("========================================");
  Serial.println("   ESP32 - SIMULADOR BPM REALISTA");
  Serial.println("========================================\n");
  
  // Conectar a WiFi
  connectWiFi();
  
  Serial.println("\n📋 INSTRUCCIONES:");
  Serial.println("   Envía por Serial:");
  Serial.println("   '1' = Modo Normal (60-90 BPM)");
  Serial.println("   '2' = Modo Ejercicio (100-140 BPM)");
  Serial.println("   '3' = Alerta Alta (130-160 BPM)");
  Serial.println("   '4' = Alerta Baja (40-50 BPM)");
  Serial.println("   '5' = BPM Aleatorio Extremo");
  Serial.println("========================================\n");
}

// ==================== LOOP PRINCIPAL ====================
void loop() {
  // Verificar comandos del Serial
  checkSerialCommands();
  
  // Enviar datos cada intervalo
  if (millis() - lastSendTime >= sendInterval) {
    lastSendTime = millis();
    
    // Generar BPM según el modo
    currentBPM = generateRealisticBPM();
    
    // Mostrar en Serial
    displayBPMInfo();
    
    // Enviar al servidor
    if (WiFi.status() == WL_CONNECTED) {
      sendBPMData(currentBPM);
    } else {
      Serial.println("❌ WiFi desconectado - Reconectando...");
      connectWiFi();
    }
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

// ==================== GENERAR BPM REALISTA ====================
int generateRealisticBPM() {
  int bpm;
  
  switch(simulationMode) {
    case 0:  // MODO NORMAL (60-90 BPM)
      bpm = random(60, 91);
      // Pequeñas variaciones graduales
      if (random(0, 100) < 30) {
        bpm = currentBPM + random(-3, 4);
        bpm = constrain(bpm, 60, 90);
      }
      break;
      
    case 1:  // MODO EJERCICIO (100-140 BPM)
      bpm = random(100, 141);
      // Simular picos de ejercicio
      if (random(0, 100) < 20) {
        bpm = random(120, 145);
      }
      break;
      
    case 2:  // ALERTA ALTA - Taquicardia (130-160 BPM)
      bpm = random(130, 161);
      // Ocasionalmente picos más altos
      if (random(0, 100) < 15) {
        bpm = random(150, 170);
      }
      break;
      
    case 3:  // ALERTA BAJA - Bradicardia (40-50 BPM)
      bpm = random(40, 51);
      // Ocasionalmente caídas más bajas
      if (random(0, 100) < 15) {
        bpm = random(35, 45);
      }
      break;
      
    case 4: {  // ALEATORIO EXTREMO - ✅ Agregamos llaves para crear scope
      int mode = random(0, 4);
      if (mode == 0) bpm = random(30, 50);   // Muy bajo
      else if (mode == 1) bpm = random(60, 90);   // Normal
      else if (mode == 2) bpm = random(100, 130); // Elevado
      else bpm = random(140, 180);  // Muy alto
      break;
    }
      
    default:
      bpm = random(60, 91);
  }
  
  // Asegurar que está en rango válido (30-220)
  return constrain(bpm, 30, 220);
}

// ==================== MOSTRAR INFO EN SERIAL ====================
void displayBPMInfo() {
  Serial.println("\n─────────────────────────────────────");
  Serial.print("⏰ Tiempo: ");
  Serial.print(millis() / 1000);
  Serial.println(" seg");
  
  Serial.print("🔄 Modo: ");
  switch(simulationMode) {
    case 0: Serial.println("NORMAL"); break;
    case 1: Serial.println("EJERCICIO"); break;
    case 2: Serial.println("ALERTA ALTA ⚠️"); break;
    case 3: Serial.println("ALERTA BAJA ⚠️"); break;
    case 4: Serial.println("ALEATORIO"); break;
  }
  
  Serial.print("💓 BPM Generado: ");
  Serial.print(currentBPM);
  
  // Indicador visual
  if (currentBPM < 60) {
    Serial.println(" 🔵 (Bajo)");
  } else if (currentBPM > 100) {
    Serial.println(" 🔴 (Alto)");
  } else {
    Serial.println(" 🟢 (Normal)");
  }
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

// ==================== COMANDOS POR SERIAL ====================
void checkSerialCommands() {
  if (Serial.available() > 0) {
    char command = Serial.read();
    
    switch(command) {
      case '1':
        simulationMode = 0;
        Serial.println("\n🟢 Modo NORMAL activado (60-90 BPM)");
        break;
      case '2':
        simulationMode = 1;
        Serial.println("\n🏃 Modo EJERCICIO activado (100-140 BPM)");
        break;
      case '3':
        simulationMode = 2;
        Serial.println("\n🔴 Modo ALERTA ALTA activado (130-160 BPM)");
        break;
      case '4':
        simulationMode = 3;
        Serial.println("\n🔵 Modo ALERTA BAJA activado (40-50 BPM)");
        break;
      case '5':
        simulationMode = 4;
        Serial.println("\n🎲 Modo ALEATORIO activado");
        break;
      default:
        // Ignorar otros caracteres
        break;
    }
  }
}