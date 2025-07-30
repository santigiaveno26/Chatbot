import os
from openai import OpenAI
import fitz  # PyMuPDF
import PyPDF2
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, scrolledtext, PhotoImage
from PIL import Image, ImageTk
import requests
import threading
import time

# Configuración inicial
client = OpenAI(
    api_key="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",  # Reemplazá con tu API key
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "http://localhost",  # o tu dominio si lo subís online
        "X-Title": "Chatbot Equilimpia"
    }
)
def leer_google_doc_como_texto(doc_id):
        url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            return f"⚠️ Error al descargar el documento (código {response.status_code})"
documento = leer_google_doc_como_texto("188FIPeiBigd1GtmyeoprlvRggjp5oZaImqYEg3vXJFk")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ChatbotGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        # === Paleta de colores personalizada ===
        self.color_bg = "#1B2B24"
        self.color_text = "#FAFAFA"
        self.color_accent = "#4CAF50"
        self.color_hover = "#388E3C"
        self.color_input = "#ECEFF1"
        self.color_detail = "#455A64"

        # === Tipografías ===
        self.font_title = ctk.CTkFont(family="Roboto", size=30, weight="bold",)
        self.font_subtitle = ctk.CTkFont(family="Roboto", size=22, weight="bold")
        self.font_regular = ctk.CTkFont(family="Roboto", size=16)
        self.iconbitmap("assets/favicon.ico")
        # Configuración de la ventana principal
        self.title("Equilimpia Chatbot")
        self.geometry("1000x700")
        self.minsize(800, 600)
        
        # Tipografía
        self.font_bold = ctk.CTkFont(family="Roboto", size=18, weight="bold")
        self.font_regular = ctk.CTkFont(family="Roboto", size=16)
        self.configure(fg_color=self.color_bg)  #
        # Estructura principal
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)  # Ahora solo hay una columna: la del chat

        # Área de chat principal
        self.chat_frame = ctk.CTkFrame(self, corner_radius=0)
        self.chat_frame.grid(row=0, column=0, sticky="nsew")
        self.chat_frame.grid_rowconfigure(1, weight=1)
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self.chat_frame.configure(fg_color=self.color_bg)
        
        
        # Barra de título del chat
        self.chat_header = ctk.CTkFrame(self.chat_frame, height=50, corner_radius=0)
        self.chat_header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.chat_header.grid_columnconfigure(0, weight=1)

        icon_image = tk.PhotoImage(file="assets/horse.png")  # PNG transparente recomendado
        self.iconphoto(False, icon_image)
        
        self.chat_title = ctk.CTkLabel(
            self.chat_header, 
            text="Asistente Virtual del prototipo Equilimpia", 
            font=self.font_bold,
            anchor="center"
        )
        self.chat_title.grid(row=0, column=0, padx=20, sticky="n",columnspan=2)
        
        # Área de mensajes
        self.chat_display = ctk.CTkTextbox(
            self.chat_frame,
            wrap=tk.WORD,
            font=self.font_regular,
            activate_scrollbars=True,
            fg_color="#2b2b2b",
            scrollbar_button_color="#4d4d4d"
        )
        self.chat_display.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.chat_display.tag_config("user", foreground="#4FC3F7")
        self.chat_display.tag_config("bot", foreground="#81C784")
        self.chat_display.configure(fg_color=self.color_detail, text_color=self.color_text)
        # Área de entrada
        self.input_frame = ctk.CTkFrame(self.chat_frame, height=80)
        self.input_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        self.input_frame.grid_columnconfigure(0, weight=1)
        
        self.user_input = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Escribi tu duda sobre el prototipo...",
            font=self.font_regular
        )
        self.user_input.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.user_input.bind("<Return>", lambda e: self.send_message())
        self.input_frame.configure(fg_color=self.color_bg)
        self.send_btn = ctk.CTkButton(
            self.input_frame,
            text="Send",
            command=self.send_message,
            fg_color="#1976D2",
            hover_color="#1565C0",
            width=100
        )
        self.send_btn.grid(row=0, column=1, padx=5, pady=5)
        
        # Inicializar historial
        self.historial = [
            {"role": "system", "content": self.load_context()}]
        
        # Scroll automático al final
        self.chat_display.see("end")
        
        # Cargar conocimiento inicial
        self.context = self.load_context()
        self.add_message("system", "Hola, soy el asistente virtual de la máquina Equilimpia. ¿En qué puedo ayudarte hoy?")
    
    def add_message(self, sender, message):
        tag = "user" if sender == "user" else "bot"
        avatar = "👤" if sender == "user" else "🤖"
        
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"{avatar} ", tag)
        self.chat_display.insert("end", f"{message}\n\n", tag)
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")
    
    def send_message(self):
        question = self.user_input.get()
        if not question.strip():
            return
        
        self.user_input.delete(0, "end")
        self.add_message("user", question)
        
        # Simular "typing..."
        typing_id = self.chat_display.index("end-1c")
        self.chat_display.insert("end", "🤖 ", "bot")
        typing_msg = self.chat_display.insert(typing_id, "Typing...", "bot")
        self.chat_display.see("end")
        
        # Procesamiento en segundo plano
        threading.Thread(target=self.process_query, args=(question, typing_id, typing_msg)).start()
    
    def process_query(self, question, typing_id, typing_msg):
        try:
            # Agregar la pregunta al historial
            self.historial.append({"role": "user", "content": question})
            
            # Obtener respuesta del modelo
            response = self.obtener_respuesta()
            
            # Reemplazar "typing..." con la respuesta real
            self.after(0, self.update_response, typing_id, typing_msg, response)
            
        except Exception as e:
            self.after(0, self.update_response, typing_id, typing_msg, f"Error: {str(e)}")
    
    def update_response(self, typing_id, typing_msg, response):
        self.chat_display.configure(state="normal")
        
        # Eliminar "Typing..." desde el índice
        self.chat_display.delete(typing_id, f"{typing_id}+{len('Typing...')}c")
        
        # Insertar mensaje del bot en nueva línea
        self.chat_display.insert("end", f"🤖 ¿{response}\n\n", "bot")
        
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")
        
    def load_context(self):

        contexto = documento[:4000]  # limitar tokens para evitar errores
        return f"""
                Eres un asistente técnico especializado en la máquina Equilimpia, un equipo diseñado para aspirar camas usadas de caballos y esparcirlas en el campo, reemplazando su quema y beneficiando al medio ambiente. Combinas funciones de aspiradora agrícola y estercolera.

                Tu tarea es responder únicamente preguntas técnicas y prácticas relacionadas con el funcionamiento, mantenimiento, uso, características y resolución de problemas de la máquina Equilimpia. Basá todas tus respuestas exclusivamente en el siguiente manual:
                {contexto}

                Usá un lenguaje claro, técnico pero accesible para usuarios con conocimientos básicos y medios en maquinaria agrícola. Evitá responder preguntas que no estén relacionadas con la máquina o que requieran información fuera del manual.

                Si la pregunta es ambigua, pedí que se aclare. Si no sabés la respuesta con base en el manual, respondé que no podés ayudar en ese tema.

                No des información extra, no hagas conjeturas ni inventes datos.

                Si te saludan, tu saludación es: "¡Hola! Soy el chatbot de la máquina Equilimpia. ¿Qué dudas tenés sobre el prototipo?, sin dar informacion demas si te saludan o no entendes la pregunta aclara"
                """
    def obtener_respuesta(self):
        """Obtener respuesta del modelo usando el historial"""
        try:
            respuesta = client.chat.completions.create(
                model="z-ai/glm-4.5-air:free",
                messages=self.historial
            )
            contenido = respuesta.choices[0].message.content
            # Agregar la respuesta al historial
            self.historial.append({"role": "assistant", "content": contenido})
            return contenido
        except Exception as e:
            return f"Error en API: {str(e)}"
    
if __name__ == "__main__":
    app = ChatbotGUI()
    app.mainloop()
