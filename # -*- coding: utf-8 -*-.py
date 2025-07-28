# -*- coding: utf-8 -*-
import argparse # Importa el módulo argparse para manejar argumentos de línea de comandos.
import os       # Importa el módulo os para interactuar con el sistema operativo.
import logging  # Importa el módulo logging para registrar mensajes.
import subprocess # Importa el módulo subprocess para ejecutar comandos externos (como Git).
from datetime import datetime # Importa datetime para obtener la fecha actual para el commit y para parsear timestamps.

# Configura el sistema de registro básico para el script.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Ruta de salida fija para el archivo JavaScript principal (transacciones).
FIXED_OUTPUT_JS_PATH = "data.js"
# Nueva ruta de salida fija para el archivo JavaScript de beneficios diarios.
FIXED_OUTPUT_JS_PATH_2 = "data2.js"

def calculate_daily_profits_from_csv(csv_content):
    """
    Calcula los beneficios/pérdidas diarios a partir del contenido CSV de transacciones.

    Args:
        csv_content (str): El contenido completo del CSV de transacciones.

    Returns:
        str: Una cadena CSV con el formato "fecha,beneficio" para cada día con transacciones de venta.
             Retorna una cadena con solo el encabezado si no hay transacciones o hay un error.
    """
    daily_profits = {} # Diccionario para almacenar los beneficios por día.
    lines = csv_content.strip().split('\n') # Divide el contenido CSV en líneas.

    if not lines or len(lines) < 2: # Si no hay líneas o solo hay encabezado.
        logging.warning("⚠️ Contenido CSV de transacciones vacío o solo con encabezado. No se pueden calcular beneficios diarios.")
        return "fecha,beneficio\n" # Retorna un CSV vacío con encabezado.

    headers = [h.strip() for h in lines[0].split(',')] # Extrae y limpia los encabezados.
    
    # Encontrar los índices de las columnas necesarias.
    try:
        timestamp_idx = headers.index('timestamp')
        tipo_idx = headers.index('tipo')
        ganancia_usdt_idx = headers.index('ganancia_usdt')
    except ValueError as e:
        logging.error(f"❌ Error: Columnas necesarias (timestamp, tipo, ganancia_usdt) no encontradas en el CSV. Error: {e}")
        return "fecha,beneficio\n" # Retorna un CSV vacío con encabezado.

    for i in range(1, len(lines)): # Itera sobre las líneas de datos (saltando el encabezado).
        current_line = [c.strip() for c in lines[i].split(',')] # Divide y limpia la línea actual.
        
        if len(current_line) != len(headers): # Salta líneas mal formadas.
            logging.warning(f"⚠️ Línea CSV mal formada, saltando: {lines[i]}")
            continue

        # Si es una transacción de VENTA y tiene el campo 'ganancia_usdt'.
        if current_line[tipo_idx] == 'VENTA' and current_line[ganancia_usdt_idx]:
            try:
                # Extraer la fecha (YYYY-MM-DD) del timestamp ISO.
                transaction_date = datetime.fromisoformat(current_line[timestamp_idx]).strftime("%Y-%m-%d")
                profit = float(current_line[ganancia_usdt_idx]) # Convierte la ganancia a flotante.
                
                if transaction_date not in daily_profits: # Si la fecha no está en el diccionario.
                    daily_profits[transaction_date] = 0.0 # Inicializa el beneficio para esa fecha.
                daily_profits[transaction_date] += profit # Suma el beneficio a la fecha correspondiente.
            except (ValueError, KeyError) as e: # Captura errores de valor o clave.
                logging.warning(f"⚠️ Transacción con formato inválido o datos faltantes para cálculo de beneficio diario: {lines[i]}. Error: {e}")
                continue # Continúa con la siguiente transacción.

    # Ordenar las fechas para la salida CSV.
    sorted_dates = sorted(daily_profits.keys()) # Ordena las fechas cronológicamente.

    # Formatear a cadena CSV.
    csv_string_lines = ["fecha,beneficio"] # Encabezado CSV.
    for date in sorted_dates: # Itera sobre las fechas ordenadas.
        csv_string_lines.append(f"{date},{daily_profits[date]:.10f}") # Añade la fecha y el beneficio formateado a la lista.

    return "\n".join(csv_string_lines) # Une las líneas para formar la cadena CSV completa.

def generate_js_data_files(input_csv_path, run_git_commands=True):
    """
    Genera dos archivos JavaScript:
    - data.js: Contiene el contenido exacto del CSV de transacciones.
    - data2.js: Contiene los beneficios diarios en formato CSV, calculados desde el CSV de transacciones.
    Opcionalmente, puede ejecutar comandos Git después de generar los archivos.

    Args:
        input_csv_path (str): La ruta al archivo CSV de entrada (transacciones).
        run_git_commands (bool): Si es True, el script intentará ejecutar comandos Git.
    """
    # --- 1. Generar csvData desde el archivo CSV de entrada (para data.js) ---
    csv_content = "" # Inicializa el contenido CSV.
    if not os.path.exists(input_csv_path): # Verifica si el archivo CSV de entrada existe.
        logging.error(f"❌ Error: El archivo CSV de entrada no se encontró en '{input_csv_path}'") # Registra un error.
        # Continúa para intentar generar dailyProfitData incluso si esto falla.
    else: # Si el archivo CSV existe.
        try: # Intenta leer el archivo.
            with open(input_csv_path, 'r', encoding='utf-8') as f: # Abre el archivo en modo lectura.
                csv_content = f.read().strip() # Lee el contenido y elimina espacios en blanco.
            if not csv_content: # Si el contenido está vacío.
                logging.warning("⚠️ El archivo CSV de entrada está vacío. 'csvData' estará vacío.") # Advierte que csvData estará vacío.
        except Exception as e: # Captura cualquier error durante la lectura.
            logging.error(f"❌ Error al leer el archivo CSV de entrada '{input_csv_path}': {e}", exc_info=True) # Registra el error.

    js_csv_data_string = f"export const csvData = `\n{csv_content}\n`;" # Formatea el contenido CSV para JavaScript.

    # --- 2. Generar dailyProfitData calculando desde el csv_content (para data2.js) ---
    daily_profit_csv_content = calculate_daily_profits_from_csv(csv_content) # Obtiene los beneficios diarios como cadena CSV.
    if not daily_profit_csv_content or daily_profit_csv_content == "fecha,beneficio\n": # Si no se pudieron obtener datos de beneficios diarios o solo tiene el encabezado.
        logging.warning("⚠️ No se pudieron calcular datos de beneficios diarios desde el CSV de entrada o están vacíos. 'dailyProfitData' estará vacío.") # Advierte que dailyProfitData estará vacío.
        daily_profit_csv_content = "fecha,beneficio\n" # Asegura que al menos el encabezado esté presente.

    js_daily_profit_data_string = f"export const csvData = `\n{daily_profit_csv_content}\n`;" # Formatea los beneficios diarios para JavaScript.

    # --- Escribir data.js ---
    output_dir_data = os.path.dirname(FIXED_OUTPUT_JS_PATH) # Obtiene el directorio de salida para data.js.
    if output_dir_data and not os.path.exists(output_dir_data): # Si el directorio no existe.
        os.makedirs(output_dir_data) # Crea el directorio.
        logging.info(f"✅ Directorio de salida creado: '{output_dir_data}'") # Registra la creación del directorio.

    try: # Intenta escribir data.js.
        with open(FIXED_OUTPUT_JS_PATH, 'w', encoding='utf-8') as f: # Abre el archivo en modo escritura.
            f.write(js_csv_data_string) # Escribe el contenido de csvData.
        logging.info(f"✅ Archivo '{FIXED_OUTPUT_JS_PATH}' generado exitosamente con 'csvData'.") # Registra el éxito.
    except Exception as e: # Captura cualquier error.
        logging.error(f"❌ Error al escribir el archivo '{FIXED_OUTPUT_JS_PATH}': {e}", exc_info=True) # Registra el error.

    # --- Escribir data2.js ---
    output_dir_data2 = os.path.dirname(FIXED_OUTPUT_JS_PATH_2) # Obtiene el directorio de salida para data2.js.
    if output_dir_data2 and not os.path.exists(output_dir_data2): # Si el directorio no existe.
        os.makedirs(output_dir_data2) # Crea el directorio.
        logging.info(f"✅ Directorio de salida creado: '{output_dir_data2}'") # Registra la creación del directorio.

    try: # Intenta escribir data2.js.
        with open(FIXED_OUTPUT_JS_PATH_2, 'w', encoding='utf-8') as f: # Abre el archivo en modo escritura.
            f.write(js_daily_profit_data_string) # Escribe el contenido de dailyProfitData.
        logging.info(f"✅ Archivo '{FIXED_OUTPUT_JS_PATH_2}' generado exitosamente con 'dailyProfitData'.") # Registra el éxito.
    except Exception as e: # Captura cualquier error.
        logging.error(f"❌ Error al escribir el archivo '{FIXED_OUTPUT_JS_PATH_2}': {e}", exc_info=True) # Registra el error.

    # --- Ejecución de comandos Git (Opcional) ---
    if run_git_commands: # Si se deben ejecutar comandos Git.
        logging.info("🚀 Intentando ejecutar comandos Git...") # Mensaje de intento de ejecución de Git.
        
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Obtiene la fecha y hora actual.
        commit_message = f"Actualización de datos de análisis (data.js y data2.js): {current_date}" # Mensaje de commit.

        try_git_command(["git", "add", FIXED_OUTPUT_JS_PATH], f"'git add {FIXED_OUTPUT_JS_PATH}'") # Añade data.js.
        try_git_command(["git", "add", FIXED_OUTPUT_JS_PATH_2], f"'git add {FIXED_OUTPUT_JS_PATH_2}'") # Añade data2.js.
        try_git_command(["git", "commit", "-m", commit_message], "'git commit'") # Intenta ejecutar 'git commit'.
        try_git_command(["git", "push"], "'git push'") # Intenta ejecutar 'git push'.
    
    logging.info("🎉 todo ha ido ok") # Mensaje de éxito final.

def try_git_command(command, command_name):
    """Función auxiliar para ejecutar comandos Git y registrar los resultados."""
    try: # Intenta ejecutar el comando.
        result = subprocess.run(command, capture_output=True, text=True, check=True) # Ejecuta el comando y captura la salida.
        logging.info(f"✅ {command_name} ejecutado con éxito. Salida: {result.stdout.strip()}") # Registra el éxito.
    except subprocess.CalledProcessError as e: # Captura errores de comandos Git.
        if "nothing to commit" in e.stderr.lower() and "commit" in command_name: # Si no hay cambios para confirmar en un commit.
            logging.warning(f"⚠️ No hay cambios para confirmar. {command_name} no fue necesario.") # Advierte que no fue necesario.
        else: # Otros errores de Git.
            logging.error(f"❌ Error al ejecutar {command_name}: {e}. Stderr: {e.stderr.strip()}") # Registra el error.
            if "push" in command_name: # Si el error es en 'git push'.
                logging.error("💡 Sugerencia: El 'git push' puede fallar por problemas de autenticación o si no hay cambios remotos. Asegúrate de que Git esté configurado para autenticación no interactiva.") # Sugiere posibles soluciones.
    except FileNotFoundError: # Si el comando 'git' no se encuentra.
        logging.error(f"❌ Error: 'git' no se encontró. Asegúrate de que Git esté instalado y en tu PATH.") # Registra el error de Git no encontrado.
    except Exception as e: # Captura cualquier otro error inesperado.
        logging.error(f"❌ Error inesperado al ejecutar {command_name}: {e}") # Registra el error inesperado.

if __name__ == "__main__": # Bloque de ejecución principal cuando el script se ejecuta directamente.
    # Configura el analizador de argumentos de línea de comandos.
    parser = argparse.ArgumentParser(
        description="Genera un archivo JavaScript con datos CSV y de beneficios diarios, y opcionalmente ejecuta comandos Git."
    )
    # Define el argumento para la ruta del archivo CSV de entrada.
    parser.add_argument(
        "input_csv",
        type=str,
        help="La ruta al archivo CSV de entrada."
    )
    # Define el argumento opcional para ejecutar comandos Git.
    parser.add_argument(
        "--git",
        action="store_true", # Si se usa este flag, se establece a True.
        help="Si se especifica, el script intentará ejecutar 'git add .', 'git commit', y 'git push' después de generar el archivo JS."
    )

    # Parsea los argumentos proporcionados por el usuario.
    args = parser.parse_args()

    # Llama a la función principal con la ruta del archivo de entrada y el flag de Git.
    generate_js_data_files(args.input_csv, args.git)
