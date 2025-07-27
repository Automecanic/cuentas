import argparse # Importa el módulo argparse para manejar argumentos de línea de comandos.
import os       # Importa el módulo os para interactuar con el sistema operativo.
import logging  # Importa el módulo logging para registrar mensajes.
import subprocess # Importa el módulo subprocess para ejecutar comandos externos (como Git).
from datetime import datetime # Importa datetime para obtener la fecha actual para el commit.

# Configura el sistema de registro básico para el script.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Ruta de salida fija para el archivo JavaScript.
# Esta variable ya no se espera como argumento de línea de comandos.
FIXED_OUTPUT_JS_PATH = "../docs_bot_tading_spot/data.js"

def convert_csv_to_js_string(input_csv_path, run_git_commands=True):
    """
    Lee un archivo CSV y lo formatea como una cadena JavaScript exportable
    para ser usada en un archivo HTML/JS, manteniendo el contenido exacto del CSV.
    El archivo de salida se guarda en una ruta fija predefinida.
    Opcionalmente, puede ejecutar comandos Git después de generar el archivo.

    La salida tendrá el formato:
    export const csvData = `
    <contenido_exacto_del_csv_aqui>
    `;

    Args:
        input_csv_path (str): La ruta al archivo CSV de entrada.
        run_git_commands (bool): Si es True, el script intentará ejecutar comandos Git.
    """
    # Usamos la ruta de salida fija definida globalmente.
    output_js_path = FIXED_OUTPUT_JS_PATH

    if not os.path.exists(input_csv_path):
        # Verifica si el archivo CSV de entrada existe.
        logging.error(f"❌ Error: El archivo CSV de entrada no se encontró en '{input_csv_path}'")
        return

    try:
        # Lee el contenido completo del archivo CSV tal cual.
        with open(input_csv_path, 'r', encoding='utf-8') as f:
            csv_content = f.read().strip() # .strip() para eliminar cualquier espacio en blanco al inicio/final

        if not csv_content:
            logging.warning("⚠️ El archivo CSV de entrada está vacío. No se generará salida.")
            return

        # Formatea el contenido CSV en la cadena JavaScript deseada con 'export'.
        js_string_output = f"export const csvData = `\n{csv_content}\n`;"

        # Asegura que el directorio de salida exista
        output_dir = os.path.dirname(output_js_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logging.info(f"✅ Directorio de salida creado: '{output_dir}'")

        # Escribe la cadena formateada en el archivo JavaScript de salida.
        with open(output_js_path, 'w', encoding='utf-8') as f:
            f.write(js_string_output)
        
        logging.info(f"✅ Archivo '{output_js_path}' generado exitosamente desde '{input_csv_path}'.")
        logging.info("Contenido del archivo de salida (primeras 500 caracteres para vista previa):")
        logging.info(js_string_output[:500] + "..." if len(js_string_output) > 500 else js_string_output)

        # --- Ejecución de comandos Git (Opcional) ---
        if run_git_commands:
            logging.info("🚀 Intentando ejecutar comandos Git...")
            
            # Obtener la fecha actual para el mensaje de commit.
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_message = f"Actualización de datos CSV: {current_date}"

            # 1. git add .
            try:
                # Ejecuta 'git add .' para añadir todos los cambios en el directorio actual.
                # capture_output=True para capturar stdout y stderr.
                # text=True para que la salida sea una cadena de texto.
                result = subprocess.run(["git", "add", "."], capture_output=True, text=True, check=True)
                logging.info(f"✅ 'git add .' ejecutado con éxito. Salida: {result.stdout.strip()}")
            except subprocess.CalledProcessError as e:
                logging.error(f"❌ Error al ejecutar 'git add .': {e}. Stderr: {e.stderr.strip()}")
            except FileNotFoundError:
                logging.error("❌ Error: 'git' no se encontró. Asegúrate de que Git esté instalado y en tu PATH.")
            except Exception as e:
                logging.error(f"❌ Error inesperado al ejecutar 'git add .': {e}")

            # 2. git commit -m "fecha <valor fecha>"
            try:
                # Ejecuta 'git commit' con el mensaje dinámico.
                result = subprocess.run(["git", "commit", "-m", commit_message], capture_output=True, text=True, check=True)
                logging.info(f"✅ 'git commit' ejecutado con éxito. Salida: {result.stdout.strip()}")
            except subprocess.CalledProcessError as e:
                # Si no hay cambios para confirmar, git commit lanzará un error.
                if "nothing to commit" in e.stderr.lower():
                    logging.warning("⚠️ No hay cambios para confirmar. 'git commit' no fue necesario.")
                else:
                    logging.error(f"❌ Error al ejecutar 'git commit': {e}. Stderr: {e.stderr.strip()}")
            except FileNotFoundError:
                logging.error("❌ Error: 'git' no se encontró. Asegúrate de que Git esté instalado y en tu PATH.")
            except Exception as e:
                logging.error(f"❌ Error inesperado al ejecutar 'git commit': {e}")

            # 3. git push
            try:
                # Ejecuta 'git push'. Esto requerirá autenticación si no está configurada.
                result = subprocess.run(["git", "push"], capture_output=True, text=True, check=True)
                logging.info(f"✅ 'git push' ejecutado con éxito. Salida: {result.stdout.strip()}")
            except subprocess.CalledProcessError as e:
                logging.error(f"❌ Error al ejecutar 'git push': {e}. Stderr: {e.stderr.strip()}")
                logging.error("💡 Sugerencia: El 'git push' puede fallar por problemas de autenticación o si no hay cambios remotos. Asegúrate de que Git esté configurado para autenticación no interactiva.")
            except FileNotFoundError:
                logging.error("❌ Error: 'git' no se encontró. Asegúrate de que Git esté instalado y en tu PATH.")
            except Exception as e:
                logging.error(f"❌ Error inesperado al ejecutar 'git push': {e}")
        # --- Fin de la ejecución de comandos Git ---
        
        logging.info("🎉 todo ha ido ok") # Mensaje de éxito final.

    except Exception as e:
        # Captura cualquier excepción que ocurra durante el proceso principal.
        logging.error(f"❌ Ocurrió un error general durante la conversión o la ejecución de Git: {e}", exc_info=True)

if __name__ == "__main__":
    # Configura el analizador de argumentos de línea de comandos.
    parser = argparse.ArgumentParser(
        description="Convierte un archivo CSV a una cadena de texto formateada para JavaScript, manteniendo el contenido original. Opcionalmente, ejecuta comandos Git."
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
    # La ruta de salida ahora es fija y no se pasa como argumento.
    convert_csv_to_js_string(args.input_csv, args.git)
