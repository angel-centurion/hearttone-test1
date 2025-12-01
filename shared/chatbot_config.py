# shared/chatbot_config.py
import requests
import json
from datetime import datetime

class ChatbotManager:
    def __init__(self):
        self.huggingface_token = ""  # Opcional para más requests
        self.context = self._get_base_context()
    
    def _get_base_context(self):
        return """Eres CardioBot, un asistente médico especializado en cardiología. 
        Ayudas a usuarios a entender su ritmo cardíaco basado en sus datos.

        Reglas:
        - Sé empático pero profesional
        - No des diagnósticos médicos
        - Recomienda consultar con profesionales
        - Usa emojis apropiados
        - Sé conciso pero útil

        Datos del usuario: {user_context}

        Pregunta del usuario: {user_message}

        Respuesta:"""
    
    def get_response(self, user_message, user_data=None):
        try:
            # Usar respuesta inteligente programada (gratuita)
            return self._get_smart_response(user_message, user_data)
            
        except Exception as e:
            print(f"Error en chatbot: {e}")
            return self._get_fallback_response(user_message, user_data)
    
    def _get_smart_response(self, user_message, user_data):
        """Respuesta inteligente con lógica programada"""
        user_message_lower = user_message.lower()
        
        # Análisis de salud
        if any(word in user_message_lower for word in ['cómo estoy', 'mi estado', 'análisis', 'salud']):
            return self._analyze_health(user_data) if user_data else self._get_health_analysis_placeholder()
        
        # Alertas y emergencias
        elif any(word in user_message_lower for word in ['alerta', 'emergencia', 'peligro', 'urgencia']):
            return self._handle_emergency_query(user_data)
        
        # Recomendaciones
        elif any(word in user_message_lower for word in ['consejo', 'recomendación', 'qué hacer', 'sugerencia']):
            return self._get_personalized_advice(user_data)
        
        # Ritmo cardíaco específico
        elif any(word in user_message_lower for word in ['ritmo', 'bpm', 'latidos', 'cardíaco']):
            return self._analyze_heart_rate(user_data)
        
        # Medicamentos
        elif any(word in user_message_lower for word in ['medicina', 'medicamento', 'pastilla', 'tratamiento']):
            return "💊 **Sobre medicamentos:** Siempre consulta con tu médico sobre medicamentos. Nunca modifiques tu tratamiento sin supervisión médica profesional."
        
        # Síntomas
        elif any(word in user_message_lower for word in ['síntoma', 'dolor', 'mareo', 'molestia']):
            return self._handle_symptoms_query(user_message_lower)
        
        # General
        else:
            return self._get_general_response(user_message, user_data)
    
    def _analyze_health(self, user_data):
        if not user_data:
            return "📊 Para darte un análisis personalizado, necesito que completes tus datos médicos en la aplicación."
        
        stats = user_data['statistics']
        profile = user_data['user_profile']
        
        analysis = f"**📈 ANÁLISIS DE TU SALUD CARDÍACA**\n\n"
        
        # Análisis basado en BPM promedio
        avg_bpm = stats['avg_bpm']
        if avg_bpm < 60:
            analysis += "• ❤️ **Ritmo:** Bradicardia leve detectada\n"
        elif avg_bpm > 100:
            analysis += "• ❤️ **Ritmo:** Taquicardia detectada\n"
        else:
            analysis += "• ❤️ **Ritmo:** Dentro de rangos normales\n"
        
        # Análisis de alertas
        alert_percentage = stats['alert_percentage']
        if alert_percentage < 10:
            analysis += "• ✅ **Estabilidad:** Excelente control\n"
        elif alert_percentage < 30:
            analysis += "• ⚠️ **Estabilidad:** Atención moderada necesaria\n"
        else:
            analysis += "• 🚨 **Estabilidad:** Alta frecuencia de alertas\n"
        
        # Recomendaciones específicas
        analysis += f"\n**💡 RECOMENDACIONES:**\n"
        
        if profile['heart_condition'] == 'taquicardia':
            analysis += "• Practica respiración profunda\n• Reduce cafeína\n• Maneja el estrés\n"
        elif profile['heart_condition'] == 'bradicardia':
            analysis += "• Ejercicio moderado regular\n• Dieta balanceada\n• Revisiones periódicas\n"
        else:
            analysis += "• Mantén hábitos saludables\n• Monitorea regularmente\n• Ejercicio aeróbico\n"
        
        analysis += "\n*Recuerda consultar con tu cardiólogo para evaluación profesional.*"
        
        return analysis
    
    def _handle_emergency_query(self, user_data):
        emergency_response = "🚨 **INFORMACIÓN IMPORTANTE:**\n\n"
        emergency_response += "**Si experimentas:**\n"
        emergency_response += "• Dolor intenso en el pecho\n• Dificultad para respirar\n• Mareo o desmayo\n• Palpitaciones muy fuertes\n\n"
        emergency_response += "**Busca atención médica inmediata**\n"
        emergency_response += "Llama a emergencias o ve al hospital más cercano.\n\n"
        
        if user_data and user_data['statistics']['alert_readings'] > 5:
            emergency_response += f"📊 Tienes {user_data['statistics']['alert_readings']} alertas recientes. Es importante que un médico revise tus datos."
        
        return emergency_response
    
    def _get_personalized_advice(self, user_data):
        advice = "💡 **RECOMENDACIONES PERSONALIZADAS**\n\n"
        
        if user_data:
            stats = user_data['statistics']
            profile = user_data['user_profile']
            
            # Consejos basados en BPM
            if stats['avg_bpm'] > 90:
                advice += "• 🧘 **Relajación:** Meditación 10 min/día\n• ☕ **Dieta:** Reduce cafeína\n• 💤 **Sueño:** 7-8 horas nocturnas\n"
            elif stats['avg_bpm'] < 55:
                advice += "• 🚶 **Ejercicio:** Caminata diaria 30 min\n• 🥩 **Nutrición:** Alimentos ricos en hierro\n• ⏰ **Rutina:** Horarios regulares\n"
            else:
                advice += "• 🏃 **Actividad:** Ejercicio moderado\n• 🥦 **Alimentación:** Dieta mediterránea\n• 😊 **Bienestar:** Manejo del estrés\n"
            
            # Consejos por condición
            if profile['heart_condition'] == 'taquicardia':
                advice += "\n**Específico para taquicardia:**\n• Evita deportes intensos\n• Mantén hidratación\n• Registra episodios\n"
            elif profile['heart_condition'] == 'bradicardia':
                advice += "\n**Específico para bradicardia:**\n• Ejercicio aeróbico regular\n• Evita cambios bruscos de temperatura\n"
        
        else:
            advice += "• 🏃 Ejercicio regular moderado\n• 🥗 Dieta baja en sal y grasas\n• 💤 Dormir 7-8 horas\n• 😊 Técnicas de relajación\n• 🚭 Evitar tabaco\n• 🍷 Alcohol con moderación\n"
        
        advice += "\n*Consulta con profesionales para recomendaciones específicas a tu caso.*"
        return advice
    
    def _analyze_heart_rate(self, user_data):
        if not user_data:
            return "❤️ **Ritmo Cardíaco:** Completa tus datos médicos para un análisis personalizado de tu BPM."
        
        stats = user_data['statistics']
        
        analysis = f"**❤️ ANÁLISIS DE RITMO CARDÍACO**\n\n"
        analysis += f"• 📊 **Promedio:** {stats['avg_bpm']} BPM\n"
        analysis += f"• 📈 **Máximo:** {stats['max_bpm']} BPM\n"
        analysis += f"• 📉 **Mínimo:** {stats['min_bpm']} BPM\n"
        analysis += f"• 🔄 **Variabilidad:** {stats['variability']} BPM\n\n"
        
        # Interpretación
        if stats['avg_bpm'] < 60:
            analysis += "**Interpretación:** Ritmo en reposo bajo (Bradicardia leve)\n"
        elif stats['avg_bpm'] > 100:
            analysis += "**Interpretación:** Ritmo en reposo alto (Taquicardia)\n"
        else:
            analysis += "**Interpretación:** Ritmo en reposo normal\n"
        
        return analysis
    
    def _handle_symptoms_query(self, user_message):
        if 'pecho' in user_message:
            return "💔 **Dolor de pecho:** Si el dolor es intenso, se extiende al brazo o cuello, o viene con dificultad para respirar, busca atención médica inmediata."
        elif 'mareo' in user_message or 'vértigo' in user_message:
            return "🌀 **Mareos:** Pueden relacionarse con presión arterial o ritmo cardíaco. Si son frecuentes o intensos, consulta con tu médico."
        elif 'palpitación' in user_message:
            return "💓 **Palpitaciones:** Sensación de latidos fuertes o irregulares. Si son frecuentes o vienen con otros síntomas, es importante evaluación médica."
        else:
            return "🤒 **Síntomas:** Cualquier síntoma persistente o que cause preocupación debe ser evaluado por un profesional de la salud."
    
    def _get_general_response(self, user_message, user_data):
        responses = [
            "🤖 ¡Hola! Soy CardioBot, tu asistente de salud cardíaca. Puedo ayudarte a entender tus datos de ritmo cardíaco y darte recomendaciones generales.",
            "💙 Hola! Como tu asistente cardíaco, puedo analizar tus datos de BPM, explicar alertas y dar consejos de estilo de vida saludable.",
            "👋 ¡Hola! Estoy aquí para ayudarte con información sobre tu salud cardíaca. ¿Tienes alguna pregunta específica sobre tus datos o síntomas?"
        ]
        
        return responses[hash(user_message) % len(responses)]
    
    def _get_health_analysis_placeholder(self):
        return "📊 **Para un análisis personalizado:**\n\n1. Completa tus datos médicos en 'Datos Médicos'\n2. Usa el monitor para recoger datos\n3. Vuelve para un análisis detallado\n\nMientras tanto, puedo responder preguntas generales sobre salud cardíaca."
    
    def _get_fallback_response(self, user_message, user_data):
        return "🤖 ¡Hola! Soy CardioBot. Estoy aquí para ayudarte con tu salud cardíaca. ¿Tienes alguna pregunta sobre tu ritmo cardíaco o necesitas recomendaciones?"

# Instancia global del chatbot
chatbot_manager = ChatbotManager()