import sys
import os
import time
import base64
import keyboard
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchWindowException, WebDriverException
from selenium.webdriver.edge.options import Options as EdgeOptions
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from tkinter import ttk
from tkinter import Tk, Button, Entry, Label, messagebox, StringVar, OptionMenu, Frame, Toplevel, OptionMenu, END, Canvas, Scrollbar, VERTICAL, RIGHT, Y, BOTH, LEFT, BOTTOM, X, HORIZONTAL
from tkinter.filedialog import askdirectory
from tkinter import TclError  
import threading
import re

def get_base_path():
    # Determinar si estamos ejecutando desde un .exe o desde el script
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def close_program():
    root.destroy()

def toggle_topmost():
    global is_topmost
    is_topmost = not is_topmost
    root.attributes('-topmost', is_topmost)
    # Cambiar el texto del botón según el estado
    if is_topmost:
        topmost_button.config(text="📌")  # Candado abierto
    else:
        topmost_button.config(text="🔒")  # Candado cerrado

def set_widgets_state(state):
    for widget in root.winfo_children():
        try:
            widget.configure(state=state)
        except TclError:
            pass  # Ignorar los widgets que no tienen la opción "state"

def keep_window_on_top(window, duration=5000):
    """
    Mantiene la ventana en primer plano durante un tiempo especificado.
    """
    window.attributes('-topmost', 1)
    window.after(duration, lambda: window.attributes('-topmost', 0))

def show_loading_screen(root):
    loading_screen = Toplevel(root)
    loading_screen.geometry("300x100")
    loading_label = Label(loading_screen, text="Cargando, por favor espera...")
    loading_label.pack(pady=20)
    
    # Crear una barra de progreso
    progress = ttk.Progressbar(loading_screen, orient=HORIZONTAL, length=200, mode='determinate')
    progress.pack(pady=10)
    
    # Deshabilitar widgets de la interfaz
    set_widgets_state('disabled')

    # Ocultar la ventana de Edge
    driver.minimize_window()
    
    def update_progress(value):
        progress['value'] = value
        if value < 100:
            root.after(60, update_progress, value + 1)
        else:
            on_load_complete()

    def on_load_complete():
        loading_screen.destroy()
        set_widgets_state('normal')
        driver.maximize_window()

    # Vincular el evento de cierre de la ventana de carga al cierre del programa
    loading_screen.protocol("WM_DELETE_WINDOW", close_program)

    # Iniciar la actualización de la barra de progreso
    update_progress(0)

def is_valid_url(url):
    # Expresión regular para validar URL
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// o https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # dominio...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...o dirección IP
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...o dirección IPv6
        r'(?::\d+)?'  # puerto opcional
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return re.match(regex, url) is not None

# Configuración de Selenium para Edge
def setup_driver():
    try:
        # Configuración automática con webdriver-manager (requiere internet)
        driver_path = EdgeChromiumDriverManager().install()
    except Exception as e:
        # Fallback a driver local si hay error de conexión
        base_path = get_base_path()
        driver_path = os.path.join(base_path, "drivers", "msedgedriver.exe")
        if not os.path.exists(driver_path):
            raise FileNotFoundError(f"No se encontró el driver en: {driver_path} | Error original: {str(e)}")

    # Configurar opciones del navegador
    options = EdgeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    options.add_argument('--start-maximized')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # Configurar servicio y driver
    service = EdgeService(driver_path)
    
    try:
        driver = webdriver.Edge(service=service, options=options)
    except Exception as e:
        raise RuntimeError(f"Error al iniciar Edge: {str(e)}")

    return driver

# Variables globales
screenshot_dir = None
current_mode = "completo"
current_url = ""
hotkey = "alt+shift"
last_created_items = []

# Configuración por modo
mode_settings = {
    "completo": {
        "counter": 1,
        "base_name": "captura_completa",
        "counter_entry": None,
        "name_entry": None
    },
    "elemento": {
        "counter": 1,
        "folder_name": "elemento",
        "file_prefix": "elemento",
        "counter_entry": None,
        "folder_entry": None,
        "file_entry": None
    },
    "ventana": {
        "counter": 1,
        "base_name": "captura_ventana",
        "counter_entry": None,
        "name_entry": None
    }
}

def show_info():

    # Crear ventana emergente botones adicionales
    info_window = Toplevel(root)
    info_window.title("Botones adicionales")
    info_window.geometry("400x200")
    
    # Crear Frame contenedor
    main_frame = Frame(info_window, bg="white")
    main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
    
    # Título principal
    Label(main_frame, 
          text="Información de Botones Adicionales", 
          font=("Arial", 12, "bold"),
          bg="white").pack(pady=(0,10))
    
    # Sección de botones adicionales
    info_text = (
        "1. Botón de Superposición (🔒): Mantiene la ventana de la aplicación en primer plano.\n"
    )
    Label(main_frame, text=info_text, wraplength=380, justify="left", bg="white").pack(anchor="w", pady=5)
    
    # Botón de Superposición
    icon_label = Label(main_frame, text="🔒", font=("Arial", 12), bg="white")
    icon_label.pack(anchor="w", pady=(10, 0))


    # Crear ventana emergente del manual de información
    info_window = Toplevel(root)
    info_window.title("WebShot v5.0 - Información")
    info_window.geometry("500x600")
    
    # Crear Canvas y Scrollbar
    canvas = Canvas(info_window, bg="white")
    scrollbar = Scrollbar(info_window, orient=VERTICAL, command=canvas.yview)
    
    # Configurar Canvas
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    # Frame contenedor dentro del Canvas
    main_frame = Frame(canvas, bg="white")
    canvas.create_window((0, 0), window=main_frame, anchor="nw")
    
    # Posicionar elementos
    canvas.pack(side=LEFT, fill=BOTH, expand=True)
    scrollbar.pack(side=RIGHT, fill=Y)
    
    # Habilitar scroll con rueda del ratón
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    # Función para crear secciones
    def create_section(parent, title, content, bg_color="#F0F0F0"):
        section_frame = Frame(parent, bd=1, relief="solid", padx=10, pady=10, bg=bg_color)
        Label(section_frame, text=title, font=("Arial", 11, "bold"), bg=bg_color).pack(anchor="w")
        Label(section_frame, 
              text=content, 
              justify="left", 
              wraplength=850,
              bg=bg_color).pack(anchor="w", pady=(5,0))
        return section_frame
    
    # Título principal
    Label(main_frame, 
          text="WebShot v5.0 - Información Completa", 
          font=("Arial", 12, "bold"),
          bg="white").pack(pady=(0,10))
    
    # ========== SECCIÓN MODOS DE CAPTURA ==========
    modos_captura = """
    1. Completo: Captura toda la página web (scroll completo)
    2. Ventana: Captura solo el área visible del navegador
    3. Elemento: Captura un elemento específico (requiere XPATH)
    """
    create_section(main_frame, "Modos de Captura", modos_captura).pack(fill="x", pady=5)
    
    # Aclaraciones Modos
    aclaraciones_modos = """
    - Para modo 'elemento':
      1. Click derecho sobre el elemento > "Inspeccionar"
      2. En el código fuente, buscar la línea correspondiente
      3. Click derecho > "Copiar XPATH"
      4. Si no encuentra XPATH relativo, usar el absoluto
    """
    create_section(main_frame, "Aclaraciones: Modos de Captura", aclaraciones_modos, "#E0F7FA").pack(fill="x", pady=5)
    
    # ========== SECCIÓN FUNCIONALIDADES ==========
    funcionalidades = """
    - Contadores personalizables para cada modo
    - Nombres personalizados para archivos/carpetas
    - Combinación de teclas configurable
    - Deshacer última acción (elimina archivos/carpetas)
    - Generación automática de XPATHs en modo completo
    """
    create_section(main_frame, "Funcionalidades Principales", funcionalidades).pack(fill="x", pady=5)
    
    # Aclaraciones Funcionalidades
    aclaraciones_func = """
    - Al usar 'Deshacer última acción' múltiples veces:
      * Solo afecta la acción más reciente
      * No elimina acciones anteriores acumuladas
    """
    create_section(main_frame, "Aclaraciones: Funcionalidades", aclaraciones_func, "#E0F7FA").pack(fill="x", pady=5)
    
    # ========== SECCIÓN CONTROLES ==========
    controles = """
    - Botón 'Ir': Navegar a URL especificada
    - Botón 'Realizar Captura': Ejecuta captura según modo
    - Botón 'Deshacer Última Captura': Elimina última captura
    - Botón 'Cambiar Directorio': Selecciona carpeta destino
    - Botón 'Detectar': Captura combinación de teclas
    - Botón 'Cambiar': Guarda nueva combinación
    - Campos de texto: Personaliza nombres y contadores
    - Selector de modo: Cambia entre tipos de captura
    """
    create_section(main_frame, "Controles Disponibles", controles).pack(fill="x", pady=5)
    
    # Aclaraciones Controles
    aclaraciones_controles = """
    - Deshacer última acción en modo 'elemento':
      * Eliminan carpeta completa con todo su contenido
    - Proceso cambio de atajo:
      1. Usar 'Detectar'
      2. Presionar combinación deseada
      3. Pulsar 'Cambiar' para guardar
    """
    create_section(main_frame, "Aclaraciones: Controles", aclaraciones_controles, "#E0F7FA").pack(fill="x", pady=5)
    
    # ========== SECCIÓN ATAJOS ==========
    atajos = """
    - Alt+Shift: Realizar captura rápida
    - Contadores se actualizan automáticamente
    - Cierre seguro: Al cerrar la ventana se cierra el navegador
    """
    create_section(main_frame, "Atajos y Comportamientos", atajos).pack(fill="x", pady=5)

def fullpage_screenshot(driver, file_path):
    try:
        time.sleep(0.3)
        result = driver.execute_cdp_cmd('Page.captureScreenshot', {
            'captureBeyondViewport': True,
            'fromSurface': True,
            'format': 'png'
        })
        image_data = base64.b64decode(result['data'])
        with open(file_path, 'wb') as f:
            f.write(image_data)
        return True
    except Exception as e:
        print(f"Error en captura completa: {str(e)}")
        return False

def navigate_to_url():
    global current_url, driver
    url = url_entry.get()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    if not is_valid_url(url):
        messagebox.showerror("Error", "La URL introducida no es válida.")
        return

    try:
        # Intentar obtener la ventana activa del navegador
        driver.current_window_handle  # Esto debería lanzar una excepción si no hay ventana activa
        driver.get(url)
    except (NoSuchWindowException, WebDriverException):
        # Si no hay ventana activa, reiniciar el WebDriver
        driver.quit()
        driver = setup_driver()  # Reiniciar el WebDriver
        driver.get(url)
        driver.switch_to.window(driver.window_handles[-1])

    root.focus_force()  # Recuperar el enfoque en la ventana principal de Tkinter
    keep_window_on_top(root, duration=3000)  # Mantener la ventana en primer plano durante 3 segundos

    try:
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        current_url = url
        messagebox.showinfo("Éxito", "Página cargada correctamente")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar la página: {str(e)}")

def capture_completo_mode():
    global last_created_items
    last_created_items = []
    update_mode_settings()
    settings = mode_settings["completo"]
    
    if not current_url:
        messagebox.showerror("Error", "Primero carga una URL válida")
        return

    try:
        screenshot_name = f"{settings['base_name']}_{settings['counter']}.png"
        xpaths_name = f"xpaths_{settings['base_name']}_{settings['counter']}.txt"
        
        screenshot_path = os.path.join(screenshot_dir, screenshot_name)
        xpaths_path = os.path.join(screenshot_dir, xpaths_name)

        if fullpage_screenshot(driver, screenshot_path):
            last_created_items.extend([screenshot_path, xpaths_path])
            
            with open(xpaths_path, 'w', encoding='utf-8') as f:
                elements = driver.find_elements(By.XPATH, "//*")
                for element in elements:
                    try:
                        xpath = driver.execute_script(
                            """return (function(el) {
                                if (!el || !el.tagName) return null;
                                let path = [];
                                while (el.nodeType === Node.ELEMENT_NODE) {
                                    let selector = el.tagName.toLowerCase();
                                    if (el.id) {
                                        selector += '[@id="' + el.id + '"]';
                                        path.unshift(selector);
                                        break;
                                    } else {
                                        let sib = el, nth = 1;
                                        while (sib = sib.previousElementSibling) {
                                            if (sib.tagName.toLowerCase() === selector) nth++;
                                        }
                                        if (nth != 1) selector += "[" + nth + "]";
                                        path.unshift(selector);
                                    }
                                    el = el.parentNode;
                                }
                                return path.length ? "/" + path.join("/") : null;
                            })(arguments[0]);""",
                            element
                        )
                        if xpath:
                            f.write(xpath + "\n")
                    except:
                        continue

            settings['counter'] += 1
            settings['counter_entry'].delete(0, 'end')
            settings['counter_entry'].insert(0, str(settings['counter']))
            messagebox.showinfo("Éxito", f"Captura {screenshot_name} y XPATHs guardados")
        else:
            messagebox.showerror("Error", "Captura fallida")

    except Exception as e:
        messagebox.showerror("Error", f"Error en captura: {str(e)}")

def undo_last_action():
    global last_created_items
    if not last_created_items:
        messagebox.showinfo("Información", "No hay acciones para deshacer")
        return
    
    try:
        for path in last_created_items:
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
        
        current_settings = mode_settings[current_mode]
        if current_settings['counter'] > 1:
            current_settings['counter'] -= 1
            current_settings['counter_entry'].delete(0, 'end')
            current_settings['counter_entry'].insert(0, str(current_settings['counter']))
        
        messagebox.showinfo("Éxito", "Última acción deshecha correctamente")
        last_created_items = []
        
    except Exception as e:
        messagebox.showerror("Error", f"Error al deshacer: {str(e)}")

def capture_element_mode():
    global last_created_items
    last_created_items = []
    update_mode_settings()
    settings = mode_settings["elemento"]
    element_xpath = xpath_entry.get()
    absolute_xpath = abs_xpath_entry.get()

    if not element_xpath and not absolute_xpath:
        messagebox.showerror("Error", "Debes introducir al menos un XPATH")
        return

    try:
        # Localizar el elemento inicial
        element = None
        original_url = driver.current_url
        
        if element_xpath:
            try:
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, element_xpath))
                )
            except:
                pass

        if not element and absolute_xpath:
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, absolute_xpath))
            )

        if not element:
            messagebox.showerror("Error", "No se encontró el elemento con los XPATH proporcionados")
            return

        # Preparar entorno
        base_counter = settings['counter']
        element_dir = os.path.join(screenshot_dir, f"{settings['folder_name']}_{base_counter}")
        os.makedirs(element_dir, exist_ok=True)
        last_created_items.append(element_dir)

        with open(os.path.join(element_dir, "xpath_utilizado.txt"), 'w', encoding='utf-8') as f:
            f.write(element_xpath if element_xpath else absolute_xpath)

        # Scroll y espera
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
        time.sleep(0.8)

        # Verificar las dimensiones del elemento
        if element.size['width'] == 0 or element.size['height'] == 0:
            messagebox.showerror("Error", "No se puede capturar la captura de pantalla: El elemento tiene un ancho o alto de 0.")
            return

        # 1. Captura NORMAL
        normal_path = os.path.join(element_dir, f"{settings['file_prefix']}_normal_{base_counter}.png")
        element.screenshot(normal_path)
        last_created_items.append(normal_path)

        # 2. Captura HOVER
        try:
            original_bg = element.value_of_css_property('background-color')
            ActionChains(driver)\
                .move_to_element(element)\
                .pause(0.8)\
                .perform()
            
            # Esperar cambio visual
            WebDriverWait(driver, 2).until(
                lambda d: element.value_of_css_property('background-color') != original_bg
                or element.value_of_css_property('cursor') == 'pointer'
            )
            
            # Verificar las dimensiones del elemento después del hover
            if element.size['width'] == 0 or element.size['height'] == 0:
                messagebox.showerror("Error", "No se puede capturar la captura de pantalla: El elemento tiene un ancho o alto de 0.")
                return
            
            # Tomar captura hover
            hover_path = os.path.join(element_dir, f"{settings['file_prefix']}_hover_{base_counter}.png")
            element.screenshot(hover_path)
            last_created_items.append(hover_path)
            
            # Resetear hover
            ActionChains(driver).move_by_offset(10, 10).perform()
            time.sleep(0.3)
        except Exception as e:
            messagebox.showwarning("Advertencia Hover", f"No se detectaron cambios visuales: {str(e)}")

        # 3. Captura CLICK
        try:
            # Guardar estado original
            original_window = driver.current_window_handle
            original_url = driver.current_url

            # Hacer click y esperar cambios
            element.click()
            time.sleep(0.5)
            
            # Esperar carga de nueva página o cambio
            WebDriverWait(driver, 3).until(
                lambda d: d.current_url != original_url 
                or EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'active')]"))
            )
            
            # Relocalizar el elemento después del click
            new_element = driver.find_element(By.XPATH, element_xpath if element_xpath else absolute_xpath)
            
            # Verificar las dimensiones del nuevo elemento después del click
            if new_element.size['width'] == 0 or new_element.size['height'] == 0:
                messagebox.showerror("Error", "No se puede capturar la captura de pantalla: El nuevo elemento tiene un ancho o alto de 0.")
                return
            
            # Tomar captura post-click
            click_path = os.path.join(element_dir, f"{settings['file_prefix']}_click_{base_counter}.png")
            new_element.screenshot(click_path)
            last_created_items.append(click_path)

            # Restaurar estado original si hay nueva pestaña
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(original_window)
            elif driver.current_url != original_url:
                driver.back()
                WebDriverWait(driver, 3).until(EC.url_to_be(original_url))

        except Exception as e:
            messagebox.showwarning("Advertencia Click", f"Error en captura click: {str(e)}")

        # Actualizar contador
        settings['counter'] += 1
        settings['counter_entry'].delete(0, 'end')
        settings['counter_entry'].insert(0, str(settings['counter']))
        messagebox.showinfo("Éxito", f"Capturas del elemento guardadas en {element_dir}")

    except Exception as e:
        messagebox.showerror("Error", f"Error general capturando elemento: {str(e)}")

def capture_window_mode():
    global last_created_items
    last_created_items = []
    update_mode_settings()
    settings = mode_settings["ventana"]
    if not current_url:
        messagebox.showerror("Error", "Primero carga una URL válida")
        return

    try:
        screenshot_name = f"{settings['base_name']}_{settings['counter']}.png"
        screenshot_path = os.path.join(screenshot_dir, screenshot_name)
        
        driver.save_screenshot(screenshot_path)
        last_created_items.append(screenshot_path)
        
        settings['counter'] += 1
        settings['counter_entry'].delete(0, 'end')
        settings['counter_entry'].insert(0, str(settings['counter']))
        messagebox.showinfo("Éxito", f"Captura de ventana {screenshot_name} guardada")

    except Exception as e:
        messagebox.showerror("Error", f"Error en captura de ventana: {str(e)}")

def update_mode_settings():
    current = mode_settings[current_mode]
    if current_mode == "completo":
        current['base_name'] = current['name_entry'].get() or "captura_completa"
        current['counter'] = int(current['counter_entry'].get() or 1)
    elif current_mode == "ventana":
        current['base_name'] = current['name_entry'].get() or "captura_ventana"
        current['counter'] = int(current['counter_entry'].get() or 1)
    elif current_mode == "elemento":
        current['folder_name'] = current['folder_entry'].get() or "elemento"
        current['file_prefix'] = current['file_entry'].get() or "elemento"
        current['counter'] = int(current['counter_entry'].get() or 1)

def change_capture_mode(*args):
    global current_mode
    current_mode = mode_var.get()
    
    normal_frame.grid_remove()
    window_frame.grid_remove()
    element_frame.grid_remove()
    xpath_frame.grid_remove()
    
    if current_mode == "completo":
        normal_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
    elif current_mode == "ventana":
        window_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
    elif current_mode == "elemento":
        element_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        xpath_frame.grid(row=5, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
    
    update_mode_settings()

def change_screenshot_dir():
    global screenshot_dir
    new_dir = askdirectory(title="Seleccionar nueva carpeta para capturas")
    if new_dir:
        screenshot_dir = new_dir
        dir_label.config(text=f"Directorio actual: {screenshot_dir}")
        messagebox.showinfo("Éxito", f"Directorio cambiado a:\n{screenshot_dir}")

def is_valid_hotkey(hotkey_str):
    """Valida si una combinación de teclas es válida"""
    try:
        # Intenta agregar y remover el hotkey temporalmente
        keyboard.add_hotkey(hotkey_str, lambda: None)
        keyboard.remove_hotkey(hotkey_str)
        return True
    except ValueError:
        return False

def detect_key_press():
    """Función principal para detectar combinación de teclas"""
    try:
        # Crear ventana emergente
        popup = Toplevel(root)
        popup.title("Detectando combinación")
        popup.geometry("300x100")
        Label(popup, text="Presione la combinación de teclas...\n(Para cancelar presione ESC)").pack(pady=10)
        
        # Variable para compartir entre hilos
        detected_hotkey = [None]
        
        def on_detect():
            """Hilo para detectar teclas sin bloquear la GUI"""
            try:
                # Leer combinación
                combo = keyboard.read_hotkey(suppress=False)
                detected_hotkey[0] = combo
                # Cerrar ventana desde el hilo principal
                root.after(0, lambda: popup.destroy())
            except Exception as e:
                messagebox.showerror("Error", f"Error en detección: {str(e)}")
            finally:
                # Actualizar interfaz
                root.after(0, update_hotkey_entry)
        
        def update_hotkey_entry():
            """Actualiza el campo de entrada con la combinación detectada"""
            if detected_hotkey[0]:
                normalized = detected_hotkey[0].lower().replace(" ", "").replace("control", "ctrl")
                hotkey_entry.delete(0, END)
                hotkey_entry.insert(0, normalized)
        
        def cancel_detection():
            """Cancelar la detección"""
            detected_hotkey[0] = None
            popup.destroy()
        
        # Botón de cancelar
        Button(popup, text="Cancelar", command=cancel_detection).pack(pady=5)
        
        # Iniciar detección en hilo separado
        detection_thread = threading.Thread(target=on_detect, daemon=True)
        detection_thread.start()
        
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo iniciar la detección: {str(e)}")

def change_hotkey():
    """Función modificada con validación mejorada"""
    global hotkey
    try:
        new_hotkey = hotkey_entry.get().strip().lower()
        
        # Normalizar entrada
        new_hotkey = (
            new_hotkey.replace(" ", "")
            .replace("control", "ctrl")
            .replace("++", "+")
            .replace("altgr", "ctrl+alt")
        )
        
        if not new_hotkey:
            messagebox.showwarning("Advertencia", "La combinación no puede estar vacía")
            return
        
        # Validación técnica
        try:
            keyboard.add_hotkey(new_hotkey, lambda: None, suppress=True)
            keyboard.remove_hotkey(new_hotkey)
        except ValueError as e:
            messagebox.showerror(
                "Combinación inválida",
                f"Error: {str(e)}\n\nEjemplos válidos:\n"
                "• ctrl+shift+a\n"
                "• alt+tab\n"
                "• ctrl+alt+7",
            )
            return
        
        # Actualizar hotkey global
        keyboard.unhook_all()
        keyboard.add_hotkey(new_hotkey, delayed_capture)
        hotkey = new_hotkey
        messagebox.showinfo("Éxito", f"Combinación actualizada: {hotkey}")
        
    except Exception as e:
        messagebox.showerror("Error crítico", f"Error inesperado: {str(e)}")
        raise  # Opcional: quitar en producción

def delayed_capture():
    time.sleep(0.1)
    if current_mode == "elemento":
        capture_element_mode()
    elif current_mode == "ventana":
        capture_window_mode()
    else:
        capture_completo_mode()

# Configuración de la GUI
root = Tk()
root.title("WebShot v5.0")
is_topmost = False  # Variable global para alternar superposición




# Botón de información mejorado
info_btn = Button(root, 
                 text="?", 
                 command=show_info,
                 font=("Arial", 9),
                 bg="#E0F7FA",
                 relief="flat",
                 borderwidth=2)
info_btn.grid(row=0, column=0, padx=5, pady=5, sticky="w")

# URL
Label(root, text="URL:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
url_entry = Entry(root, width=50)
url_entry.grid(row=0, column=1, padx=5, pady=5)
Button(root, text="Ir", command=navigate_to_url).grid(row=0, column=2, padx=5, pady=5)

# Botón de superposición
topmost_button = Button(root, text="🔒", command=toggle_topmost, font=("Arial", 12), bg="#E0F7FA", relief="flat", borderwidth=2)
topmost_button.grid(row=1, column=0, padx=5, pady=5, sticky="w")

# Selector de modo
mode_var = StringVar(root)
mode_var.set("completo")
mode_var.trace("w", change_capture_mode)
mode_menu = OptionMenu(root, mode_var, "completo", "ventana", "elemento")
mode_menu.grid(row=1, column=0, columnspan=3, pady=5)

# Frame modo completo
normal_frame = Frame(root)
Label(normal_frame, text="Nombre captura:").grid(row=0, column=0, padx=5)
normal_name_entry = Entry(normal_frame, width=25)
normal_name_entry.grid(row=0, column=1, padx=5)
Label(normal_frame, text="Contador:").grid(row=0, column=2, padx=5)
normal_counter_entry = Entry(normal_frame, width=10)
normal_counter_entry.grid(row=0, column=3, padx=5)
mode_settings["completo"]['name_entry'] = normal_name_entry
mode_settings["completo"]['counter_entry'] = normal_counter_entry

# Frame modo ventana
window_frame = Frame(root)
Label(window_frame, text="Nombre ventana:").grid(row=0, column=0, padx=5)
window_name_entry = Entry(window_frame, width=25)
window_name_entry.grid(row=0, column=1, padx=5)
Label(window_frame, text="Contador:").grid(row=0, column=2, padx=5)
window_counter_entry = Entry(window_frame, width=10)
window_counter_entry.grid(row=0, column=3, padx=5)
mode_settings["ventana"]['name_entry'] = window_name_entry
mode_settings["ventana"]['counter_entry'] = window_counter_entry

# Frame modo elemento
element_frame = Frame(root)
Label(element_frame, text="Nombre carpeta:").grid(row=0, column=0, padx=5)
element_folder_entry = Entry(element_frame, width=20)
element_folder_entry.grid(row=0, column=1, padx=5)
Label(element_frame, text="Prefijo archivos:").grid(row=0, column=2, padx=5)
element_file_entry = Entry(element_frame, width=20)
element_file_entry.grid(row=0, column=3, padx=5)
Label(element_frame, text="Contador:").grid(row=0, column=4, padx=5)
element_counter_entry = Entry(element_frame, width=10)
element_counter_entry.grid(row=0, column=5, padx=5)
mode_settings["elemento"]['folder_entry'] = element_folder_entry
mode_settings["elemento"]['file_entry'] = element_file_entry
mode_settings["elemento"]['counter_entry'] = element_counter_entry

# Frame para XPATHs
xpath_frame = Frame(root)
Label(xpath_frame, text="XPATH Relativo:").grid(row=0, column=0, padx=5)
xpath_entry = Entry(xpath_frame, width=30)
xpath_entry.grid(row=0, column=1, padx=5)
Label(xpath_frame, text="XPATH Absoluto:").grid(row=1, column=0, padx=5)
abs_xpath_entry = Entry(xpath_frame, width=30)
abs_xpath_entry.grid(row=1, column=1, padx=5)

# Sección directorio
dir_frame = Frame(root)
dir_frame.grid(row=8, column=0, columnspan=3, pady=10)
dir_label = Label(dir_frame, text=f"Directorio actual: {screenshot_dir}", wraplength=400)
dir_label.pack(side='left', padx=5)
Button(dir_frame, text="Cambiar Directorio", command=change_screenshot_dir).pack(side='right', padx=5)

# Sección hotkey
hotkey_frame = Frame(root)
hotkey_frame.grid(row=7, column=0, columnspan=3, pady=10)
Label(hotkey_frame, text="Combinación de teclas:").pack(side='left', padx=5)
hotkey_entry = Entry(hotkey_frame, width=25)
hotkey_entry.insert(0, hotkey)
hotkey_entry.pack(side='left', padx=5)
Button(hotkey_frame, text="Detectar", command=detect_key_press, bg="#e0e0e0").pack(side='left', padx=5)
Button(hotkey_frame, text="Cambiar", command=change_hotkey, bg="#99ff99").pack(side='left', padx=5)

# Botón Deshacer
undo_btn = Button(root, text="Deshacer Última Acción", command=undo_last_action, bg="#ff9999")
undo_btn.grid(row=3, column=0, columnspan=3, pady=5)  # Ajustado para ocupar todo el ancho

# Inicializar valores
normal_name_entry.insert(0, mode_settings["completo"]["base_name"])
normal_counter_entry.insert(0, "1")
window_name_entry.insert(0, mode_settings["ventana"]["base_name"])
window_counter_entry.insert(0, "1")
element_folder_entry.insert(0, mode_settings["elemento"]["folder_name"])
element_file_entry.insert(0, mode_settings["elemento"]["file_prefix"])
element_counter_entry.insert(0, "1")

# Iniciar driver
driver = setup_driver()
keyboard.add_hotkey(hotkey, delayed_capture)

# Botón de captura manual
capture_btn = Button(root, text="Realizar Captura", command=delayed_capture, bg="#99ff99")
capture_btn.grid(row=2, column=0, columnspan=5, pady=5)  # Movido a la fila 3

# Solicitar directorio inicial
screenshot_dir = askdirectory(title="Seleccionar carpeta para guardar capturas")
if not screenshot_dir:
    messagebox.showerror("Error", "Debes seleccionar un directorio")
    exit()

# Mostrar pantalla de carga
show_loading_screen(root)

dir_label.config(text=f"Directorio actual: {screenshot_dir}")

root.mainloop()

# Limpieza final
driver.quit()
keyboard.unhook_all()
